import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.output_parsers import PydanticOutputParser
from statschat.generative.response_model import LlmResponse
from statschat.generative.prompts_cloud import (
    EXTRACTIVE_PROMPT_PYDANTIC,
    STUFF_DOCUMENT_PROMPT,
)
from functools import lru_cache
from statschat.generative.utils import deduplicator, highlighter
from statschat.embedding.latest_flag_helpers import time_decay


class Inquirer:
    """
    Wraps the logic for using an LLM to synthesise a written answer from
    the text of a set of searched/retrieved documents.
    """

    def __init__(
        self,
        generative_model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
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

        # Load variables from .env
        load_dotenv()

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

            if not sec_key or not api_base:
                raise ValueError(
                    "Missing OpenRouter configuration. Set OPENROUTER_API_KEY and OPENROUTER_BASE_URL in your .env."
                )

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
        resolved_root = self._resolve_faiss_root(faiss_db_root)

        if faiss_db_root_latest is None:
            faiss_db_root_latest = f"{faiss_db_root}_latest"
        resolved_latest_root = self._resolve_faiss_root(
            faiss_db_root_latest,
            fallback_name=Path(resolved_root).name,
            fallback_path=resolved_root,
        )

        self.db = FAISS.load_local(
            resolved_root, embeddings, allow_dangerous_deserialization=True
        )
        self.db_latest = FAISS.load_local(
            resolved_latest_root, embeddings, allow_dangerous_deserialization=True
        )

        return None

    @staticmethod
    def _resolve_faiss_root(
        root: str,
        *,
        fallback_name: str | None = None,
        fallback_path: str | None = None,
    ) -> str:
        """Resolve a FAISS DB directory path.

        The project typically uses `data/db_langchain` (and optionally
        `data/db_langchain_latest`). In some local runs the database can
        end up nested as `data/data/db_langchain` (e.g., if the pipeline
        was executed from within the `data/` directory).

        If `root` does not exist, we try a small set of sane fallbacks.
        """

        candidate = Path(root)
        if candidate.exists():
            return str(candidate)

        # Common accidental nesting: data/data/<db_name>
        db_name = candidate.name
        nested = Path("data") / "data" / db_name
        if nested.exists():
            return str(nested)

        # Optional explicit fallback (e.g., use base DB when _latest missing)
        if fallback_path is not None and Path(fallback_path).exists():
            return str(Path(fallback_path))

        # Provide a focused, actionable error message.
        expected_files = [candidate / "index.faiss", candidate / "index.pkl"]
        hint = (
            "Vector store not found. Expected FAISS files like "
            f"{expected_files[0]} and {expected_files[1]}. "
            "Create/update the vector store by running `python3 statschat/pdf_runner.py` "
            "from the repo root, or update `statschat/config/main.toml` to point at the correct `faiss_db_root`."
        )
        raise FileNotFoundError(hint)

    @staticmethod
    def flatten_meta(d):
        """Utility, raise metadata within nested dicts."""
        return d | d.pop("metadata")

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove simple HTML markup from text for safe display."""
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def _extract_month_year(text: str) -> str | None:
        """Extract a 'Month YYYY' substring from text, if present.

        Used to bias retrieval when a user asks about a specific month/year.
        """

        months = (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        )
        month_re = "|".join(months)
        m = re.search(rf"\b({month_re})\s+(20\d{{2}})\b", text, flags=re.IGNORECASE)
        if not m:
            return None

        return f"{m.group(1).capitalize()} {m.group(2)}"

    @staticmethod
    def _parse_latest_filter(latest_filter) -> bool:
        """Normalize the user/API `latest_filter` input to a boolean."""

        if isinstance(latest_filter, bool):
            return latest_filter
        if latest_filter is None:
            return True
        if isinstance(latest_filter, str):
            value = latest_filter.strip().lower()
            return value in {"on", "true", "1", "yes"}

        return bool(latest_filter)

    def similarity_search(
        self, query: str, latest_filter: bool = True, return_dicts: bool = True
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

        month_year_hint = self._extract_month_year(query)
        k_docs = self.k_docs
        if month_year_hint is not None:
            # Date-specific questions can require a larger top-k to surface the
            # correct month/year bulletin.
            k_docs = max(k_docs, 50)

        if latest_filter:
            top_matches = self.db_latest.similarity_search_with_score(
                query=query, k=k_docs
            )
        else:
            top_matches = self.db.similarity_search_with_score(query=query, k=k_docs)

        # filter to document matches with similarity scores less than...
        # i.e. closest cosine distances to query
        top_matches = [x for x in top_matches if x[-1] <= self.similarity_threshold]

        # If a month/year is explicitly requested (e.g. "April 2025"), promote
        # docs with matching metadata date ("01 April 2025" contains "April 2025").
        if month_year_hint is not None:

            def _sort_key(item: tuple[Document, float]) -> tuple[int, float]:
                doc, score = item
                date_str = str((getattr(doc, "metadata", None) or {}).get("date", ""))
                is_match = month_year_hint.lower() in date_str.lower()
                return (0 if is_match else 1, float(score))

            top_matches.sort(key=_sort_key)

        if return_dicts:
            return [
                self.flatten_meta(doc[0].dict()) | {"score": float(doc[1])}
                for doc in top_matches
            ]
        return top_matches

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
            for i, text in enumerate(docs[: self.k_contexts])
            if text["score"] <= 1.5 * docs[0]["score"]
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
        response = chain.invoke(
            {"input_documents": top_matches, "question": query},
            return_only_outputs=True,
        )

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

        month_year_hint = self._extract_month_year(question)
        # For explicit month/year questions, do not bias toward recency.
        effective_latest_weight = 0 if month_year_hint is not None else latest_weight

        docs1 = self.similarity_search(
            question, latest_filter=self._parse_latest_filter(latest_filter)
        )

        if len(docs1) == 0:
            empty_response = LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
            )
            return docs1, "", empty_response
        docs = deduplicator(docs1, keys=["title", "date"])

        if effective_latest_weight > 0:
            for doc in docs:
                # Divided by decay term because similarity scores are inverted
                # Original score is L2 distance; lower is better
                # https://python.langchain.com/docs/integrations/vectorstores/faiss
                doc["score"] = doc["score"] / time_decay(
                    doc["date"], latest=effective_latest_weight
                )
            docs.sort(key=lambda doc: doc["score"])
            self.logger.info(
                "Weighted and reordered docs to latest with "
                + f"decay = {effective_latest_weight}"
            )

        for doc in docs:
            doc["score"] = round(doc["score"], 2)

        self.logger.info(
            f"Received {len(docs)} references"
            + f" with top distance {docs[0]['score'] if docs else 'Inf'}"
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
            # Prefer the model-provided highlight sentence when available.
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

            answer_str = highlighted or most_likely

        if docs[0]["score"] > self.answer_threshold:
            answer_str = (
                "No suitable answer found."
                + "However relevant information may be found in a PDF."
                + "Please check the link(s) provided."
            )

        else:
            answer_str = answer_str

        if docs[0]["score"] > self.document_threshold:
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
    # question = "What was the inflation rate in December 2022?"
    # question = "What was Kenya's Consumer Price Index inflation rate in December 2022?"
    # question = "What was inflation in Kenya in 2023?"
    # question = "By how much did Kenya's GDP grow in 2024?"
    # question = "What proportion of women own agricultural land in Kenya?"
    # question = "What is the latest official GDP figure for 2025?"
    question = "What is the consumer price index in April 2025?"

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
