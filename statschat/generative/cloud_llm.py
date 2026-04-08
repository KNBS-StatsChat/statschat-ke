import logging
import os
import re
from collections import defaultdict
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.output_parsers import PydanticOutputParser
from openai import NotFoundError, RateLimitError
from sentence_transformers import CrossEncoder
from statschat.generative.response_model import LlmResponse
from statschat.generative.prompts_cloud import (
    EXTRACTIVE_PROMPT_PYDANTIC,
    STUFF_DOCUMENT_PROMPT,
)
from statschat.generative.utils import highlighter

YEAR_PATTERN = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")

# Range years: "2023-24", "2023/24", "2023-2024", "2023/2024", "FY2023/24"
# Use digit-only lookbehind/lookahead so glued prefixes like "FY" still match.
RANGE_YEAR_PATTERN = re.compile(r"(?<!\d)(19|20)(\d{2})[\-/](\d{2}|\d{4})(?!\d)")

MONTH_NAME_TO_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
MONTH_NAME_PATTERN = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b",
    re.IGNORECASE,
)

# Quarter detection: "Q3", "Q 3", "third quarter", "quarter three", "3rd quarter"
QUARTER_DIGIT_PATTERN = re.compile(r"\bq\s*([1-4])\b", re.IGNORECASE)
QUARTER_ORDINAL_PATTERN = re.compile(
    r"\b(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter\b", re.IGNORECASE
)
QUARTER_NUMBER_PATTERN = re.compile(
    r"\bquarter\s+(?:([1-4])|(one|two|three|four|first|second|third|fourth))\b",
    re.IGNORECASE,
)
ORDINAL_TO_QUARTER = {
    "first": 1,
    "1st": 1,
    "one": 1,
    "second": 2,
    "2nd": 2,
    "two": 2,
    "third": 3,
    "3rd": 3,
    "three": 3,
    "fourth": 4,
    "4th": 4,
    "four": 4,
}


def _extract_years(text: str) -> set[int]:
    """Extract four-digit years from free text, expanding range years.

    Ranges like ``2023-24`` and ``2023/2024`` count as both endpoints, so titles
    such as ``2023-24 Kenya Housing Survey`` match queries that mention either
    2023 or 2024.
    """
    text = str(text or "")
    years: set[int] = set()
    consumed: list[tuple[int, int]] = []

    for match in RANGE_YEAR_PATTERN.finditer(text):
        century = match.group(1)
        start_yy = match.group(2)
        end_token = match.group(3)
        start_year = int(century + start_yy)
        if len(end_token) == 2:
            end_year = int(century + end_token)
            if end_year < start_year:
                # Handle century rollover, e.g. 1999-00 → 2000
                end_year += 100
        else:
            end_year = int(end_token)
        # Only treat as a true range if endpoints are sane and adjacent-ish
        if 0 <= end_year - start_year <= 10:
            years.add(start_year)
            years.add(end_year)
            consumed.append(match.span())

    for match in YEAR_PATTERN.finditer(text):
        start, _ = match.span()
        if any(cs <= start < ce for cs, ce in consumed):
            continue
        years.add(int(match.group(0)))

    return years


def _extract_months(text: str) -> set[int]:
    """Extract month numbers (1–12) from free text."""
    return {
        MONTH_NAME_TO_NUM[match.group(0).lower()]
        for match in MONTH_NAME_PATTERN.finditer(str(text or ""))
    }


def _extract_quarters(text: str) -> set[int]:
    """Extract quarter numbers (1–4) from free text."""
    text = str(text or "")
    quarters: set[int] = set()
    for match in QUARTER_DIGIT_PATTERN.finditer(text):
        quarters.add(int(match.group(1)))
    for match in QUARTER_ORDINAL_PATTERN.finditer(text):
        quarters.add(ORDINAL_TO_QUARTER[match.group(1).lower()])
    for match in QUARTER_NUMBER_PATTERN.finditer(text):
        if match.group(1):
            quarters.add(int(match.group(1)))
        else:
            quarters.add(ORDINAL_TO_QUARTER[match.group(2).lower()])
    return quarters


