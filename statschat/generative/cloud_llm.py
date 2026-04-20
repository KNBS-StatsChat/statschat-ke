import logging
import os
import re
from collections import defaultdict
from datetime import date
from functools import lru_cache

from dotenv import load_dotenv
from rapidfuzz import fuzz
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
NON_KENYA_COUNTRY_PATTERN = re.compile(
    r"\b("
    r"tanzania|uganda|ethiopia|nigeria|rwanda|burundi|south\s+sudan|sudan|"
    r"somalia|djibouti|eritrea|democratic\s+republic\s+of\s+congo|drc|"
    r"congo|zambia|malawi|mozambique|south\s+africa|ghana"
    r")\b",
    re.IGNORECASE,
)
POLICY_ADVICE_PATTERN = re.compile(
    r"(^|\b)(should|recommend|recommendation|recommendations)\b|"
    r"\bwhat\s+polic(?:y|ies)\s+should\b",
    re.IGNORECASE,
)
SUBJECTIVE_JUDGEMENT_PATTERN = re.compile(
    r"\b(best|worst|performing\s+well|compared\s+to\s+its\s+potential)\b",
    re.IGNORECASE,
)
UNSUPPORTED_TOPIC_PATTERN = re.compile(
    r"\b(knbs\s+director\s+general|director\s+general).*\bsalary\b|"
    r"\bsalary\b.*\b(knbs\s+director\s+general|director\s+general)\b|"
    r"\b(military\s+expenditure|defen[cs]e\s+spending)\b",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
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

REPORT_FAMILY_DOC_PATTERNS = {
    "economic_survey": (re.compile(r"\beconomic survey\b", re.IGNORECASE),),
    "facts_and_figures": (
        re.compile(r"\b(?:kenya )?facts (?:and|&) figures\b", re.IGNORECASE),
    ),
    "statistical_abstract": (re.compile(r"\bstatistical abstract\b", re.IGNORECASE),),
    "construction_input_price_indices": (
        re.compile(r"\bconstruction input price ind(?:ex|ices)\b", re.IGNORECASE),
    ),
    "cpi_inflation": (
        re.compile(
            r"\b(?:consumer price indices?|consumer price index|cpi|inflation rates?)\b",
            re.IGNORECASE,
        ),
    ),
    "national_agriculture_production_report": (
        re.compile(r"\bnational agriculture production report\b", re.IGNORECASE),
    ),
    "gross_county_product": (re.compile(r"\bgross county product\b", re.IGNORECASE),),
    "kenya_demographic_and_health_survey": (
        re.compile(r"\b(?:kenya demographic and health survey|kdhs)\b", re.IGNORECASE),
    ),
    "kenya_housing_survey_basic_report": (
        re.compile(r"\bkenya housing survey\b", re.IGNORECASE),
        re.compile(r"\bbasic report\b", re.IGNORECASE),
    ),
    "finaccess": (re.compile(r"\bfinaccess\b", re.IGNORECASE),),
    "leading_economic_indicators": (
        re.compile(r"\bleading economic indicators?\b", re.IGNORECASE),
    ),
}

REPORT_FAMILY_QUERY_PATTERNS = {
    "economic_survey": (
        re.compile(r"\beconomic survey\b", re.IGNORECASE),
        re.compile(r"\bpetroleum product imports?\b", re.IGNORECASE),
        re.compile(r"\binternational visitor arrivals?\b", re.IGNORECASE),
        re.compile(r"\brecorded employment\b", re.IGNORECASE),
        re.compile(r"\bpopulation census\b.*\bdisabil", re.IGNORECASE),
        re.compile(r"\bdisabil.*\bpopulation census\b", re.IGNORECASE),
    ),
    "facts_and_figures": (
        re.compile(r"\bfacts (?:and|&) figures\b", re.IGNORECASE),
        re.compile(r"\bmodern sector\b.*\bwage employment\b", re.IGNORECASE),
        re.compile(r"\bwage employment\b.*\bmodern sector\b", re.IGNORECASE),
        re.compile(r"\bteachers service commission\b", re.IGNORECASE),
        re.compile(r"\bgdp at constant prices\b", re.IGNORECASE),
    ),
    "statistical_abstract": (
        re.compile(r"\bstatistical abstract\b", re.IGNORECASE),
        re.compile(r"\bholiday\b.*\bbusiness visitors?\b", re.IGNORECASE),
        re.compile(r"\bvisitor arrivals?\b", re.IGNORECASE),
        re.compile(r"\bunmilled wheat\b", re.IGNORECASE),
        re.compile(r"\bwheat\b.*\bimports?\b", re.IGNORECASE),
        re.compile(r"\bimports?\b.*\bwheat\b", re.IGNORECASE),
    ),
    "construction_input_price_indices": (
        re.compile(r"\bconstruction input price ind(?:ex|ices)\b", re.IGNORECASE),
        re.compile(r"\bconstruction inflation\b", re.IGNORECASE),
        re.compile(r"\bconstruction\b.*\binflation rate\b", re.IGNORECASE),
    ),
    "cpi_inflation": (
        re.compile(r"\binflation rates?\b", re.IGNORECASE),
        re.compile(r"\bconsumer price indices?\b", re.IGNORECASE),
        re.compile(r"\bconsumer price index\b", re.IGNORECASE),
        re.compile(r"\bcpi\b", re.IGNORECASE),
    ),
    "national_agriculture_production_report": (
        re.compile(r"\bnational agriculture production report\b", re.IGNORECASE),
        re.compile(r"\bagriculture production report\b", re.IGNORECASE),
        re.compile(r"\bagricultural sector\b.*\bgdp\b", re.IGNORECASE),
        re.compile(r"\bfood crops\b", re.IGNORECASE),
        re.compile(r"\bmaize\b", re.IGNORECASE),
        re.compile(r"\bsugar\b", re.IGNORECASE),
        re.compile(r"\baquaculture\b", re.IGNORECASE),
    ),
    "gross_county_product": (
        re.compile(r"\bgross county product\b", re.IGNORECASE),
        re.compile(r"\bgross value added\b", re.IGNORECASE),
        re.compile(r"\bgva\b", re.IGNORECASE),
    ),
    "kenya_demographic_and_health_survey": (
        re.compile(r"\bkenya demographic and health survey\b", re.IGNORECASE),
        re.compile(r"\bkdhs\b", re.IGNORECASE),
        re.compile(r"\bbirth certificate\b", re.IGNORECASE),
        re.compile(r"\bfamily planning\b", re.IGNORECASE),
        re.compile(r"\badolescent women\b", re.IGNORECASE),
        re.compile(r"\bhousehold size\b", re.IGNORECASE),
    ),
    "kenya_housing_survey_basic_report": (
        re.compile(r"\bhousing survey\b", re.IGNORECASE),
        re.compile(r"\bdwelling unit\b", re.IGNORECASE),
        re.compile(r"\bmobile phone\b.*\bownership status\b", re.IGNORECASE),
        re.compile(r"\bmobile phone\b.*\bregardless of ownership\b", re.IGNORECASE),
    ),
    "finaccess": (
        re.compile(r"\bfinaccess\b", re.IGNORECASE),
        re.compile(r"\bformal financial access\b", re.IGNORECASE),
        re.compile(r"\bfinancial access rate\b", re.IGNORECASE),
        re.compile(r"\bfinancial inclusion\b", re.IGNORECASE),
        re.compile(r"\bmobile money\b.*\bdaily\b", re.IGNORECASE),
        re.compile(r"\bfinancially healthy\b", re.IGNORECASE),
        re.compile(r"\bfinancial health\b", re.IGNORECASE),
    ),
    "leading_economic_indicators": (
        re.compile(r"\bleading economic indicators?\b", re.IGNORECASE),
        re.compile(r"\bbroad money supply\b", re.IGNORECASE),
        re.compile(r"\bm3\b", re.IGNORECASE),
    ),
}
GENERATION_PAGE_STOPWORDS = frozenset(
    {
        "according",
        "and",
        "are",
        "did",
        "for",
        "from",
        "kenya",
        "kenyan",
        "the",
        "this",
        "that",
        "was",
        "were",
        "what",
        "which",
        "with",
        "report",
    }
)


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


def _guardrail_refusal_reason(query: str, *, today: date | None = None) -> str | None:
    """Return a refusal reason for clearly out-of-scope public queries."""
    query_text = str(query or "").strip()
    if not query_text:
        return None

    if NON_KENYA_COUNTRY_PATTERN.search(query_text):
        return (
            "Question asks for statistics outside the Kenya/KNBS corpus or for an "
            "unsupported cross-country comparison."
        )

    if POLICY_ADVICE_PATTERN.search(query_text):
        return (
            "Question asks for policy advice or recommendations rather than an "
            "official KNBS statistical fact."
        )

    if SUBJECTIVE_JUDGEMENT_PATTERN.search(query_text):
        return (
            "Question asks for a subjective judgement rather than an official KNBS "
            "statistical fact."
        )

    if UNSUPPORTED_TOPIC_PATTERN.search(query_text):
        return (
            "Question asks for a topic outside the indexed KNBS statistical "
            "publication scope."
        )

    temporal = parse_temporal_tokens(query_text)
    today = today or date.today()
    future_years = {year for year in temporal["years"] if year > today.year}
    if future_years:
        return "Question asks for future or unpublished statistical data."

    if today.year in temporal["years"] and any(
        month > today.month for month in temporal["months"]
    ):
        return "Question asks for future or unpublished statistical data."

    return None


def guardrail_refusal_reason(query: str, *, today: date | None = None) -> str | None:
    """Public wrapper for API entrypoints that share cloud guardrails."""

    return _guardrail_refusal_reason(query, today=today)


def has_temporal_constraint(text: str) -> bool:
    """True if the text carries any year, month, or quarter token."""
    tokens = parse_temporal_tokens(text)
    return bool(tokens["years"] or tokens["months"] or tokens["quarters"])


def _matches_all_patterns(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    """Return True if every regex pattern matches the text."""
    return all(pattern.search(text) for pattern in patterns)


def _normalize_report_family_text(text: str) -> str:
    """Normalize URL/file-name separators before report-family regex matching."""
    return re.sub(r"\s+", " ", re.sub(r"[-_/]+", " ", str(text or ""))).strip()


def infer_query_report_families(text: str) -> set[str]:
    """Infer likely report families from explicit names or metric cues."""
    text = _normalize_report_family_text(text)
    families = {
        family
        for family, patterns in REPORT_FAMILY_QUERY_PATTERNS.items()
        if any(pattern.search(text) for pattern in patterns)
    }
    if "construction_input_price_indices" in families:
        families.discard("cpi_inflation")
    return families


def _doc_report_families(doc: dict) -> set[str]:
    """Infer report families from document title and URL metadata."""
    parts = [
        str(doc.get("title", "")),
        str(doc.get("url", "")),
        str(doc.get("page_url", "")),
    ]
    text = _normalize_report_family_text(" ".join(parts))
    return {
        family
        for family, patterns in REPORT_FAMILY_DOC_PATTERNS.items()
        if _matches_all_patterns(text, patterns)
    }


def _select_lagged_year_subset(
    docs: list[dict], query_tokens: dict
) -> tuple[list[dict] | None, str | None]:
    """
    Prefer lagged publication years for year-only annual-summary queries.

    Many annual reports are published in the year after the data year they
    summarise, e.g. 2025 Economic Survey for 2024 outcomes.
    """
    if (
        not docs
        or not query_tokens["years"]
        or query_tokens["months"]
        or query_tokens["quarters"]
    ):
        return None, None

    max_query_year = max(query_tokens["years"])
    preference_order = [
        ({max_query_year + 1}, "year+1"),
        (set(query_tokens["years"]), "query year"),
        ({max_query_year + 2}, "year+2"),
    ]

    for preferred_years, label in preference_order:
        subset = [
            doc for doc in docs if _doc_temporal_tokens(doc)["years"] & preferred_years
        ]
        if subset:
            return subset, f"{label} {sorted(preferred_years)}"

    return None, None


def _lagged_year_label_rank(label: str | None) -> int:
    """Rank lagged-year preference labels; lower is more preferred."""
    if label is None:
        return 99
    if label.startswith("year+1"):
        return 0
    if label.startswith("query year"):
        return 1
    if label.startswith("year+2"):
        return 2
    return 99


def _doc_temporal_tokens(doc: dict) -> dict:
    """Extract temporal tokens from a doc's title, date, and URL metadata."""
    parts = [
        str(doc.get("title", "")),
        str(doc.get("date", "")),
        str(doc.get("url", "")),
        str(doc.get("page_url", "")),
    ]
    return parse_temporal_tokens(" ".join(parts))


def _doc_period_tokens(doc: dict) -> dict:
    """Extract the report period from title/URL before falling back to pub date.

    For editioned bulletins, publication dates can lag the reported period. A
    fourth-quarter 2023 construction bulletin may be published in 2024, but it
    should not satisfy a query asking for Q4 2024.
    """

    period_parts = [
        str(doc.get("title", "")),
        str(doc.get("url", "")),
        str(doc.get("page_url", "")),
    ]
    period_tokens = parse_temporal_tokens(" ".join(period_parts))
    if period_tokens["years"] or period_tokens["months"] or period_tokens["quarters"]:
        return period_tokens

    return parse_temporal_tokens(str(doc.get("date", "")))


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


def _select_precise_temporal_subset(
    docs: list[dict],
    query_tokens: dict,
    query_families: set[str],
) -> tuple[list[dict], str]:
    """Select docs matching precise query periods with family-specific handling."""

    if (
        "leading_economic_indicators" in query_families
        and query_tokens["years"]
        and query_tokens["months"]
        and not query_tokens["quarters"]
    ):
        preferred_years = {year + 1 for year in query_tokens["years"]}
        preferred_subset = [
            doc
            for doc in docs
            if (query_tokens["months"] & _doc_period_tokens(doc)["months"])
            and (preferred_years & _doc_period_tokens(doc)["years"])
        ]
        if preferred_subset:
            return preferred_subset, "leading indicators year+1 edition"

    exact_subset = [
        doc
        for doc in docs
        if _doc_matches_query_temporal(query_tokens, _doc_period_tokens(doc))
    ]
    return exact_subset, "exact report period"


def _extract_doc_year(doc: dict) -> int | None:
    """Best-effort publication year extraction from metadata."""
    date_text = str(doc.get("date", "")).strip()
    title_text = str(doc.get("title", "")).strip()
    years = _extract_years(f"{date_text} {title_text}")
    if not years:
        return None
    return max(years)


def _normalize_page_url(
    page_url: str | None, base_url: str | None, page_number: object | None
) -> str:
    """Return a fully qualified page URL when enough metadata is available."""
    page_url_str = str(page_url or "").strip()
    base_url_str = str(base_url or "").strip()

    if page_url_str and not page_url_str.startswith("#page="):
        return page_url_str

    if page_url_str.startswith("#page=") and base_url_str:
        return f"{base_url_str}{page_url_str}"

    if base_url_str and page_number not in (None, ""):
        return f"{base_url_str}#page={page_number}"

    return page_url_str


def _extract_page_number(doc: dict) -> int | None:
    """Best-effort page-number extraction from metadata or page URL."""
    raw_page_number = doc.get("page_number")
    if raw_page_number not in (None, ""):
        try:
            return int(str(raw_page_number).strip())
        except (TypeError, ValueError):
            pass

    page_url = _normalize_page_url(
        doc.get("page_url"), doc.get("url"), doc.get("page_number")
    )
    match = re.search(r"#page=(\d+)\b", page_url)
    if match:
        return int(match.group(1))
    return None


def _base_document_url(doc: dict) -> str:
    """Return the normalized document-level URL without any page fragment."""
    url = str(doc.get("url", "")).strip()
    if url:
        return url
    page_url = _normalize_page_url(
        doc.get("page_url"), doc.get("url"), doc.get("page_number")
    )
    return page_url.split("#", 1)[0].strip()


def _doc_group_key(doc: dict) -> str:
    """Stable grouping key for mild document diversification."""
    base_url = _base_document_url(doc)
    if base_url:
        return base_url.lower()
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


def _normalized_tokens(text: str) -> list[str]:
    """Return lowercase alphanumeric tokens for lightweight lexical scoring."""
    return TOKEN_PATTERN.findall(str(text).lower())


def _content_terms(text: str) -> list[str]:
    """Return query terms that carry signal for page-level selection."""
    return [
        token
        for token in _normalized_tokens(text)
        if len(token) >= 3 and token not in GENERATION_PAGE_STOPWORDS
    ]


def _ngrams(tokens: list[str], size: int) -> list[str]:
    """Return contiguous token n-grams."""
    if size <= 0 or len(tokens) < size:
        return []
    return [
        " ".join(tokens[index : index + size])
        for index in range(len(tokens) - size + 1)
    ]


def _score_generation_page_candidate(query: str, page_text: str) -> float:
    """Score whether a page is a good within-document generation candidate."""
    query_terms = _content_terms(query)
    if not query_terms:
        return 0.0

    page_terms = set(_content_terms(page_text))
    overlap_score = len(set(query_terms) & page_terms) * 10.0
    normalized_page = " ".join(_normalized_tokens(page_text))
    phrase_score = sum(
        5.0
        for phrase in _ngrams(query_terms, 2) + _ngrams(query_terms, 3)
        if phrase in normalized_page
    )
    fuzzy_score = (
        fuzz.partial_ratio(" ".join(_normalized_tokens(query)), normalized_page) / 10.0
    )
    return overlap_score + phrase_score + fuzzy_score


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
        page_expansion_doc_limit: int = 3,
        page_expansion_seed_pages_per_doc: int = 2,
        page_expansion_window: int = 1,
        generation_page_selection_enabled: bool = True,
        generation_page_shortlist_k: int = 24,
        lagged_year_candidate_k: int | None = None,
        initialize_llm: bool = True,
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
        # Only used for annual family/year queries that would otherwise fall
        # through to a year+2 proxy. Keep this larger pool narrowly gated so
        # the broader candidate surface does not perturb normal queries.
        self.lagged_year_candidate_k = max(
            int(lagged_year_candidate_k or max(self.temporal_candidate_k * 3, 320)),
            int(self.temporal_candidate_k),
        )
        self.recency_bias_weight = float(recency_bias_weight)
        self.max_chunks_per_doc = max(int(max_chunks_per_doc), 1)
        self.per_doc_penalty = float(per_doc_penalty)
        self.page_expansion_doc_limit = max(int(page_expansion_doc_limit), 0)
        self.page_expansion_seed_pages_per_doc = max(
            int(page_expansion_seed_pages_per_doc), 0
        )
        self.page_expansion_window = max(int(page_expansion_window), 0)
        self.generation_page_selection_enabled = bool(generation_page_selection_enabled)
        self.generation_page_shortlist_k = max(int(generation_page_shortlist_k), 0)

        # Load variables from .env
        load_dotenv()

        env_model_override = os.getenv("STATSCHAT_GENERATIVE_MODEL")
        if env_model_override:
            self.logger.info(
                "Overriding generative model from environment: " f"{env_model_override}"
            )
            generative_model_name = env_model_override

        self.generative_model_name = generative_model_name
        self.llm = None

        if not initialize_llm:
            self.logger.info(
                "Initialising cloud retrieval stack without a generation LLM."
            )
        elif provider == "openai":
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
        flattened = d | d.pop("metadata")
        flattened["page_url"] = _normalize_page_url(
            flattened.get("page_url"),
            flattened.get("url"),
            flattened.get("page_number"),
        )
        return flattened

    @staticmethod
    def _stored_document_to_record(doc) -> dict:
        """Convert a stored LangChain document into the dict shape used downstream."""
        if hasattr(doc, "model_dump"):
            payload = doc.model_dump()
        elif hasattr(doc, "dict"):
            payload = doc.dict()
        else:
            raise TypeError(f"Unsupported stored document type: {type(doc)!r}")
        return Inquirer.flatten_meta(payload)

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

    def _get_docstore_page_index(
        self, latest_filter_enabled: bool
    ) -> dict[str, dict[int, list[str]]]:
        """
        Lazily index FAISS docstore entries by document URL and page number.

        This supports a lightweight page-aware second pass without changing the
        global retriever: once a report family is retrieved, we can cheaply pull
        neighboring pages from the same source document.
        """
        cache = getattr(self, "_docstore_page_index_cache", {})
        cache_key = "latest" if latest_filter_enabled else "all"
        if cache_key in cache:
            return cache[cache_key]

        db = self.db_latest if latest_filter_enabled else self.db
        docstore_dict = getattr(getattr(db, "docstore", None), "_dict", None)
        if not isinstance(docstore_dict, dict):
            cache[cache_key] = {}
            self._docstore_page_index_cache = cache
            return {}

        index: defaultdict[str, defaultdict[int, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for doc_id, stored_doc in docstore_dict.items():
            metadata = getattr(stored_doc, "metadata", None)
            if metadata:
                record = {
                    "url": metadata.get("url"),
                    "page_url": metadata.get("page_url"),
                    "page_number": metadata.get("page_number"),
                }
            else:
                try:
                    record = self._stored_document_to_record(stored_doc)
                except TypeError:
                    continue
            base_url = _base_document_url(record).lower()
            page_number = _extract_page_number(record)
            if not base_url or page_number is None:
                continue
            index[base_url][page_number].append(doc_id)

        cache[cache_key] = {
            base_url: dict(page_map) for base_url, page_map in index.items()
        }
        self._docstore_page_index_cache = cache
        return cache[cache_key]

    def _expand_doc_local_candidates(
        self, docs: list[dict], latest_filter_enabled: bool
    ) -> list[dict]:
        """
        Pull neighboring pages from the top matched documents before final truncation.

        This is intentionally document-local: it preserves the current family/year
        routing, then improves page recall inside the already matched report family.
        """
        if not docs:
            return docs

        doc_limit = max(int(getattr(self, "page_expansion_doc_limit", 3)), 0)
        seed_pages_per_doc = max(
            int(getattr(self, "page_expansion_seed_pages_per_doc", 2)), 0
        )
        page_window = max(int(getattr(self, "page_expansion_window", 1)), 0)

        if doc_limit == 0 or seed_pages_per_doc == 0:
            return docs

        db = (
            getattr(self, "db_latest", None)
            if latest_filter_enabled
            else getattr(self, "db", None)
        )
        docstore_dict = getattr(getattr(db, "docstore", None), "_dict", None)
        if not isinstance(docstore_dict, dict):
            return docs

        page_index = self._get_docstore_page_index(latest_filter_enabled)
        if not page_index:
            return docs

        seed_pages_by_doc: dict[str, list[int]] = {}
        for doc in docs:
            base_url = _base_document_url(doc).lower()
            page_number = _extract_page_number(doc)
            if not base_url or page_number is None:
                continue

            if base_url not in seed_pages_by_doc:
                if len(seed_pages_by_doc) >= doc_limit:
                    continue
                seed_pages_by_doc[base_url] = []

            if page_number not in seed_pages_by_doc[base_url]:
                seed_pages_by_doc[base_url].append(page_number)

        if not seed_pages_by_doc:
            return docs

        base_scores_by_doc: dict[str, float] = {}
        for doc in docs:
            base_url = _base_document_url(doc).lower()
            if not base_url:
                continue
            doc_score = float(doc.get("score", float("inf")))
            current_best = base_scores_by_doc.get(base_url, float("inf"))
            base_scores_by_doc[base_url] = min(current_best, doc_score)

        expanded_docs = list(docs)
        seen = {
            (
                str(doc.get("page_url", "")).strip(),
                str(doc.get("page_content", "")).strip(),
            )
            for doc in docs
        }
        added = 0

        for base_url, seed_pages in seed_pages_by_doc.items():
            candidate_pages: set[int] = set()
            for page_number in seed_pages[:seed_pages_per_doc]:
                for candidate_page in range(
                    max(1, page_number - page_window), page_number + page_window + 1
                ):
                    candidate_pages.add(candidate_page)

            for candidate_page in sorted(candidate_pages):
                for doc_id in page_index.get(base_url, {}).get(candidate_page, []):
                    stored_doc = docstore_dict.get(doc_id)
                    if stored_doc is None:
                        continue
                    record = self._stored_document_to_record(stored_doc)
                    signature = (
                        str(record.get("page_url", "")).strip(),
                        str(record.get("page_content", "")).strip(),
                    )
                    if signature in seen:
                        continue
                    record["score"] = float(
                        base_scores_by_doc.get(base_url, float("inf"))
                    )
                    seen.add(signature)
                    expanded_docs.append(record)
                    added += 1

        if added:
            self.logger.info(
                "Doc-local page expansion: added %s neighboring chunks across %s docs",
                added,
                len(seed_pages_by_doc),
            )

        return expanded_docs

    def _rank_generation_page_shortlist(
        self,
        query: str,
        docs_for_group: list[dict],
        latest_filter_enabled: bool,
        shortlist_k: int,
    ) -> list[dict]:
        """Return the best page candidates inside one already-selected document."""
        if not docs_for_group or shortlist_k <= 0:
            return []

        base_url = _base_document_url(docs_for_group[0]).lower()
        if not base_url:
            return []

        db = (
            getattr(self, "db_latest", None)
            if latest_filter_enabled
            else getattr(self, "db", None)
        )
        docstore_dict = getattr(getattr(db, "docstore", None), "_dict", None)
        if not isinstance(docstore_dict, dict):
            return []

        page_index = self._get_docstore_page_index(latest_filter_enabled)
        if not page_index or base_url not in page_index:
            return []

        original_scores = {
            _extract_page_number(doc): float(doc.get("score", 0.0))
            for doc in docs_for_group
            if _extract_page_number(doc) is not None
        }
        best_by_page: dict[int, dict] = {}
        for page_number, doc_ids in page_index[base_url].items():
            for doc_id in doc_ids:
                stored_doc = docstore_dict.get(doc_id)
                if stored_doc is None:
                    continue
                record = self._stored_document_to_record(stored_doc)
                record_page = _extract_page_number(record)
                if record_page is None:
                    continue

                lexical_score = _score_generation_page_candidate(
                    query, str(record.get("page_content", ""))
                )
                record["generation_page_score"] = lexical_score
                record["score"] = original_scores.get(
                    record_page, record.get("score", 0.0)
                )
                current_best = best_by_page.get(record_page)
                if (
                    current_best is None
                    or lexical_score > current_best["generation_page_score"]
                ):
                    best_by_page[record_page] = record

        shortlisted = sorted(
            best_by_page.values(),
            key=lambda doc: float(doc.get("generation_page_score", 0.0)),
            reverse=True,
        )[:shortlist_k]
        if not shortlisted:
            return []

        reranker_model_name = getattr(self, "reranker_model_name", None)
        if not reranker_model_name:
            return shortlisted

        reranker = _get_reranker(reranker_model_name)
        pairs = [(query, _build_reranker_passage(doc)) for doc in shortlisted]
        ce_scores = reranker.predict(pairs)
        for doc, ce_score in zip(shortlisted, ce_scores):
            doc["generation_page_reranker_score"] = float(ce_score)

        shortlisted.sort(
            key=lambda doc: float(doc.get("generation_page_reranker_score", 0.0)),
            reverse=True,
        )
        return shortlisted

    def _refine_generation_context_pages(
        self,
        query: str,
        selected_docs: list[dict],
        latest_filter_enabled: bool,
    ) -> list[dict]:
        """
        Improve page choice inside each document's existing generation allocation.

        This deliberately does not add new documents or change the number of
        context slots each already-selected document receives. It only swaps in
        stronger pages from the same document when a capped within-document
        shortlist and rerank finds them.
        """
        if (
            not selected_docs
            or not getattr(self, "generation_page_selection_enabled", True)
            or not hasattr(self, "db")
        ):
            return selected_docs

        shortlist_k = max(int(getattr(self, "generation_page_shortlist_k", 24)), 0)
        if shortlist_k == 0:
            return selected_docs

        docs_by_group: defaultdict[str, list[dict]] = defaultdict(list)
        for doc in selected_docs:
            docs_by_group[_doc_group_key(doc)].append(doc)

        replacements_by_group: dict[str, list[dict]] = {}
        for doc_key, docs_for_group in docs_by_group.items():
            ranked_pages = self._rank_generation_page_shortlist(
                query,
                docs_for_group,
                latest_filter_enabled,
                shortlist_k,
            )
            if not ranked_pages:
                continue

            replacements_by_group[doc_key] = ranked_pages[: len(docs_for_group)]

        if not replacements_by_group:
            return selected_docs

        offsets_by_group: defaultdict[str, int] = defaultdict(int)
        refined_docs: list[dict] = []
        for doc in selected_docs:
            doc_key = _doc_group_key(doc)
            replacements = replacements_by_group.get(doc_key)
            offset = offsets_by_group[doc_key]
            offsets_by_group[doc_key] += 1

            if replacements and offset < len(replacements):
                refined_docs.append(replacements[offset])
            else:
                refined_docs.append(doc)

        return refined_docs

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

    def retrieve_documents(
        self,
        question: str,
        *,
        latest_filter: str | bool = "on",
        latest_weight: float = 1,
    ) -> tuple[list[dict], bool, float]:
        """Run the shared cloud retrieval pipeline without invoking an LLM.

        This is used by the cloud API before cloud generation and by the local
        API before local generation, so retrieval behavior can stay aligned
        across API modes.
        """

        latest_filter_enabled = self._latest_filter_enabled(latest_filter)
        query_temporal = parse_temporal_tokens(question)
        query_families = infer_query_report_families(question)
        is_temporal_query = bool(
            query_temporal["years"]
            or query_temporal["months"]
            or query_temporal["quarters"]
        )
        is_precise_temporal_query = bool(
            query_temporal["months"] or query_temporal["quarters"]
        )
        candidate_k = (
            getattr(self, "temporal_candidate_k", None)
            if (is_temporal_query or query_families)
            else None
        )

        docs1 = self.similarity_search(
            question,
            latest_filter=latest_filter_enabled,
            candidate_k=candidate_k,
        )
        if len(docs1) == 0:
            return docs1, latest_filter_enabled, float("inf")

        docs = self._dedupe_exact_chunks(docs1)

        def apply_family_filter(candidates: list[dict]) -> list[dict]:
            if not query_families:
                return candidates

            family_subset = [
                doc for doc in candidates if _doc_report_families(doc) & query_families
            ]
            if family_subset:
                self.logger.info(
                    "Report-family pre-filter: reranking %s of %s candidates for %s",
                    len(family_subset),
                    len(candidates),
                    sorted(query_families),
                )
                return family_subset

            self.logger.info(
                "Report-family pre-filter: no candidates matched %s; "
                "falling back to current pool",
                sorted(query_families),
            )
            return candidates

        docs = apply_family_filter(docs)

        def retry_wider_temporal_pool(reason: str) -> list[dict] | None:
            widened_candidate_k = getattr(
                self,
                "lagged_year_candidate_k",
                getattr(self, "temporal_candidate_k", 0),
            )
            if candidate_k is not None and widened_candidate_k <= candidate_k:
                return None

            self.logger.info(
                "Temporal candidate retry: widening candidates from %s to %s because %s",
                candidate_k,
                widened_candidate_k,
                reason,
            )
            widened_docs = self.similarity_search(
                question,
                latest_filter=latest_filter_enabled,
                candidate_k=widened_candidate_k,
            )
            widened_docs = self._dedupe_exact_chunks(widened_docs)
            return apply_family_filter(widened_docs)

        if is_precise_temporal_query:
            temporal_subset, temporal_subset_reason = _select_precise_temporal_subset(
                docs, query_temporal, query_families
            )
            if temporal_subset:
                self.logger.info(
                    f"Temporal pre-filter: reranking {len(temporal_subset)} of "
                    f"{len(docs)} candidates using {temporal_subset_reason} "
                    f"for query temporal tokens {query_temporal}"
                )
                docs = temporal_subset
            else:
                widened_docs = retry_wider_temporal_pool(
                    f"no candidates matched precise temporal tokens {query_temporal}"
                )
                widened_temporal_subset, widened_subset_reason = (
                    _select_precise_temporal_subset(
                        widened_docs or [], query_temporal, query_families
                    )
                )
                if widened_temporal_subset:
                    self.logger.info(
                        "Temporal pre-filter retry: reranking %s of %s widened "
                        "candidates using %s for query temporal tokens %s",
                        len(widened_temporal_subset),
                        len(widened_docs or []),
                        widened_subset_reason,
                        query_temporal,
                    )
                    docs = widened_temporal_subset
                else:
                    self.logger.info(
                        f"Temporal pre-filter: no candidates matched {query_temporal}; "
                        "falling back to current pool"
                    )
        elif query_families and query_temporal["years"]:
            lagged_subset, lagged_label = _select_lagged_year_subset(
                docs, query_temporal
            )
            if not lagged_label or not lagged_label.startswith("year+1"):
                widened_docs = retry_wider_temporal_pool(
                    "initial annual family pool missed preferred year+1 edition"
                )
                widened_subset, widened_label = _select_lagged_year_subset(
                    widened_docs or [], query_temporal
                )
                if widened_subset and _lagged_year_label_rank(
                    widened_label
                ) < _lagged_year_label_rank(lagged_label):
                    lagged_subset = widened_subset
                    lagged_label = widened_label
            if lagged_subset:
                self.logger.info(
                    "Annual-report year preference: reranking %s of %s candidates "
                    "using %s within %s",
                    len(lagged_subset),
                    len(docs),
                    lagged_label,
                    sorted(query_families),
                )
                docs = lagged_subset

        docs = self._rerank_results(question, docs, latest_weight=latest_weight)
        expanded_docs = self._expand_doc_local_candidates(docs, latest_filter_enabled)
        if len(expanded_docs) > len(docs):
            docs = self._rerank_results(
                question, expanded_docs, latest_weight=latest_weight
            )
        else:
            docs = expanded_docs
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
        return docs, latest_filter_enabled, best_distance

    def select_generation_documents(
        self,
        query: str,
        docs: list[dict],
        *,
        latest_filter_enabled: bool | None = None,
    ) -> list[dict]:
        """Select and refine generation contexts from retrieved documents."""

        selected_docs = select_generation_contexts(
            docs,
            self.k_contexts,
            max_chunks_per_doc=getattr(self, "max_chunks_per_doc", 3),
            per_doc_penalty=getattr(self, "per_doc_penalty", 0.2),
        )
        if latest_filter_enabled is not None:
            selected_docs = self._refine_generation_context_pages(
                query, selected_docs, latest_filter_enabled
            )
        return selected_docs

    def query_texts(
        self,
        query: str,
        docs: list[dict],
        *,
        latest_filter_enabled: bool | None = None,
    ) -> LlmResponse:
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

        selected_docs = self.select_generation_documents(
            query, docs, latest_filter_enabled=latest_filter_enabled
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
        guardrail_reason = _guardrail_refusal_reason(question)
        if guardrail_reason:
            self.logger.info("Guardrail refusal: %s", guardrail_reason)
            empty_response = LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
                reasoning=guardrail_reason,
            )
            return [], "", empty_response

        docs, latest_filter_enabled, best_distance = self.retrieve_documents(
            question,
            latest_filter=latest_filter,
            latest_weight=latest_weight,
        )
        if len(docs) == 0:
            empty_response = LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
            )
            return docs, "", empty_response

        self.logger.info(
            f"Received {len(docs)} references"
            + f" with top distance {best_distance if docs else 'Inf'}"
        )

        validated_response = self.query_texts(
            question, docs, latest_filter_enabled=latest_filter_enabled
        )
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