def parse_temporal_tokens(text: str) -> dict:
    """Parse all temporal constraints from query or document text."""
    return {
        "years": _extract_years(text),
        "months": _extract_months(text),
        "quarters": _extract_quarters(text),
    }


def has_temporal_constraint(text: str) -> bool:
    """True if the text carries any year, month, or quarter token."""
    tokens = parse_temporal_tokens(text)
    return bool(tokens["years"] or tokens["months"] or tokens["quarters"])


def _doc_temporal_tokens(doc: dict) -> dict:
    """Extract temporal tokens from a doc's title, date, and URL metadata."""
    parts = [
        str(doc.get("title", "")),
        str(doc.get("date", "")),
        str(doc.get("url", "")),
        str(doc.get("page_url", "")),
    ]
    return parse_temporal_tokens(" ".join(parts))


def _doc_matches_query_temporal(query_tokens: dict, doc_tokens: dict) -> bool:
    """Return True if a doc satisfies every non-empty temporal dimension of the query.

    A query dimension only constrains the match if the query actually mentioned
    it. A doc need not have a month if the query is year-only, etc.
    """
    if query_tokens["years"] and not (query_tokens["years"] & doc_tokens["years"]):
        return False
    if query_tokens["quarters"] and not (
        query_tokens["quarters"] & doc_tokens["quarters"]
    ):
        return False
    if query_tokens["months"] and not (query_tokens["months"] & doc_tokens["months"]):
        return False
    return True


def _extract_doc_year(doc: dict) -> int | None:
    """Best-effort publication year extraction from metadata."""
    date_text = str(doc.get("date", "")).strip()
    title_text = str(doc.get("title", "")).strip()
    years = _extract_years(f"{date_text} {title_text}")
    if not years:
        return None
    return max(years)


def _doc_group_key(doc: dict) -> str:
    """Stable grouping key for mild document diversification."""
    page_url = str(doc.get("page_url", "")).strip()
    if page_url:
        return page_url.split("#", 1)[0].lower()
    title = str(doc.get("title", "")).strip().lower()
    date = str(doc.get("date", "")).strip().lower()
    return f"{title}::{date}"


def _build_reranker_passage(doc: dict) -> str:
    """Build a structured passage for the cross-encoder reranker."""
    title = str(doc.get("title", "")).strip()
    date = str(doc.get("date", "")).strip()
    page_number = str(doc.get("page_number", "")).strip()
    page_content = str(doc.get("page_content", "")).strip()

    parts = []
    if title:
        parts.append(f"Title: {title}")
    if date:
        parts.append(f"Date: {date}")
    if page_number:
        parts.append(f"Page: {page_number}")
    if page_content:
        parts.append(page_content)

    return "\n".join(parts)


def _apply_recency_bias(
    results: list[dict], query: str, recency_bias_weight: float
) -> list[dict]:
    """
    Add a mild recency preference for ambiguous yearless questions.

    If the query already contains an explicit year, no bias is applied.
    """
    if not results:
        return results

    if recency_bias_weight <= 0 or _extract_years(query):
        for result in results:
            result["selection_score"] = float(result.get("reranker_score", 0.0))
        return results

    year_values = [year for year in (_extract_doc_year(doc) for doc in results) if year]
    if not year_values:
        for result in results:
            result["selection_score"] = float(result.get("reranker_score", 0.0))
        return results

    min_year = min(year_values)
    max_year = max(year_values)
    year_span = max_year - min_year

    for result in results:
        base_score = float(result.get("reranker_score", 0.0))
        doc_year = _extract_doc_year(result)
        if doc_year is None or year_span == 0:
            result["selection_score"] = base_score
            continue
        normalized_recency = (doc_year - min_year) / year_span
        result["selection_score"] = base_score + (
            normalized_recency * recency_bias_weight
        )
    return results


def select_generation_contexts(
    results: list[dict],
    k_contexts: int,
    *,
    max_chunks_per_doc: int = 3,
    per_doc_penalty: float = 0.2,
) -> list[dict]:
    """
    Select generation contexts with mild document diversity.

    This keeps strong evidence pages from the same report available to the LLM
    while preventing a single document from flooding every context slot.
    """
    if k_contexts <= 0 or not results:
        return []

    remaining = list(results)
    selected: list[dict] = []
    counts_by_doc: defaultdict[str, int] = defaultdict(int)

    while remaining and len(selected) < k_contexts:
        best_index: int | None = None
        best_score = float("-inf")

        for idx, doc in enumerate(remaining):
            doc_key = _doc_group_key(doc)
            if counts_by_doc[doc_key] >= max_chunks_per_doc:
                continue

            base_score = float(
                doc.get(
                    "selection_score",
                    doc.get("reranker_score", -float(doc.get("score", 0.0))),
                )
            )
            adjusted_score = base_score - (per_doc_penalty * counts_by_doc[doc_key])
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_index = idx

        if best_index is None:
            break

        chosen = remaining.pop(best_index)
        counts_by_doc[_doc_group_key(chosen)] += 1
        selected.append(chosen)

    if not selected:
        return results[:k_contexts]
    return selected


@lru_cache(maxsize=1)
def _get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> CrossEncoder:
    """Load the cross-encoder reranker once per process."""
    return CrossEncoder(model_name)


class Inquirer:
    """
    Wraps the logic for using an LLM to synthesise a written answer from
    the text of a set of searched/retrieved documents.
    """

    def __init__(
        self,
        generative_model_name: str = "mistralai/mistral-small-3.1-24b-instruct:free",
        faiss_db_root: str = "data/db_langchain",
        faiss_db_root_latest: str = "data/db_langchain",  # change to "data/db_langchain_latest" after "UPDATE"
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        k_docs: int = 10,
        k_contexts: int = 3,
        similarity_threshold: float = 2.0,  # higher threshold for smaller corpus
        logger: logging.Logger = None,
        llm_temperature: float = 0.0,
        llm_max_tokens: int = 1024,
        verbose: bool = False,
        answer_threshold: float = 0.5,
        document_threshold: float = 0.9,
        provider="openrouter",  # default
        reranker_model_name: str | None = None,
        reranker_candidate_k: int | None = None,
        temporal_candidate_k: int | None = None,
        recency_bias_weight: float = 0.5,
        max_chunks_per_doc: int = 3,
        per_doc_penalty: float = 0.2,
        **_unused_search_config,
    ):
        """
        Args:
            generative_model_name (str, optional): HuggingFace model id.
                Defaults to "mistralai/Mistral-7B-Instruct-v0.3".
            embedding_model_name (str, optional): HuggingFace embedding model id.
                Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        """

        # Initialise logger
        if logger is None:
            self.logger = logging.getLogger(__name__)

        else:
            self.logger = logger

        self.k_docs = k_docs
        self.k_contexts = k_contexts
        self.similarity_threshold = similarity_threshold
        self.answer_threshold = answer_threshold
        self.document_threshold = document_threshold
        self.verbose = verbose
        self.extractive_prompt = EXTRACTIVE_PROMPT_PYDANTIC
        self.stuff_document_prompt = STUFF_DOCUMENT_PROMPT
        self.llm_temperature = llm_temperature
        self.llm_max_tokens = llm_max_tokens
        self.provider = provider
        # Keep the cloud path compatible with the shared search config used by
        # the local path, and align ranking behaviour where practical.
        self.reranker_model_name = reranker_model_name
        self.reranker_candidate_k = max(
            int(reranker_candidate_k or max(k_docs * 6, 24)),
            int(k_docs),
        )
        # Temporal queries need a much larger candidate pool because dense
        # retrieval can be flooded by larger neighbouring-year reports before
        # a single matching chunk surfaces. Used only when the query carries
        # an explicit year / quarter / month token.
        self.temporal_candidate_k = max(
            int(temporal_candidate_k or max(k_docs * 12, 96)),
            int(self.reranker_candidate_k),
        )
        self.recency_bias_weight = float(recency_bias_weight)
        self.max_chunks_per_doc = max(int(max_chunks_per_doc), 1)
        self.per_doc_penalty = float(per_doc_penalty)

        # Load variables from .env
        load_dotenv()

        env_model_override = os.getenv("STATSCHAT_GENERATIVE_MODEL")
        if env_model_override:
            self.logger.info(
                "Overriding generative model from environment: " f"{env_model_override}"
            )
            generative_model_name = env_model_override

        self.generative_model_name = generative_model_name

        if provider == "openai":
            sec_key = os.getenv("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model=generative_model_name,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens,
                api_key=sec_key,
            )

        elif provider == "openrouter":
            sec_key = os.getenv("OPENROUTER_API_KEY")
            api_base = os.getenv("OPENROUTER_BASE_URL")
            self.llm = ChatOpenAI(
                model=generative_model_name,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens,
                openai_api_key=sec_key,
                openai_api_base=api_base,
            )

        elif provider == "huggingface_inference":
            sec_key = os.getenv("HF_TOKEN")
            self.llm = HuggingFaceEndpoint(
                repo_id=generative_model_name,
                model_kwargs={"max_length": llm_max_tokens},
                temperature=llm_temperature,
                token=sec_key,
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Embeddings
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        # Load FAISS databases
        self.db = FAISS.load_local(
            faiss_db_root, embeddings, allow_dangerous_deserialization=True
        )
        if faiss_db_root_latest is None:
            faiss_db_root_latest = faiss_db_root + "_latest"
        self.db_latest = FAISS.load_local(
            faiss_db_root_latest, embeddings, allow_dangerous_deserialization=True
        )

        return None

    def _raise_model_availability_error(self, exc: Exception) -> None:
        """Raise a clearer provider/model configuration error."""

        if self.provider == "openrouter":
            message = (
                "OpenRouter could not route the configured model "
                f"'{self.generative_model_name}'. This can happen even if the "
                "model still has a page on openrouter.ai. Update "
                "statschat/config/main.toml to a currently served model, such as "
                "'mistralai/mistral-small-3.1-24b-instruct:free' for no-cost "
                "testing or 'mistralai/mistral-nemo' for a low-cost paid option."
            )
        else:
            message = (
                "The configured model "
                f"'{self.generative_model_name}' is not available for provider "
                f"'{self.provider}'."
            )

        self.logger.error(message)
        raise RuntimeError(message) from exc

    def _raise_rate_limit_error(self, exc: Exception) -> None:
        """Raise a clearer rate-limit error for the configured provider/model."""

        if self.provider == "openrouter":
            message = (
                "OpenRouter rate-limited the configured model "
                f"'{self.generative_model_name}'. Free models can be temporarily "
                "throttled upstream. Retry shortly, or switch "
                "statschat/config/main.toml to a paid low-cost model such as "
                "'mistralai/mistral-nemo' if you need more consistent access."
            )
        else:
            message = (
                "The configured model "
                f"'{self.generative_model_name}' hit a rate limit for provider "
                f"'{self.provider}'."
            )

        self.logger.error(message)
        raise RuntimeError(message) from exc

    @staticmethod
    def flatten_meta(d):
        """Utility, raise metadata within nested dicts."""
        return d | d.pop("metadata")

    @staticmethod
    def _dedupe_exact_chunks(records: list[dict]) -> list[dict]:
        """Remove exact duplicate chunks while keeping distinct pages from one report."""
        seen: set[tuple[str, str]] = set()
        deduped: list[dict] = []
        for record in records:
            signature = (
                str(record.get("page_url", "")).strip(),
                str(record.get("page_content", "")).strip(),
            )
            if signature in seen:
                continue
            seen.add(signature)
            deduped.append(record)
        return deduped

    @staticmethod
    def _latest_filter_enabled(latest_filter: bool | str) -> bool:
        """Normalize latest-filter flags from API/query inputs."""
        if isinstance(latest_filter, bool):
            return latest_filter
        return str(latest_filter).strip().lower() in {"on", "true", "1", "yes"}

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove simple HTML markup from text for safe display."""
        return re.sub(r"<[^>]+>", "", text)

    def similarity_search(
        self,
        query: str,
        latest_filter: bool = True,
        return_dicts: bool = True,
        candidate_k: int | None = None,
    ) -> list[dict]:
        """
        Returns k document chunks with the highest relevance to the
        query

        Args:
            query (str): Question for which most relevant publications will
            be returned
            return_dicts: if True, data returned as dictionary, key = rank

        Returns:
            List[dict]: List of top k article chunks by relevance
        """
        self.logger.info("Retrieving most relevant text chunks")
        if candidate_k is None:
            candidate_k = getattr(self, "reranker_candidate_k", self.k_docs)
        if latest_filter:
            top_matches = self.db_latest.similarity_search_with_score(
                query=query, k=candidate_k
            )
        else:
            top_matches = self.db.similarity_search_with_score(
                query=query, k=candidate_k
            )

        # filter to document matches with similarity scores less than...
        # i.e. closest cosine distances to query
        top_matches = [x for x in top_matches if x[-1] <= self.similarity_threshold]

        if return_dicts:
            return [
                self.flatten_meta(doc[0].dict()) | {"score": float(doc[1])}
                for doc in top_matches
            ]
        return top_matches

    def _rerank_results(
        self, query: str, docs: list[dict], latest_weight: float = 0.0
    ) -> list[dict]:
        """Rerank FAISS candidates with a cross-encoder and year-aware recency bias."""
        if not docs:
            return docs

        reranker_model_name = getattr(self, "reranker_model_name", None)
        if reranker_model_name:
            reranker = _get_reranker(reranker_model_name)
            pairs = [(query, _build_reranker_passage(doc)) for doc in docs]
            ce_scores = reranker.predict(pairs)
            for doc, ce_score in zip(docs, ce_scores):
                doc["reranker_score"] = float(ce_score)
        else:
            for doc in docs:
                doc["reranker_score"] = -float(doc.get("score", 0.0))

        effective_bias = getattr(self, "recency_bias_weight", 0.5) * max(
            float(latest_weight), 0.0
        )
        docs = _apply_recency_bias(docs, query, effective_bias)
        docs.sort(
            key=lambda doc: float(
                doc.get("selection_score", doc.get("reranker_score", 0.0))
            ),
            reverse=True,
        )
        self.logger.info(f"Reranked {len(docs)} results with cross-encoder")
        return docs

    def query_texts(self, query: str, docs: list[dict]) -> LlmResponse:
        """
        Generates an answer to the query based on relationship
        to docs filtered in similarity_search

        Args:
            query (str): Question for which most relevant publications will
            be returned
            docs (list[dict]): Documents closely related to query

        Returns:
            LlmResponse: Generated response to query (pydantic model)
        """
        # Handle case: no search results
        if not docs:
            return LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
            )

        selected_docs = select_generation_contexts(
            docs,
            self.k_contexts,
            max_chunks_per_doc=getattr(self, "max_chunks_per_doc", 3),
            per_doc_penalty=getattr(self, "per_doc_penalty", 0.2),
        )

        # reshape Document object structure
        top_matches = [
            Document(
                page_content=text["page_content"],
                metadata={
                    "doc_num": i + 1,
                    "date": text["date"],
                    "title": text["title"],
                },
            )
            for i, text in enumerate(selected_docs)
        ]
        self.logger.info(f"Passing top {len(top_matches)} results for QA")

        # stuff all above documents to the model
        chain = load_qa_with_sources_chain(
            self.llm,
            chain_type="stuff",
            prompt=self.extractive_prompt,
            document_prompt=self.stuff_document_prompt,
            verbose=self.verbose,
        )

        # parameter values
        try:
            response = chain.invoke(
                {"input_documents": top_matches, "question": query},
                return_only_outputs=True,
            )
        except NotFoundError as exc:
            self._raise_model_availability_error(exc)
        except RateLimitError as exc:
            self._raise_rate_limit_error(exc)

        parser = PydanticOutputParser(pydantic_object=LlmResponse)
        try:
            if "output_text" in response:
                validated_answer = parser.parse(response["output_text"])
            elif "properties" in response:
                validated_answer = parser.parse(response["properties"])
            else:
                validated_answer = parser.parse(response)
        except Exception as e:
            self.logger.error(f"Cannot parse response: {e}")
            self.logger.error(f"response: {response}")
            return LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
                reasoning=f"Cannot parse response: {e} /n/n  response: {response}",
            )

        return validated_answer

    @lru_cache()
    def make_query(
        self,
        question: str,
        latest_filter: str = "on",
        highlighting: bool = True,
        latest_weight: float = 1,
    ) -> tuple[list[dict], str, LlmResponse]:
        """
        Utility, wraps code for querying the search engine, and then the summarizer.
        Also handles storing the last answer made for feedback purposes.

        Args:
            question (str): The user query.
            latest_filter (str, optional): Whether to filter to bulletins with
                'latest' flag.  Values 'on', 'On', 'true', 'True' are all indicative
                for filtering. Defaults to 'on'.
            highlighting (bool, optional): Whether highlighting to be used.
                Defaults to true.
            latest_weight (float, optional): How much the score of retrieved
                publications should be reweighted towards the recent. Defaults to 1.

        Returns:
            list[dict]: supporting documents (with highlighting)
            str: formatted answer for app to display
            LlmResponse: Generated response to query (pydantic model)
        """
        self.logger.info(f"Search query: {question}")

        # Detect explicit temporal constraints in the query. When present, we
        # widen the candidate pool and prefer to rerank only the subset of
        # docs whose metadata actually matches that period — this is the
        # cleanest way to stop dense retrieval from being seduced by larger
        # neighbouring-year reports.
        query_temporal = parse_temporal_tokens(question)
        is_temporal_query = bool(
            query_temporal["years"]
            or query_temporal["months"]
            or query_temporal["quarters"]
        )
        candidate_k = (
            getattr(self, "temporal_candidate_k", None) if is_temporal_query else None
        )

        docs1 = self.similarity_search(
            question,
            latest_filter=self._latest_filter_enabled(latest_filter),
            candidate_k=candidate_k,
        )

        if len(docs1) == 0:
            empty_response = LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
            )
            return docs1, "", empty_response
        docs = self._dedupe_exact_chunks(docs1)

        if is_temporal_query:
            temporal_subset = [
                doc
                for doc in docs
                if _doc_matches_query_temporal(
                    query_temporal, _doc_temporal_tokens(doc)
                )
            ]
            if temporal_subset:
                self.logger.info(
                    f"Temporal pre-filter: reranking {len(temporal_subset)} of "
                    f"{len(docs)} candidates that match query temporal tokens "
                    f"{query_temporal}"
                )
                docs = temporal_subset
            else:
                self.logger.info(
                    f"Temporal pre-filter: no candidates matched {query_temporal}; "
                    "falling back to full pool"
                )

        docs = self._rerank_results(question, docs, latest_weight=latest_weight)
        docs = docs[: getattr(self, "k_docs", len(docs))]

        for doc in docs:
            doc["score"] = round(doc["score"], 2)
            if "reranker_score" in doc:
                doc["reranker_score"] = round(float(doc["reranker_score"]), 4)
            if "selection_score" in doc:
                doc["selection_score"] = round(float(doc["selection_score"]), 4)

        best_distance = (
            min(float(doc["score"]) for doc in docs) if docs else float("inf")
        )

        self.logger.info(
            f"Received {len(docs)} references"
            + f" with top distance {best_distance if docs else 'Inf'}"
        )

        validated_response = self.query_texts(question, docs)
        self.logger.info(f"QAPAIR - Question: {question}, Answer: {validated_response}")

        if highlighting:
            docs = highlighter(
                docs, validated_response=validated_response, logger=self.logger
            )
        self.logger.info(f"QASOURCE - Docs: {docs}")

        if validated_response.answer_provided is False:
            answer_str = ""
        else:
            # Web/chat clients expect a human-readable plain-text answer.
            # Prefer the model's synthesized answer; highlighting phrases are
            # often fragments intended for UI emphasis rather than the final
            # answer text.
            highlighted = (
                validated_response.highlighting1[0]
                if getattr(validated_response, "highlighting1", None)
                and len(validated_response.highlighting1) > 0
                else ""
            )
            highlighted = self._strip_html(highlighted).strip()
            if highlighted and not highlighted.endswith((".", "!", "?")):
                highlighted += "."

            most_likely = self._strip_html(
                getattr(validated_response, "most_likely_answer", "") or ""
            ).strip()

            answer_str = most_likely or highlighted

        if best_distance > self.answer_threshold:
            answer_str = (
                "No suitable answer found."
                + "However relevant information may be found in a PDF."
                + "Please check the link(s) provided."
            )

        else:
            answer_str = answer_str

        if best_distance > self.document_threshold:
            document_string = "No suitable PDFs found. Please refer to context"

            context_string = "No context available. Please refer to response"

            # Ensure the answer text is consistent with placeholder references.
            # (Avoid suggesting that links are available when they are not.)
            answer_str = (
                "No suitable PDFs found for this question. Please try rephrasing."
            )

            docs.clear()

            docs.extend([document_string, context_string])

        else:
            docs = docs

        return docs, answer_str, validated_response


if __name__ == "__main__":
    from statschat import load_config

    logger = logging.getLogger(__name__)
    # Config file to load
    CONFIG = load_config(name="main")
    # initiate Statschat AI and start the app
    inquirer = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)

    # question = "Where can I find the registered births by age of mother and county?"
    # question = "What is the sample size of the Real Estate Survey?"
    # question = "How is core inflation calculated?"
    # question = "What was inflation in Kenya in December 2022?"
    # question = "What is football?"
    # question = "What was the population of Kenya in 2019?"
    # question = "How many counties are there in Kenya?"
    # question = "What is the Kenya National Bureau of Statistics?"
    # question = "What was inflation in Kenya in 2022?"
    # question = "What was Kenya's GDP growth rate in 2023?"
    # question = "What is the total area of Kenya?"
    # question = "What was inflation in Kenya in 2022?"
    # question = "What was Kenya's inflation rate in Q1 2023?"
    # question = "What is the latest official GDP figure for 2025?"
    # question = "What was Kenya's GDP growth rate in Q3 2025?"
    # question = "How much did the economy expand in the third quarter of 2025?"
    # question = "What was inflation in Kenya in 2022?"
    # question = "What was the inflation rate in Kenya in 2021?"
    # question = "What was the inflation rate in Kenya in July 2022?"
    # question = "What was the inflation rate in Kenya in August 2022?"
    # question = "What was the year on year inflation rate in August 2022?"
    question = "What was the inflation rate in December 2022?"
    # question = "What was Kenya's Consumer Price Index inflation rate in December 2022?"
    # question = "What was inflation in Kenya in 2023?"
    # question = "By how much did Kenya's GDP grow in 2024?"
    # question = "What proportion of women own agricultural land in Kenya?"

    docs, answer, response = inquirer.make_query(
        question,
        latest_filter="off",
    )

    test_thresholds = "NO"

    print("-------------------- ANSWER --------------------")

    if test_thresholds == "YES":
        print(answer)

    elif test_thresholds == "NO":
        print(answer)
        if not docs or not isinstance(docs[0], dict):
            print("No document metadata available for this question.")
        else:
            page_url = docs[0]["page_url"]
            # Extract document name from URL
            document_url = docs[0]["url"]
            split_url = document_url.split("/")
            doc_id = split_url[-1]
            document_name = doc_id[:-4]
            document_title = docs[0]["title"]

    print("-------------------- DOCUMENT -------------------")
    if test_thresholds == "YES":
        print(docs[0])

    elif test_thresholds == "NO":
        if "document_title" in locals():
            print(f"The document title is {document_title}.")
            print(f"The file name is {document_name}.")
            print(f"You can read more from the document at {page_url}.")
        else:
            print("No document details available.")

    print("------------------ CONTEXT INFO ------------------")
    if test_thresholds == "YES":
        print(docs[1])

    elif test_thresholds == "NO":
        print(docs)

    print("------------------ FULL RESPONSE -----------------")
    print(response)
