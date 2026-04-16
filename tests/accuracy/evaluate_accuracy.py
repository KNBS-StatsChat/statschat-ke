#!/usr/bin/env python3
"""Evaluate StatsChat accuracy against the KNBS QA template."""
from __future__ import annotations

import argparse
import math
import re
import string
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from statschat.generative.local_llm import similarity_search

REQUIRED_COLUMNS = {
    "query_id",
    "query_text",
    "golden_answer",
    "relevant_doc_ids",
    "evidence_locations",
    "source_text",
    "should_answer",
    "Reviewers",
}

DEFAULT_REFUSAL_PHRASES = [
    "no suitable pdfs found",
    "no suitable answer found",
    "please try rephrasing",
    "cannot answer",
    "can not answer",
    "no official",
    "insufficient information",
    "i don't know",
    "i do not know",
]

NUMBER_PATTERN = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
PERCENT_PATTERN = re.compile(
    r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(%|percent|per cent)", re.IGNORECASE
)
SCALED_NUMBER_PATTERN = re.compile(
    r"(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"(?:\s*(?P<scale>thousand|million|billion|trillion|"
    r"\(?\s*['’`]?\s*0{3}\s*\)?))?",
    re.IGNORECASE,
)
QUOTE_PATTERN = re.compile(r"[\"“”]")
ARTICLE_PATTERN = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
REVIEWER_TOKEN_PATTERN = re.compile(r"^[A-Za-z]{1,4}$")

PERCENT_KEYWORDS = re.compile(
    r"(percent|percentage|rate|inflation|growth|share|proportion)",
    re.IGNORECASE,
)
SCALE_MULTIPLIERS = {
    "thousand": 1_000.0,
    "million": 1_000_000.0,
    "billion": 1_000_000_000.0,
    "trillion": 1_000_000_000_000.0,
}


@dataclass
class EvaluationResult:
    query_id: str
    query_text: str
    should_answer: Optional[bool]
    golden_answer: str
    predicted_answer: str
    predicted_relevant_doc_ids: Optional[str]
    predicted_evidence_locations: Optional[str]
    predicted_source_text: Optional[str]
    model_answered: Optional[bool]
    correct_refusal: Optional[bool]
    false_answer: Optional[bool]
    answered_when_expected: Optional[bool]
    answer_missing: Optional[bool]
    api_mode: Optional[str]
    reference_count: Optional[int]
    reference_url: Optional[str]
    reference_doc_id: Optional[str]
    reference_page: Optional[int]
    reference_doc_ids_all: Optional[str]
    reference_pages_all: Optional[str]
    reference_doc_match: Optional[bool]
    any_reference_doc_match: Optional[bool]
    evidence_page_match: Optional[bool]
    any_reference_page_match: Optional[bool]
    doc_hit_at_1: Optional[bool]
    doc_hit_at_k: Optional[bool]
    exact_match: Optional[int]
    token_f1: Optional[float]
    semantic_similarity: Optional[float]
    is_refusal: bool
    is_correct: Optional[bool]
    similarity_score: Optional[float]
    precision_at_k: Optional[float]
    recall_at_k: Optional[float]
    mrr: Optional[float]
    ndcg: Optional[float]
    retrieval_metric_source: Optional[str]
    retrieved_doc_ids: Optional[str]
    error: Optional[str]
    reasoning: Optional[str] = None
    context_texts: Optional[str] = None
    reference_scores: Optional[str] = None
    reference_titles: Optional[str] = None
    highlighting: Optional[str] = None
    context_from: Optional[str] = None
    context_reference: Optional[str] = None
    relevant_publications: Optional[str] = None
    scoring_method: Optional[str] = None
    pipeline_doc_hit_at_1: Optional[bool] = None
    pipeline_doc_hit_at_k: Optional[bool] = None
    pipeline_precision_at_k: Optional[float] = None
    pipeline_recall_at_k: Optional[float] = None
    pipeline_mrr: Optional[float] = None
    pipeline_ndcg: Optional[float] = None
    pipeline_page_precision_at_k: Optional[float] = None
    pipeline_page_recall_at_k: Optional[float] = None
    pipeline_page_mrr: Optional[float] = None
    pipeline_page_ndcg: Optional[float] = None


FAISS_PROXY_RENAME_MAP = {
    "doc_hit_at_1": "faiss_proxy_doc_hit_at_1",
    "doc_hit_at_k": "faiss_proxy_doc_hit_at_k",
    "precision_at_k": "faiss_proxy_precision_at_k",
    "recall_at_k": "faiss_proxy_recall_at_k",
    "mrr": "faiss_proxy_mrr",
    "ndcg": "faiss_proxy_ndcg",
    "retrieval_metric_source": "faiss_proxy_metric_source",
    "retrieved_doc_ids": "faiss_proxy_retrieved_doc_ids",
}


@dataclass
class Issue:
    query_id: str
    issue: str
    detail: str


def detect_qa_sheet_name(
    excel_path: Path, preferred_sheet: str = "QA_Data"
) -> tuple[str, list[str]]:
    """Return the sheet containing the QA table and workbook sheet names."""
    workbook = pd.ExcelFile(excel_path)
    sheet_names = workbook.sheet_names

    if preferred_sheet in sheet_names:
        header_df = pd.read_excel(excel_path, sheet_name=preferred_sheet, nrows=0)
        columns = {str(col).strip() for col in header_df.columns}
        if REQUIRED_COLUMNS.issubset(columns):
            return preferred_sheet, sheet_names

    matching_sheets: list[str] = []
    for sheet_name in sheet_names:
        header_df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=0)
        columns = {str(col).strip() for col in header_df.columns}
        if REQUIRED_COLUMNS.issubset(columns):
            matching_sheets.append(sheet_name)

    if not matching_sheets:
        raise ValueError(
            "No worksheet contains the required QA columns. "
            f"Required columns: {sorted(REQUIRED_COLUMNS)}"
        )

    return matching_sheets[0], sheet_names


def is_blank(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def cell_text(value: object) -> str:
    """Return a stripped string while preserving spreadsheet blanks as empty."""
    return "" if is_blank(value) else str(value).strip()


def normalize_bool(value: object) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        if value == 1 or value == 1.0:
            return True
        if value == 0 or value == 0.0:
            return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0"}:
        return False
    return None


def normalize_text(value: str) -> str:
    text = value.lower().strip()
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_for_em(text: str) -> str:
    text = normalize_text(text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = ARTICLE_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_numbers(text: str) -> list[float]:
    return [float(num.replace(",", "")) for num in NUMBER_PATTERN.findall(text)]


def parse_percent_numbers(text: str) -> list[float]:
    return [float(num.replace(",", "")) for num, _ in PERCENT_PATTERN.findall(text)]


def parse_scaled_numbers(text: str) -> list[float]:
    """
    Parse numbers with optional scale words such as thousand or million.

    This keeps equivalent forms like "4,285.2 thousand tonnes" and
    "4,285,206 tons" close enough for numeric comparison.
    """
    values: list[float] = []
    for match in SCALED_NUMBER_PATTERN.finditer(text):
        number = float(match.group("number").replace(",", ""))
        scale = str(match.group("scale") or "").lower()
        normalized_scale = re.sub(r"[\s()'’`]", "", scale)
        multiplier = (
            1_000.0
            if normalized_scale == "000"
            else SCALE_MULTIPLIERS.get(normalized_scale, 1.0)
        )
        values.append(number * multiplier)
    return values


def has_quotes(text: str) -> bool:
    return bool(QUOTE_PATTERN.search(text))


def split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def has_two_reviewer_initials(value: object) -> bool:
    if is_blank(value):
        return False
    text = str(value).strip()
    tokens = [token.strip() for token in re.split(r"[,&/+\s;]+", text) if token.strip()]
    if len(tokens) < 2:
        return False
    return all(REVIEWER_TOKEN_PATTERN.match(token) for token in tokens[:2])


def is_refusal_answer(answer: str, refusal_phrases: Iterable[str]) -> bool:
    text = normalize_text(answer)
    return any(phrase in text for phrase in refusal_phrases)


def numeric_match(
    golden: str,
    answer: str,
    abs_tol: float,
    rel_tol: float,
) -> bool:
    expects_percent = (
        "%" in golden or "percent" in golden.lower() or "per cent" in golden.lower()
    )
    answer_mentions_percent = (
        "%" in answer or "percent" in answer.lower() or "per cent" in answer.lower()
    )
    golden_numbers = (
        parse_percent_numbers(golden)
        if expects_percent
        else parse_scaled_numbers(golden)
    )
    if not golden_numbers:
        golden_numbers = parse_numbers(golden)
    if not golden_numbers:
        return False

    candidates = parse_scaled_numbers(answer)
    if answer_mentions_percent:
        candidates.extend(parse_percent_numbers(answer))

    if not candidates:
        return False

    def matches_expected(expected: float, candidate: float) -> bool:
        if expected == 0:
            if abs(candidate) <= abs_tol:
                return True
            return False

        effective_abs_tol = abs_tol
        if max(abs(expected), abs(candidate)) < 1:
            effective_abs_tol = min(abs_tol, 0.001)

        abs_diff = abs(candidate - expected)
        rel_diff = abs_diff / abs(expected)
        if abs_diff <= effective_abs_tol or rel_diff <= rel_tol:
            return True

        if expects_percent or answer_mentions_percent:
            for transformed in (candidate / 100, candidate * 100):
                transformed_abs_tol = abs_tol
                if max(abs(expected), abs(transformed)) < 1:
                    transformed_abs_tol = min(abs_tol, 0.001)
                transformed_abs_diff = abs(transformed - expected)
                transformed_rel_diff = transformed_abs_diff / abs(expected)
                if (
                    transformed_abs_diff <= transformed_abs_tol
                    or transformed_rel_diff <= rel_tol
                ):
                    return True

        return False

    for expected in golden_numbers:
        if not any(matches_expected(expected, candidate) for candidate in candidates):
            return False

    return True


def text_match(golden: str, answer: str) -> float:
    return float(fuzz.token_set_ratio(normalize_text(golden), normalize_text(answer)))


def token_f1_score(golden: str, answer: str) -> float:
    gold_tokens = normalize_for_em(golden).split()
    pred_tokens = normalize_for_em(answer).split()
    if not gold_tokens and not pred_tokens:
        return 1.0
    if not gold_tokens or not pred_tokens:
        return 0.0
    gold_counts = {}
    for token in gold_tokens:
        gold_counts[token] = gold_counts.get(token, 0) + 1
    overlap = 0
    for token in pred_tokens:
        if gold_counts.get(token, 0) > 0:
            overlap += 1
            gold_counts[token] -= 1
    precision = overlap / len(pred_tokens) if pred_tokens else 0.0
    recall = overlap / len(gold_tokens) if gold_tokens else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def exact_match_score(golden: str, answer: str) -> int:
    return int(normalize_for_em(golden) == normalize_for_em(answer))


class SemanticSimilarityEvaluator:
    def __init__(self, model_name: str) -> None:
        try:
            self.model = SentenceTransformer(model_name, local_files_only=True)
        except TypeError:
            self.model = SentenceTransformer(model_name)

    def similarity(self, golden: str, answer: str) -> float:
        embeddings = self.model.encode([golden, answer], convert_to_tensor=True)
        return float(cos_sim(embeddings[0], embeddings[1]).item())


def normalize_doc_id(value: str) -> str:
    text = value.strip().lower()
    if "://" in text:
        parsed = urlparse(text)
        if parsed.path:
            text = parsed.path.split("/")[-1]
    text = text.split("#", 1)[0]
    text = text.split("?", 1)[0]
    if text.endswith(".pdf"):
        text = text[: -len(".pdf")]
    text = re.sub(r"[_\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_page_from_url(url: str) -> Optional[int]:
    if not url:
        return None
    match = re.search(r"page=(\d+)", url)
    if match:
        return int(match.group(1))
    return None


def parse_evidence_pages(
    relevant_doc_ids: list[str], evidence_locations: list[str]
) -> dict[str, set[int]]:
    pages_by_doc: dict[str, set[int]] = {}
    normalized_docs = [
        normalize_doc_id(doc_id) for doc_id in relevant_doc_ids if doc_id.strip()
    ]
    fallback_doc = normalized_docs[0] if len(set(normalized_docs)) == 1 else None

    for evidence in evidence_locations:
        evidence_text = str(evidence).strip()
        if not evidence_text:
            continue

        match = re.search(r"(?i)(.+):\s*(p\.|pg\.|page)\s*([0-9]+)\s*$", evidence_text)
        if match:
            normalized_doc = normalize_doc_id(match.group(1))
            page = int(match.group(3))
            pages_by_doc.setdefault(normalized_doc, set()).add(page)
            continue

        page_match = re.search(r"(?i)(p\.|pg\.|page)\s*([0-9]+)", evidence_text)
        if page_match and fallback_doc:
            page = int(page_match.group(2))
            pages_by_doc.setdefault(fallback_doc, set()).add(page)

    return pages_by_doc


def make_page_key(doc_id: str, page: int) -> str:
    return f"{normalize_doc_id(doc_id)}:p.{page}"


def parse_predicted_evidence_pairs(value: object) -> list[tuple[str, int]]:
    if is_blank(value):
        return []

    pairs: list[tuple[str, int]] = []
    for evidence in split_semicolon(str(value)):
        match = re.search(r"(?i)^(.+):\s*p\.\s*([0-9]+)\s*$", evidence.strip())
        if not match:
            continue
        doc_id = normalize_doc_id(match.group(1))
        page = int(match.group(2))
        if doc_id:
            pairs.append((doc_id, page))
    return pairs


def flatten_evidence_page_keys(evidence_pages: dict[str, set[int]]) -> list[str]:
    page_keys: list[str] = []
    for doc_id, pages in evidence_pages.items():
        for page in sorted(pages):
            page_keys.append(make_page_key(doc_id, page))
    return page_keys


def extract_doc_id(match: dict) -> str:
    page_url = str(match.get("page_url", "")).strip()
    if page_url:
        parsed = urlparse(page_url)
        if parsed.path:
            return parsed.path.split("/")[-1]
    return str(match.get("title", "")).strip()


def detect_api_mode(payload: dict) -> str:
    references = payload.get("references")
    if isinstance(references, str):
        return "local"
    if isinstance(references, list):
        return "cloud"
    return "unknown"


def extract_reference_details(
    payload: dict,
) -> tuple[Optional[str], Optional[str], Optional[int], Optional[int], list[str]]:
    references = payload.get("references")
    reference_urls: list[str] = []
    if isinstance(references, str):
        reference_url = references.strip() or None
        reference_count = 1 if reference_url else 0
        if reference_url:
            reference_urls.append(reference_url)
    elif isinstance(references, list):
        reference_count = len(references)
        for item in references:
            if isinstance(item, dict):
                page_url = str(item.get("page_url") or "").strip()
                base_url = str(item.get("url") or "").strip()
                if page_url.startswith("#page=") and base_url:
                    candidate = f"{base_url}{page_url}"
                elif page_url:
                    candidate = page_url
                else:
                    candidate = base_url
                if candidate:
                    reference_urls.append(candidate)
            elif isinstance(item, str) and item.strip():
                reference_urls.append(item.strip())
        reference_url = reference_urls[0] if reference_urls else None
    else:
        reference_url = None
        reference_count = None

    reference_doc_id = None
    reference_page = None
    if reference_url:
        parsed_ref = urlparse(reference_url)
        reference_doc_id = normalize_doc_id(Path(parsed_ref.path).name)
        reference_page = extract_page_from_url(reference_url)
    return (
        reference_url,
        reference_doc_id,
        reference_page,
        reference_count,
        reference_urls,
    )


def extract_debug_details(payload: dict) -> dict[str, Optional[str]]:
    """Extract optional debug and context fields from local/cloud API payloads."""
    debug_response = payload.get("debug_response", {}) or {}

    reasoning_value = str(debug_response.get("reasoning", "")).strip()
    reasoning = reasoning_value or None

    highlights: list[str] = []
    for key in ("highlighting1", "highlighting2", "highlighting3"):
        value = debug_response.get(key)
        if isinstance(value, list):
            highlights.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None:
            text = str(value).strip()
            if text:
                highlights.append(text)
    highlighting = "; ".join(highlights) if highlights else None

    context_texts_list: list[str] = []
    reference_scores_list: list[str] = []
    reference_titles_list: list[str] = []
    references = payload.get("references")
    if isinstance(references, list):
        for item in references:
            if not isinstance(item, dict):
                continue
            page_content = str(item.get("page_content", "")).strip()
            if page_content:
                context_texts_list.append(page_content)

            score = item.get("score")
            if score is not None:
                try:
                    reference_scores_list.append(str(round(float(score), 4)))
                except (TypeError, ValueError):
                    pass

            title = str(item.get("title", "")).strip()
            if title:
                reference_titles_list.append(title)

    context_texts = "\n---\n".join(context_texts_list) if context_texts_list else None
    reference_scores = (
        ";".join(reference_scores_list) if reference_scores_list else None
    )
    reference_titles = (
        ";".join(unique_preserve_order(reference_titles_list))
        if reference_titles_list
        else None
    )

    context_from = str(payload.get("context_from", "")).strip() or None
    context_reference = str(payload.get("context_reference", "")).strip() or None

    publication_candidates = [
        str(payload.get("relevant_publication_one", "")).strip(),
        str(payload.get("relevant_publication_two", "")).strip(),
    ]
    relevant_publications = (
        "; ".join(pub for pub in publication_candidates if pub) or None
    )

    return {
        "reasoning": reasoning,
        "context_texts": context_texts,
        "reference_scores": reference_scores,
        "reference_titles": reference_titles,
        "highlighting": highlighting,
        "context_from": context_from,
        "context_reference": context_reference,
        "relevant_publications": relevant_publications,
    }


def primary_context_text(context_texts: Optional[str]) -> Optional[str]:
    """Return the first retrieved context chunk for concise reporting."""
    if not context_texts:
        return None
    first_chunk = str(context_texts).split("\n---\n", 1)[0].strip()
    return first_chunk or None


def compute_retrieval_metrics(
    relevant_doc_ids: list[str],
    retrieved_doc_ids: list[str],
    k: int,
    *,
    normalizer: Optional[Callable[[str], str]] = None,
) -> tuple[float, float, float, float]:
    normalize = normalizer or normalize_doc_id
    relevant_set = {
        normalize(doc_id) for doc_id in relevant_doc_ids if str(doc_id).strip()
    }
    retrieved_norm_all = [
        normalize(doc_id) for doc_id in retrieved_doc_ids if str(doc_id).strip()
    ]
    retrieved_unique: list[str] = []
    seen: set[str] = set()
    for doc_id in retrieved_norm_all:
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        retrieved_unique.append(doc_id)
    retrieved_norm = retrieved_unique[:k]

    if k == 0:
        return 0.0, 0.0, 0.0, 0.0

    hits = [1 if doc_id in relevant_set else 0 for doc_id in retrieved_norm]
    if len(hits) < k:
        hits.extend([0] * (k - len(hits)))
    precision = sum(hits) / k
    retrieved_relevant = {doc_id for doc_id in retrieved_norm if doc_id in relevant_set}
    recall = len(retrieved_relevant) / len(relevant_set) if relevant_set else 0.0

    mrr = 0.0
    for idx, hit in enumerate(hits, start=1):
        if hit:
            mrr = 1.0 / idx
            break

    dcg = sum(hit / math.log2(idx + 1) for idx, hit in enumerate(hits, start=1))
    ideal_hits = [1] * min(len(relevant_set), k)
    idcg = sum(hit / math.log2(idx + 1) for idx, hit in enumerate(ideal_hits, start=1))
    ndcg = dcg / idcg if idcg else 0.0
    return precision, recall, mrr, ndcg


def compute_doc_hit_flags(
    relevant_doc_ids: list[str],
    retrieved_doc_ids: list[str],
    k: int,
    *,
    normalizer: Optional[Callable[[str], str]] = None,
) -> tuple[bool, bool]:
    normalize = normalizer or normalize_doc_id
    relevant_set = {
        normalize(doc_id) for doc_id in relevant_doc_ids if str(doc_id).strip()
    }
    retrieved_norm_all = [
        normalize(doc_id) for doc_id in retrieved_doc_ids if str(doc_id).strip()
    ]
    retrieved_unique: list[str] = []
    seen: set[str] = set()
    for doc_id in retrieved_norm_all:
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        retrieved_unique.append(doc_id)

    top_k = retrieved_unique[:k]
    doc_hit_at_1 = bool(top_k) and top_k[0] in relevant_set
    doc_hit_at_k = any(doc_id in relevant_set for doc_id in top_k)
    return doc_hit_at_1, doc_hit_at_k


def compute_pipeline_reference_metrics(
    relevant_doc_ids: list[str],
    evidence_pages: dict[str, set[int]],
    reference_doc_ids: list[str],
    reference_pairs: list[tuple[str, int]],
    k: int,
) -> dict[str, Optional[float | bool]]:
    metrics: dict[str, Optional[float | bool]] = {
        "pipeline_doc_hit_at_1": None,
        "pipeline_doc_hit_at_k": None,
        "pipeline_precision_at_k": None,
        "pipeline_recall_at_k": None,
        "pipeline_mrr": None,
        "pipeline_ndcg": None,
        "pipeline_page_precision_at_k": None,
        "pipeline_page_recall_at_k": None,
        "pipeline_page_mrr": None,
        "pipeline_page_ndcg": None,
    }

    if relevant_doc_ids:
        (
            metrics["pipeline_precision_at_k"],
            metrics["pipeline_recall_at_k"],
            metrics["pipeline_mrr"],
            metrics["pipeline_ndcg"],
        ) = compute_retrieval_metrics(
            relevant_doc_ids=relevant_doc_ids,
            retrieved_doc_ids=reference_doc_ids,
            k=k,
        )
        (
            metrics["pipeline_doc_hit_at_1"],
            metrics["pipeline_doc_hit_at_k"],
        ) = compute_doc_hit_flags(
            relevant_doc_ids=relevant_doc_ids,
            retrieved_doc_ids=reference_doc_ids,
            k=k,
        )

    relevant_page_keys = flatten_evidence_page_keys(evidence_pages)
    if relevant_page_keys:
        retrieved_page_keys = [
            make_page_key(doc_id, page) for doc_id, page in reference_pairs
        ]
        (
            metrics["pipeline_page_precision_at_k"],
            metrics["pipeline_page_recall_at_k"],
            metrics["pipeline_page_mrr"],
            metrics["pipeline_page_ndcg"],
        ) = compute_retrieval_metrics(
            relevant_doc_ids=relevant_page_keys,
            retrieved_doc_ids=retrieved_page_keys,
            k=k,
            normalizer=lambda value: value.strip().lower(),
        )

    return metrics


def determine_scoring_method(
    *,
    should_answer: Optional[bool],
    refusal: bool,
    exact_match: Optional[int],
    numeric_correct: bool,
    golden_has_numbers: bool,
    similarity_score: Optional[float],
    similarity_threshold: float,
    token_f1: Optional[float],
    f1_threshold: float,
    semantic_similarity: Optional[float],
    semantic_threshold: float,
) -> Optional[str]:
    if should_answer is True:
        if refusal:
            return "refusal"
        if exact_match == 1:
            return "exact_match"
        if numeric_correct:
            return "numeric_match"
        if golden_has_numbers:
            return "none"
        if similarity_score is not None and similarity_score >= similarity_threshold:
            return "text_match"
        if token_f1 is not None and token_f1 >= f1_threshold:
            return "token_f1"
        if (
            semantic_similarity is not None
            and semantic_similarity >= semantic_threshold
        ):
            return "semantic_similarity"
        return "none"

    if should_answer is False:
        return "correct_refusal" if refusal else "false_answer"

    return None


def rename_faiss_proxy_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        old: new for old, new in FAISS_PROXY_RENAME_MAP.items() if old in df.columns
    }
    if not rename_map:
        return df
    return df.rename(columns=rename_map)


def results_to_dataframe(results: list[EvaluationResult]) -> pd.DataFrame:
    return rename_faiss_proxy_columns(
        pd.DataFrame([result.__dict__ for result in results])
    )


def dataframe_to_results(results_df: pd.DataFrame) -> list[EvaluationResult]:
    valid_fields = set(EvaluationResult.__dataclass_fields__.keys())
    reverse_rename_map = {new: old for old, new in FAISS_PROXY_RENAME_MAP.items()}
    rows: list[EvaluationResult] = []
    for row in results_df.to_dict(orient="records"):
        remapped_row = row.copy()
        for new_name, old_name in reverse_rename_map.items():
            if new_name in remapped_row and old_name not in remapped_row:
                remapped_row[old_name] = remapped_row[new_name]
        filtered = {
            key: value for key, value in remapped_row.items() if key in valid_fields
        }
        for field_name in valid_fields:
            filtered.setdefault(field_name, None)
        rows.append(EvaluationResult(**filtered))
    return rows


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def validate_rows(
    df: pd.DataFrame,
    require_reviewers: bool,
    query_id_prefix: str,
) -> list[Issue]:
    issues: list[Issue] = []

    query_id_pattern = re.compile(rf"^{re.escape(query_id_prefix)}\d+$")

    duplicates = df["query_id"].astype(str).duplicated(keep=False)
    for query_id in df.loc[duplicates, "query_id"].astype(str).tolist():
        issues.append(
            Issue(
                query_id=query_id,
                issue="duplicate_query_id",
                detail="Duplicate query_id",
            )
        )

    for _, row in df.iterrows():
        query_id = cell_text(row.get("query_id", ""))
        if not query_id:
            issues.append(
                Issue(query_id="", issue="missing_query_id", detail="query_id is blank")
            )
        elif not query_id_pattern.match(query_id):
            issues.append(
                Issue(
                    query_id=query_id,
                    issue="invalid_query_id_format",
                    detail=f"query_id should match {query_id_prefix}<digits> (e.g. {query_id_prefix}001)",
                )
            )

        should_answer = normalize_bool(row.get("should_answer"))
        if should_answer is None:
            issues.append(
                Issue(
                    query_id=query_id,
                    issue="invalid_should_answer",
                    detail=f"should_answer is invalid: {row.get('should_answer')}",
                )
            )

        golden_answer = cell_text(row.get("golden_answer", ""))
        source_text = cell_text(row.get("source_text", ""))
        relevant_doc_ids = cell_text(row.get("relevant_doc_ids", ""))
        evidence_locations = cell_text(row.get("evidence_locations", ""))
        query_text = cell_text(row.get("query_text", ""))

        if should_answer is True:
            for field_name, field_value in {
                "golden_answer": golden_answer,
                "source_text": source_text,
                "relevant_doc_ids": relevant_doc_ids,
                "evidence_locations": evidence_locations,
            }.items():
                if is_blank(field_value):
                    issues.append(
                        Issue(
                            query_id=query_id,
                            issue="missing_required_field",
                            detail=f"{field_name} is blank",
                        )
                    )

            if source_text and not has_quotes(source_text):
                issues.append(
                    Issue(
                        query_id=query_id,
                        issue="source_text_missing_quotes",
                        detail="source_text should include quoted passages",
                    )
                )

            if require_reviewers and not has_two_reviewer_initials(
                row.get("Reviewers")
            ):
                issues.append(
                    Issue(
                        query_id=query_id,
                        issue="missing_or_invalid_reviewers",
                        detail="Reviewers should contain at least two initials (e.g. AB/CD)",
                    )
                )

            if relevant_doc_ids and evidence_locations:
                doc_ids = split_semicolon(relevant_doc_ids)
                evidence = split_semicolon(evidence_locations)
                normalized_doc_ids = [
                    normalize_doc_id(doc_id) for doc_id in doc_ids if doc_id
                ]
                normalized_doc_set = {doc_id for doc_id in normalized_doc_ids if doc_id}
                multi_doc = len(normalized_doc_set) > 1

                for ev in evidence:
                    ev_text = str(ev).strip()
                    page_match = re.search(r"(?i)(p\.|pg\.|page)\s*([0-9]+)", ev_text)
                    if not page_match:
                        issues.append(
                            Issue(
                                query_id=query_id,
                                issue="evidence_missing_page",
                                detail=f"evidence location missing page marker: {ev_text}",
                            )
                        )
                        continue

                    doc_match = re.search(
                        r"(?i)^(.+):\s*(p\.|pg\.|page)\s*([0-9]+)\s*$", ev_text
                    )
                    if doc_match:
                        evidence_doc_id = normalize_doc_id(doc_match.group(1))
                        if (
                            normalized_doc_set
                            and evidence_doc_id not in normalized_doc_set
                        ):
                            issues.append(
                                Issue(
                                    query_id=query_id,
                                    issue="evidence_doc_mismatch",
                                    detail=f"evidence '{ev_text}' does not match relevant_doc_ids",
                                )
                            )
                    elif multi_doc:
                        issues.append(
                            Issue(
                                query_id=query_id,
                                issue="evidence_doc_missing",
                                detail=f"evidence should include doc id for multi-doc rows: {ev_text}",
                            )
                        )

            if golden_answer:
                numeric_values = parse_numbers(golden_answer)
                if numeric_values and "%" not in golden_answer:
                    if any(
                        0 < value < 1 for value in numeric_values
                    ) and PERCENT_KEYWORDS.search(query_text):
                        issues.append(
                            Issue(
                                query_id=query_id,
                                issue="golden_answer_percent_format",
                                detail="golden_answer looks like a fraction; use percent like 7.9%",
                            )
                        )

        if should_answer is False:
            for field_name, field_value in {
                "golden_answer": golden_answer,
                "source_text": source_text,
                "relevant_doc_ids": relevant_doc_ids,
                "evidence_locations": evidence_locations,
            }.items():
                if not is_blank(field_value):
                    issues.append(
                        Issue(
                            query_id=query_id,
                            issue="unexpected_field_for_refusal",
                            detail=f"{field_name} should be blank",
                        )
                    )

    return issues


def evaluate(
    df: pd.DataFrame,
    base_url: str,
    content_type: str,
    api_mode: str,
    timeout: float,
    max_rows: Optional[int],
    sleep_seconds: float,
    refusal_phrases: list[str],
    similarity_threshold: float,
    abs_tol: float,
    rel_tol: float,
    retrieval_k: int,
    compute_retrieval: bool,
    semantic_model: Optional[SemanticSimilarityEvaluator],
    f1_threshold: float,
    semantic_threshold: float,
    skip_rows: int,
    request_api_debug: bool,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []

    if skip_rows:
        df = df.iloc[skip_rows:]
    if max_rows:
        df = df.head(max_rows)

    for _, row in df.iterrows():
        query_id = cell_text(row.get("query_id", ""))
        query_text = cell_text(row.get("query_text", ""))
        golden_answer = cell_text(row.get("golden_answer", ""))
        relevant_doc_ids_raw = cell_text(row.get("relevant_doc_ids", ""))
        evidence_locations_raw = cell_text(row.get("evidence_locations", ""))
        should_answer = normalize_bool(row.get("should_answer"))
        relevant_doc_ids = (
            split_semicolon(relevant_doc_ids_raw) if relevant_doc_ids_raw else []
        )
        evidence_locations = (
            split_semicolon(evidence_locations_raw) if evidence_locations_raw else []
        )
        evidence_pages = parse_evidence_pages(relevant_doc_ids, evidence_locations)
        scoring_method: Optional[str] = None

        precision_at_k: Optional[float] = None
        recall_at_k: Optional[float] = None
        mrr: Optional[float] = None
        ndcg: Optional[float] = None
        api_mode_used: Optional[str] = None
        reference_count: Optional[int] = None
        retrieved_doc_ids: Optional[str] = None
        reference_url: Optional[str] = None
        reference_doc_id: Optional[str] = None
        reference_page: Optional[int] = None
        reference_doc_ids_all: Optional[str] = None
        reference_pages_all: Optional[str] = None
        reference_doc_match: Optional[bool] = None
        any_reference_doc_match: Optional[bool] = None
        evidence_page_match: Optional[bool] = None
        any_reference_page_match: Optional[bool] = None
        doc_hit_at_1: Optional[bool] = None
        doc_hit_at_k: Optional[bool] = None
        retrieval_metric_source: Optional[str] = None
        predicted_relevant_doc_ids: Optional[str] = None
        predicted_evidence_locations: Optional[str] = None
        predicted_source_text: Optional[str] = None
        model_answered: Optional[bool] = None
        correct_refusal: Optional[bool] = None
        false_answer: Optional[bool] = None
        answered_when_expected: Optional[bool] = None
        answer_missing: Optional[bool] = None
        reasoning: Optional[str] = None
        context_texts: Optional[str] = None
        reference_scores: Optional[str] = None
        reference_titles: Optional[str] = None
        highlighting: Optional[str] = None
        context_from: Optional[str] = None
        context_reference: Optional[str] = None
        relevant_publications: Optional[str] = None
        pipeline_doc_hit_at_1: Optional[bool] = None
        pipeline_doc_hit_at_k: Optional[bool] = None
        pipeline_precision_at_k: Optional[float] = None
        pipeline_recall_at_k: Optional[float] = None
        pipeline_mrr: Optional[float] = None
        pipeline_ndcg: Optional[float] = None
        pipeline_page_precision_at_k: Optional[float] = None
        pipeline_page_recall_at_k: Optional[float] = None
        pipeline_page_mrr: Optional[float] = None
        pipeline_page_ndcg: Optional[float] = None

        if not query_text:
            results.append(
                EvaluationResult(
                    query_id=query_id,
                    query_text=query_text,
                    should_answer=should_answer,
                    golden_answer=golden_answer,
                    predicted_answer="",
                    predicted_relevant_doc_ids=None,
                    predicted_evidence_locations=None,
                    predicted_source_text=None,
                    model_answered=None,
                    correct_refusal=None,
                    false_answer=None,
                    answered_when_expected=None,
                    answer_missing=None,
                    api_mode=None,
                    reference_count=None,
                    reference_url=None,
                    reference_doc_id=None,
                    reference_page=None,
                    reference_doc_ids_all=None,
                    reference_pages_all=None,
                    reference_doc_match=None,
                    any_reference_doc_match=None,
                    evidence_page_match=None,
                    any_reference_page_match=None,
                    doc_hit_at_1=None,
                    doc_hit_at_k=None,
                    exact_match=None,
                    token_f1=None,
                    semantic_similarity=None,
                    is_refusal=False,
                    is_correct=None,
                    similarity_score=None,
                    precision_at_k=None,
                    recall_at_k=None,
                    mrr=None,
                    ndcg=None,
                    retrieval_metric_source=None,
                    retrieved_doc_ids=None,
                    error="missing query_text",
                    reasoning=None,
                    context_texts=None,
                    reference_scores=None,
                    reference_titles=None,
                    highlighting=None,
                    context_from=None,
                    context_reference=None,
                    relevant_publications=None,
                )
            )
            continue

        try:
            response = requests.get(
                f"{base_url}/search",
                params={
                    "q": query_text,
                    "content_type": content_type,
                    "debug": "true" if request_api_debug else "false",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            predicted = cell_text(payload.get("answer", ""))
            predicted_source_text = cell_text(payload.get("context_reference", ""))
            detected_api_mode = detect_api_mode(payload)
            api_mode_used = detected_api_mode if api_mode == "auto" else api_mode
            (
                reference_url,
                reference_doc_id,
                reference_page,
                reference_count,
                reference_urls,
            ) = extract_reference_details(payload)
            debug_details = extract_debug_details(payload)
            reasoning = debug_details["reasoning"]
            context_texts = debug_details["context_texts"]
            reference_scores = debug_details["reference_scores"]
            reference_titles = debug_details["reference_titles"]
            highlighting = debug_details["highlighting"]
            context_from = debug_details["context_from"]
            context_reference = debug_details["context_reference"]
            relevant_publications = debug_details["relevant_publications"]
            if not predicted_source_text:
                predicted_source_text = context_reference or primary_context_text(
                    context_texts
                )
            all_reference_doc_ids: list[str] = []
            all_reference_pages: list[int] = []
            reference_pairs: list[tuple[str, int]] = []
            for ref_url in reference_urls:
                parsed_ref = urlparse(ref_url)
                doc_id = normalize_doc_id(Path(parsed_ref.path).name)
                if doc_id:
                    all_reference_doc_ids.append(doc_id)
                page = extract_page_from_url(ref_url)
                if page is not None:
                    all_reference_pages.append(page)
                if doc_id and page is not None:
                    reference_pairs.append((doc_id, page))

            all_reference_doc_ids = unique_preserve_order(all_reference_doc_ids)
            all_reference_pages_text = unique_preserve_order(
                [str(page) for page in all_reference_pages]
            )
            if all_reference_doc_ids:
                reference_doc_ids_all = ";".join(all_reference_doc_ids)
            if all_reference_pages_text:
                reference_pages_all = ";".join(all_reference_pages_text)

            if reference_pairs:
                predicted_evidence_locations = ";".join(
                    f"{doc_id}:p.{page}" for doc_id, page in reference_pairs
                )
            elif reference_page is not None:
                if reference_doc_id is not None:
                    predicted_evidence_locations = (
                        f"{reference_doc_id}:p.{reference_page}"
                    )
                else:
                    predicted_evidence_locations = f"p.{reference_page}"

            gold_doc_ids = {
                normalize_doc_id(doc_id)
                for doc_id in relevant_doc_ids
                if doc_id.strip()
            }
            if relevant_doc_ids:
                reference_doc_match = (
                    reference_doc_id in gold_doc_ids
                    if reference_doc_id is not None
                    else False
                )
                any_reference_doc_match = any(
                    doc_id in gold_doc_ids for doc_id in all_reference_doc_ids
                )
            if evidence_pages:
                if reference_page is not None and reference_doc_id is not None:
                    pages = evidence_pages.get(reference_doc_id, set())
                    evidence_page_match = reference_page in pages if pages else False
                else:
                    evidence_page_match = False
                any_reference_page_match = any(
                    page in evidence_pages.get(doc_id, set())
                    for doc_id, page in reference_pairs
                )

            pipeline_metrics = compute_pipeline_reference_metrics(
                relevant_doc_ids=relevant_doc_ids,
                evidence_pages=evidence_pages,
                reference_doc_ids=all_reference_doc_ids,
                reference_pairs=reference_pairs,
                k=retrieval_k,
            )
            pipeline_doc_hit_at_1 = pipeline_metrics["pipeline_doc_hit_at_1"]  # type: ignore[assignment]
            pipeline_doc_hit_at_k = pipeline_metrics["pipeline_doc_hit_at_k"]  # type: ignore[assignment]
            pipeline_precision_at_k = pipeline_metrics["pipeline_precision_at_k"]  # type: ignore[assignment]
            pipeline_recall_at_k = pipeline_metrics["pipeline_recall_at_k"]  # type: ignore[assignment]
            pipeline_mrr = pipeline_metrics["pipeline_mrr"]  # type: ignore[assignment]
            pipeline_ndcg = pipeline_metrics["pipeline_ndcg"]  # type: ignore[assignment]
            pipeline_page_precision_at_k = pipeline_metrics[
                "pipeline_page_precision_at_k"
            ]  # type: ignore[assignment]
            pipeline_page_recall_at_k = pipeline_metrics[
                "pipeline_page_recall_at_k"
            ]  # type: ignore[assignment]
            pipeline_page_mrr = pipeline_metrics["pipeline_page_mrr"]  # type: ignore[assignment]
            pipeline_page_ndcg = pipeline_metrics["pipeline_page_ndcg"]  # type: ignore[assignment]
        except Exception as exc:  # noqa: BLE001
            results.append(
                EvaluationResult(
                    query_id=query_id,
                    query_text=query_text,
                    should_answer=should_answer,
                    golden_answer=golden_answer,
                    predicted_answer="",
                    predicted_relevant_doc_ids=predicted_relevant_doc_ids,
                    predicted_evidence_locations=predicted_evidence_locations,
                    predicted_source_text=predicted_source_text,
                    model_answered=model_answered,
                    correct_refusal=correct_refusal,
                    false_answer=false_answer,
                    answered_when_expected=answered_when_expected,
                    answer_missing=answer_missing,
                    api_mode=api_mode_used,
                    reference_count=reference_count,
                    reference_url=reference_url,
                    reference_doc_id=reference_doc_id,
                    reference_page=reference_page,
                    reference_doc_ids_all=reference_doc_ids_all,
                    reference_pages_all=reference_pages_all,
                    reference_doc_match=reference_doc_match,
                    any_reference_doc_match=any_reference_doc_match,
                    evidence_page_match=evidence_page_match,
                    any_reference_page_match=any_reference_page_match,
                    doc_hit_at_1=doc_hit_at_1,
                    doc_hit_at_k=doc_hit_at_k,
                    exact_match=None,
                    token_f1=None,
                    semantic_similarity=None,
                    is_refusal=False,
                    is_correct=None,
                    similarity_score=None,
                    precision_at_k=precision_at_k,
                    recall_at_k=recall_at_k,
                    mrr=mrr,
                    ndcg=ndcg,
                    retrieval_metric_source=retrieval_metric_source,
                    retrieved_doc_ids=retrieved_doc_ids,
                    error=str(exc),
                    reasoning=reasoning,
                    context_texts=context_texts,
                    reference_scores=reference_scores,
                    reference_titles=reference_titles,
                    highlighting=highlighting,
                    context_from=context_from,
                    context_reference=context_reference,
                    relevant_publications=relevant_publications,
                    scoring_method=None,
                    pipeline_doc_hit_at_1=pipeline_doc_hit_at_1,
                    pipeline_doc_hit_at_k=pipeline_doc_hit_at_k,
                    pipeline_precision_at_k=pipeline_precision_at_k,
                    pipeline_recall_at_k=pipeline_recall_at_k,
                    pipeline_mrr=pipeline_mrr,
                    pipeline_ndcg=pipeline_ndcg,
                    pipeline_page_precision_at_k=pipeline_page_precision_at_k,
                    pipeline_page_recall_at_k=pipeline_page_recall_at_k,
                    pipeline_page_mrr=pipeline_page_mrr,
                    pipeline_page_ndcg=pipeline_page_ndcg,
                )
            )
            continue

        if api_mode != "auto" and detected_api_mode not in {api_mode, "unknown"}:
            error = (
                f"API mode mismatch: requested '{api_mode}' but response looked like "
                f"'{detected_api_mode}'"
            )
        else:
            error = None

        if (
            compute_retrieval
            and relevant_doc_ids
            and api_mode_used in {"local", "cloud"}
        ):
            retrieval_metric_source = "local_similarity_search_proxy"
            try:
                top_matches = similarity_search(
                    query_text,
                    latest_filter=(content_type == "latest"),
                    return_dicts=True,
                )
                retrieved_raw = [extract_doc_id(doc) for doc in top_matches]
                retrieved_doc_ids = ";".join(retrieved_raw)
                predicted_relevant_doc_ids = retrieved_doc_ids
                precision_at_k, recall_at_k, mrr, ndcg = compute_retrieval_metrics(
                    relevant_doc_ids=relevant_doc_ids,
                    retrieved_doc_ids=retrieved_raw,
                    k=retrieval_k,
                )
                doc_hit_at_1, doc_hit_at_k = compute_doc_hit_flags(
                    relevant_doc_ids=relevant_doc_ids,
                    retrieved_doc_ids=retrieved_raw,
                    k=retrieval_k,
                )
            except Exception as exc:  # noqa: BLE001
                precision_at_k = None
                recall_at_k = None
                mrr = None
                ndcg = None
                doc_hit_at_1 = None
                doc_hit_at_k = None
                retrieved_doc_ids = None
                retrieval_metric_source = "local_similarity_search_proxy_failed"
                error = str(exc) if error is None else f"{error}; {exc}"
        elif compute_retrieval and relevant_doc_ids:
            retrieval_metric_source = "disabled_non_local_api"
        elif compute_retrieval:
            retrieval_metric_source = "disabled_no_relevant_doc_ids"
        else:
            retrieval_metric_source = "disabled_by_flag"

        refusal = is_refusal_answer(predicted, refusal_phrases) or (
            should_answer is False and not predicted
        )
        model_answered = bool(predicted) and not refusal
        similarity_score: Optional[float] = None
        is_correct: Optional[bool] = None
        exact_match: Optional[int] = None
        token_f1: Optional[float] = None
        semantic_similarity: Optional[float] = None
        numeric_correct = False
        golden_has_numbers = False

        if should_answer is True:
            exact_match = exact_match_score(golden_answer, predicted)
            token_f1 = token_f1_score(golden_answer, predicted)
            if semantic_model is not None:
                try:
                    semantic_similarity = semantic_model.similarity(
                        golden_answer, predicted
                    )
                except Exception:
                    semantic_similarity = None

            if refusal:
                is_correct = False
            else:
                numeric_correct = numeric_match(
                    golden_answer, predicted, abs_tol=abs_tol, rel_tol=rel_tol
                )
                similarity_score = text_match(golden_answer, predicted)
                passes_f1 = token_f1 >= f1_threshold if token_f1 is not None else False
                passes_semantic = (
                    semantic_similarity >= semantic_threshold
                    if semantic_similarity is not None
                    else False
                )

                # When the golden answer is primarily numeric, only trust
                # exact match or numeric_match — fuzzy text and semantic
                # similarity can produce false positives for numbers that
                # look textually similar but are factually wrong.
                golden_has_numbers = bool(parse_scaled_numbers(golden_answer))
                if golden_has_numbers:
                    is_correct = exact_match == 1 or numeric_correct
                else:
                    is_correct = (
                        exact_match == 1
                        or numeric_correct
                        or similarity_score >= similarity_threshold
                        or passes_f1
                        or passes_semantic
                    )
            scoring_method = determine_scoring_method(
                should_answer=should_answer,
                refusal=refusal,
                exact_match=exact_match,
                numeric_correct=numeric_correct,
                golden_has_numbers=golden_has_numbers,
                similarity_score=similarity_score,
                similarity_threshold=similarity_threshold,
                token_f1=token_f1,
                f1_threshold=f1_threshold,
                semantic_similarity=semantic_similarity,
                semantic_threshold=semantic_threshold,
            )
            answered_when_expected = model_answered
            answer_missing = not model_answered
        elif should_answer is False:
            is_correct = refusal
            correct_refusal = refusal
            false_answer = not refusal
            scoring_method = determine_scoring_method(
                should_answer=should_answer,
                refusal=refusal,
                exact_match=None,
                numeric_correct=False,
                golden_has_numbers=False,
                similarity_score=None,
                similarity_threshold=similarity_threshold,
                token_f1=None,
                f1_threshold=f1_threshold,
                semantic_similarity=None,
                semantic_threshold=semantic_threshold,
            )

        results.append(
            EvaluationResult(
                query_id=query_id,
                query_text=query_text,
                should_answer=should_answer,
                golden_answer=golden_answer,
                predicted_answer=predicted,
                predicted_relevant_doc_ids=predicted_relevant_doc_ids,
                predicted_evidence_locations=predicted_evidence_locations,
                predicted_source_text=predicted_source_text,
                model_answered=model_answered,
                correct_refusal=correct_refusal,
                false_answer=false_answer,
                answered_when_expected=answered_when_expected,
                answer_missing=answer_missing,
                api_mode=api_mode_used,
                reference_count=reference_count,
                reference_url=reference_url,
                reference_doc_id=reference_doc_id,
                reference_page=reference_page,
                reference_doc_ids_all=reference_doc_ids_all,
                reference_pages_all=reference_pages_all,
                reference_doc_match=reference_doc_match,
                any_reference_doc_match=any_reference_doc_match,
                evidence_page_match=evidence_page_match,
                any_reference_page_match=any_reference_page_match,
                doc_hit_at_1=doc_hit_at_1,
                doc_hit_at_k=doc_hit_at_k,
                exact_match=exact_match,
                token_f1=token_f1,
                semantic_similarity=semantic_similarity,
                is_refusal=refusal,
                is_correct=is_correct,
                similarity_score=similarity_score,
                precision_at_k=precision_at_k,
                recall_at_k=recall_at_k,
                mrr=mrr,
                ndcg=ndcg,
                retrieval_metric_source=retrieval_metric_source,
                retrieved_doc_ids=retrieved_doc_ids,
                error=error,
                reasoning=reasoning,
                context_texts=context_texts,
                reference_scores=reference_scores,
                reference_titles=reference_titles,
                highlighting=highlighting,
                context_from=context_from,
                context_reference=context_reference,
                relevant_publications=relevant_publications,
                scoring_method=scoring_method,
                pipeline_doc_hit_at_1=pipeline_doc_hit_at_1,
                pipeline_doc_hit_at_k=pipeline_doc_hit_at_k,
                pipeline_precision_at_k=pipeline_precision_at_k,
                pipeline_recall_at_k=pipeline_recall_at_k,
                pipeline_mrr=pipeline_mrr,
                pipeline_ndcg=pipeline_ndcg,
                pipeline_page_precision_at_k=pipeline_page_precision_at_k,
                pipeline_page_recall_at_k=pipeline_page_recall_at_k,
                pipeline_page_mrr=pipeline_page_mrr,
                pipeline_page_ndcg=pipeline_page_ndcg,
            )
        )

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return results


def build_summary_from_dataframe(
    results_df: pd.DataFrame, retrieval_k: int
) -> dict[str, object]:
    df = results_df.copy()
    for column in [
        "should_answer",
        "is_correct",
        "correct_refusal",
        "false_answer",
        "answered_when_expected",
        "answer_missing",
        "reference_doc_match",
        "any_reference_doc_match",
        "evidence_page_match",
        "any_reference_page_match",
        "faiss_proxy_doc_hit_at_1",
        "faiss_proxy_doc_hit_at_k",
        "pipeline_doc_hit_at_1",
        "pipeline_doc_hit_at_k",
    ]:
        if column in df.columns:
            df[column] = df[column].apply(normalize_bool)

    for column in [
        "exact_match",
        "token_f1",
        "semantic_similarity",
        "faiss_proxy_precision_at_k",
        "faiss_proxy_recall_at_k",
        "faiss_proxy_mrr",
        "faiss_proxy_ndcg",
        "pipeline_precision_at_k",
        "pipeline_recall_at_k",
        "pipeline_mrr",
        "pipeline_ndcg",
        "pipeline_page_precision_at_k",
        "pipeline_page_recall_at_k",
        "pipeline_page_mrr",
        "pipeline_page_ndcg",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    evaluated = df[df["is_correct"].notna()].copy()
    total = len(evaluated)
    answerable = evaluated[
        evaluated["should_answer"].map(lambda value: value is True)
    ].copy()
    unanswerable = evaluated[
        evaluated["should_answer"].map(lambda value: value is False)
    ].copy()

    answerable_correct = int(answerable["is_correct"].fillna(False).sum())
    unanswerable_correct = int(unanswerable["is_correct"].fillna(False).sum())
    overall_correct = answerable_correct + unanswerable_correct
    overall_accuracy = overall_correct / total if total else 0.0
    answerable_accuracy = (
        answerable_correct / len(answerable) if len(answerable) else 0.0
    )
    unanswerable_accuracy = (
        unanswerable_correct / len(unanswerable) if len(unanswerable) else 0.0
    )

    summary: dict[str, object] = {
        "retrieval_k": retrieval_k,
        "total_evaluated": total,
        "answerable_count": len(answerable),
        "unanswerable_count": len(unanswerable),
        "answerable_accuracy": answerable_accuracy,
        "unanswerable_accuracy": unanswerable_accuracy,
        "overall_accuracy": overall_accuracy,
    }

    if "api_mode" in df.columns:
        api_modes = sorted({str(v) for v in df["api_mode"].dropna() if str(v).strip()})
        if api_modes:
            summary["api_modes_observed"] = ";".join(api_modes)

    for column, summary_key in [
        ("exact_match", "exact_match_avg"),
        ("token_f1", "token_f1_avg"),
        ("semantic_similarity", "semantic_similarity_avg"),
    ]:
        if column in answerable.columns:
            values = answerable[column].dropna()
            if not values.empty:
                summary[summary_key] = float(values.mean())

    for prefix in ("faiss_proxy", "pipeline", "pipeline_page"):
        precision_col = f"{prefix}_precision_at_k"
        recall_col = f"{prefix}_recall_at_k"
        mrr_col = f"{prefix}_mrr"
        ndcg_col = f"{prefix}_ndcg"
        if precision_col in evaluated.columns and recall_col in evaluated.columns:
            metric_rows = evaluated[
                evaluated[precision_col].notna() & evaluated[recall_col].notna()
            ]
            if not metric_rows.empty:
                summary[f"{prefix}_precision_at_k_avg"] = float(
                    metric_rows[precision_col].mean()
                )
                summary[f"{prefix}_recall_at_k_avg"] = float(
                    metric_rows[recall_col].mean()
                )
                if mrr_col in metric_rows.columns:
                    summary[f"{prefix}_mrr_avg"] = float(
                        metric_rows[mrr_col].dropna().mean()
                    )
                if ndcg_col in metric_rows.columns:
                    summary[f"{prefix}_ndcg_avg"] = float(
                        metric_rows[ndcg_col].dropna().mean()
                    )

    if "faiss_proxy_metric_source" in df.columns:
        retrieval_sources = sorted(
            {str(v) for v in df["faiss_proxy_metric_source"].dropna() if str(v).strip()}
        )
        if retrieval_sources:
            summary["faiss_proxy_metric_sources"] = ";".join(retrieval_sources)

    for prefix in ("faiss_proxy", "pipeline"):
        hit_k_col = f"{prefix}_doc_hit_at_k"
        hit_1_col = f"{prefix}_doc_hit_at_1"
        if hit_k_col in evaluated.columns:
            doc_hit_rows = evaluated[evaluated[hit_k_col].notna()]
            if not doc_hit_rows.empty:
                hit_1_count = int(doc_hit_rows[hit_1_col].fillna(False).sum())
                hit_k_count = int(doc_hit_rows[hit_k_col].fillna(False).sum())
                summary[f"{prefix}_doc_hit_at_1_rate"] = hit_1_count / len(doc_hit_rows)
                summary[f"{prefix}_doc_hit_at_1_count"] = hit_1_count
                summary[f"{prefix}_doc_hit_at_1_denom"] = len(doc_hit_rows)
                summary[f"{prefix}_doc_hit_at_k_rate"] = hit_k_count / len(doc_hit_rows)
                summary[f"{prefix}_doc_hit_at_k_count"] = hit_k_count
                summary[f"{prefix}_doc_hit_at_k_denom"] = len(doc_hit_rows)

    for column_prefix, summary_prefix in [
        ("reference_doc_match", "first_reference_doc_match"),
        ("any_reference_doc_match", "any_reference_doc_match"),
        ("evidence_page_match", "first_reference_page_hit"),
        ("any_reference_page_match", "any_reference_page_hit"),
    ]:
        if column_prefix in evaluated.columns:
            rows = evaluated[evaluated[column_prefix].notna()]
            if not rows.empty:
                count = int(rows[column_prefix].fillna(False).sum())
                summary[f"{summary_prefix}_rate"] = count / len(rows)
                summary[f"{summary_prefix}_count"] = count
                summary[f"{summary_prefix}_denom"] = len(rows)

    if not unanswerable.empty:
        correct_refusal_count = int(unanswerable["correct_refusal"].fillna(False).sum())
        false_answer_count = int(unanswerable["false_answer"].fillna(False).sum())
        summary["correct_refusal_rate"] = correct_refusal_count / len(unanswerable)
        summary["correct_refusal_count"] = correct_refusal_count
        summary["correct_refusal_denom"] = len(unanswerable)
        summary["false_answer_rate"] = false_answer_count / len(unanswerable)
        summary["false_answer_count"] = false_answer_count
        summary["false_answer_denom"] = len(unanswerable)

    if not answerable.empty:
        answered_when_expected_count = int(
            answerable["answered_when_expected"].fillna(False).sum()
        )
        answer_missing_count = int(answerable["answer_missing"].fillna(False).sum())
        summary["answer_coverage"] = answered_when_expected_count / len(answerable)
        summary["answer_coverage_count"] = answered_when_expected_count
        summary["answer_coverage_denom"] = len(answerable)
        summary["answer_missing_rate"] = answer_missing_count / len(answerable)
        summary["answer_missing_count"] = answer_missing_count
        summary["answer_missing_denom"] = len(answerable)

    correct_refusal_count = (
        int(unanswerable["correct_refusal"].fillna(False).sum())
        if "correct_refusal" in unanswerable.columns
        else 0
    )
    summary["safe_response_rate"] = (
        (answerable_correct + correct_refusal_count) / total if total else 0.0
    )
    summary["error_count"] = (
        int(df["error"].notna().sum()) if "error" in df.columns else 0
    )
    return summary


def build_summary(
    results: list[EvaluationResult], retrieval_k: int
) -> dict[str, object]:
    return build_summary_from_dataframe(results_to_dataframe(results), retrieval_k)


def print_summary(summary: dict[str, object], retrieval_k: int) -> None:
    print("\nAccuracy summary")
    print(f"Retrieval k: {retrieval_k}")
    print(f"Total evaluated: {summary['total_evaluated']}")
    print(f"Answerable: {summary['answerable_count']}")
    print(f"Unanswerable: {summary['unanswerable_count']}")
    print(f"Answerable accuracy: {summary['answerable_accuracy']:.3f}")
    print(f"Unanswerable accuracy: {summary['unanswerable_accuracy']:.3f}")
    print(f"Overall accuracy: {summary['overall_accuracy']:.3f}")

    api_modes = summary.get("api_modes_observed")
    if api_modes:
        print(f"API mode(s) observed: {str(api_modes).replace(';', ', ')}")

    if summary.get("exact_match_avg") is not None:
        print(f"Exact Match (EM): {summary['exact_match_avg']:.3f}")
    if summary.get("token_f1_avg") is not None:
        print(f"Token F1 (avg): {summary['token_f1_avg']:.3f}")
    if summary.get("semantic_similarity_avg") is not None:
        print(f"Semantic Similarity (avg): {summary['semantic_similarity_avg']:.3f}")

    if summary.get("pipeline_precision_at_k_avg") is not None:
        print(
            f"Pipeline Precision@k (avg): {summary['pipeline_precision_at_k_avg']:.3f}"
        )
        print(f"Pipeline Recall@k (avg): {summary['pipeline_recall_at_k_avg']:.3f}")
        print(f"Pipeline MRR (avg): {summary['pipeline_mrr_avg']:.3f}")
        print(f"Pipeline nDCG (avg): {summary['pipeline_ndcg_avg']:.3f}")

    if summary.get("pipeline_doc_hit_at_1_rate") is not None:
        print(
            f"Pipeline Doc Hit@1: {summary['pipeline_doc_hit_at_1_rate']:.3f} "
            f"({summary['pipeline_doc_hit_at_1_count']}/"
            f"{summary['pipeline_doc_hit_at_1_denom']})"
        )
        print(
            f"Pipeline Doc Hit@{retrieval_k}: "
            f"{summary['pipeline_doc_hit_at_k_rate']:.3f} "
            f"({summary['pipeline_doc_hit_at_k_count']}/"
            f"{summary['pipeline_doc_hit_at_k_denom']})"
        )

    if summary.get("pipeline_page_precision_at_k_avg") is not None:
        print(
            f"Pipeline Page Precision@k (avg): "
            f"{summary['pipeline_page_precision_at_k_avg']:.3f}"
        )
        print(
            f"Pipeline Page Recall@k (avg): "
            f"{summary['pipeline_page_recall_at_k_avg']:.3f}"
        )
        print(f"Pipeline Page MRR (avg): {summary['pipeline_page_mrr_avg']:.3f}")
        print(f"Pipeline Page nDCG (avg): {summary['pipeline_page_ndcg_avg']:.3f}")
    faiss_sources = summary.get("faiss_proxy_metric_sources")
    if faiss_sources:
        print(f"FAISS proxy source(s): {str(faiss_sources).replace(';', ', ')}")

    if summary.get("faiss_proxy_precision_at_k_avg") is not None:
        print(
            f"FAISS Proxy Precision@k (avg): "
            f"{summary['faiss_proxy_precision_at_k_avg']:.3f}"
        )
        print(
            f"FAISS Proxy Recall@k (avg): "
            f"{summary['faiss_proxy_recall_at_k_avg']:.3f}"
        )
        print(f"FAISS Proxy MRR (avg): {summary['faiss_proxy_mrr_avg']:.3f}")
        print(f"FAISS Proxy nDCG (avg): {summary['faiss_proxy_ndcg_avg']:.3f}")

    if summary.get("faiss_proxy_doc_hit_at_1_rate") is not None:
        print(
            f"FAISS Proxy Doc Hit@1: {summary['faiss_proxy_doc_hit_at_1_rate']:.3f} "
            f"({summary['faiss_proxy_doc_hit_at_1_count']}/"
            f"{summary['faiss_proxy_doc_hit_at_1_denom']})"
        )
        print(
            f"FAISS Proxy Doc Hit@{retrieval_k}: "
            f"{summary['faiss_proxy_doc_hit_at_k_rate']:.3f} "
            f"({summary['faiss_proxy_doc_hit_at_k_count']}/"
            f"{summary['faiss_proxy_doc_hit_at_k_denom']})"
        )

    if summary.get("first_reference_doc_match_rate") is not None:
        print(
            f"First Reference Doc Match: "
            f"{summary['first_reference_doc_match_rate']:.3f} "
            f"({summary['first_reference_doc_match_count']}/"
            f"{summary['first_reference_doc_match_denom']})"
        )

    if summary.get("any_reference_doc_match_rate") is not None:
        print(
            f"Any Reference Doc Match: "
            f"{summary['any_reference_doc_match_rate']:.3f} "
            f"({summary['any_reference_doc_match_count']}/"
            f"{summary['any_reference_doc_match_denom']})"
        )

    if summary.get("first_reference_page_hit_rate") is not None:
        print(
            f"First Reference Page Hit: "
            f"{summary['first_reference_page_hit_rate']:.3f} "
            f"({summary['first_reference_page_hit_count']}/"
            f"{summary['first_reference_page_hit_denom']})"
        )

    if summary.get("any_reference_page_hit_rate") is not None:
        print(
            f"Any Reference Page Hit: "
            f"{summary['any_reference_page_hit_rate']:.3f} "
            f"({summary['any_reference_page_hit_count']}/"
            f"{summary['any_reference_page_hit_denom']})"
        )

    if summary.get("correct_refusal_rate") is not None:
        print(
            f"Correct Refusal Rate: {summary['correct_refusal_rate']:.3f} "
            f"({summary['correct_refusal_count']}/{summary['correct_refusal_denom']})"
        )
        print(
            f"False Answer Rate: {summary['false_answer_rate']:.3f} "
            f"({summary['false_answer_count']}/{summary['false_answer_denom']})"
        )

    if summary.get("answer_coverage") is not None:
        print(
            f"Answer Coverage: {summary['answer_coverage']:.3f} "
            f"({summary['answer_coverage_count']}/{summary['answer_coverage_denom']})"
        )
        print(
            f"Answer Missing Rate: {summary['answer_missing_rate']:.3f} "
            f"({summary['answer_missing_count']}/{summary['answer_missing_denom']})"
        )

    print(f"Safe response rate: {summary['safe_response_rate']:.3f}")

    if summary.get("error_count"):
        print(f"\nErrors: {summary['error_count']} (see output file for details)")


def save_issues(issues: list[Issue], output_path: Path) -> None:
    if not issues:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([issue.__dict__ for issue in issues])
    df.to_csv(output_path, index=False)


def save_results(results: list[EvaluationResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = results_to_dataframe(results)
    df.to_csv(output_path, index=False)


def save_summary(summary: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(output_path, index=False)


def save_results_excel(
    source_excel: Path,
    qa_sheet_name: str,
    workbook_sheet_names: list[str],
    results: list[EvaluationResult],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    qa_df = pd.read_excel(source_excel, sheet_name=qa_sheet_name)
    qa_df = qa_df.rename(columns=lambda c: str(c).strip())
    results_df = results_to_dataframe(results)
    merged = qa_df.merge(results_df, on=["query_id", "query_text"], how="left")

    predicted_answers_df = merged[
        [
            "query_id",
            "query_text",
            "api_mode",
            "predicted_answer",
            "predicted_relevant_doc_ids",
            "predicted_evidence_locations",
            "predicted_source_text",
            "reference_url",
            "reference_doc_id",
            "reference_doc_ids_all",
            "reference_page",
            "reference_pages_all",
            "reference_titles",
            "context_from",
            "context_reference",
            "relevant_publications",
            "reasoning",
            "scoring_method",
        ]
    ].copy()

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        qa_df.to_excel(writer, sheet_name=qa_sheet_name, index=False)
        predicted_answers_df.to_excel(
            writer, sheet_name="Predicted_Answers", index=False
        )
        for sheet in workbook_sheet_names:
            if sheet == qa_sheet_name:
                continue
            try:
                df_sheet = pd.read_excel(source_excel, sheet_name=sheet, header=None)
                df_sheet.to_excel(writer, sheet_name=sheet, header=False, index=False)
            except ValueError:
                continue


def determine_effective_api_mode(
    requested_api_mode: str, results: list[EvaluationResult]
) -> str:
    """Choose a stable label for run-artifact directories."""
    if requested_api_mode != "auto":
        return requested_api_mode
    observed = {result.api_mode for result in results if result.api_mode}
    return observed.pop() if len(observed) == 1 else "auto"


def create_run_dir(api_mode: str) -> Path:
    """Create a timestamped run directory under tests/accuracy/runs/{mode}/."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    mode_label = api_mode if api_mode in {"local", "cloud"} else "auto"
    run_dir = Path("tests/accuracy/runs") / mode_label / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def load_runtime_search_config(api_mode: str | None = None) -> dict[str, str]:
    """Read provider/model/search settings from the active runtime config."""
    load_dotenv(override=False)
    runtime_config = {
        "provider": "unknown",
        "model": "unknown",
        "k_docs": "unknown",
        "k_contexts": "unknown",
        "answer_threshold": "unknown",
        "document_threshold": "unknown",
    }
    try:
        from statschat import load_config

        cfg = load_config(name="main")
        search_cfg = cfg.get("search", {})
        runtime_config["provider"] = str(search_cfg.get("provider", "unknown"))
        default_model = str(search_cfg.get("generative_model_name", "unknown"))
        local_model = str(search_cfg.get("generative_model_name_local", default_model))
        cloud_model = str(search_cfg.get("generative_model_name_cloud", default_model))
        if api_mode == "local":
            runtime_config["model"] = local_model
        elif api_mode == "cloud":
            runtime_config["model"] = cloud_model
        else:
            runtime_config["model"] = default_model
        runtime_config["k_docs"] = str(search_cfg.get("k_docs", "unknown"))
        runtime_config["k_contexts"] = str(search_cfg.get("k_contexts", "unknown"))
        runtime_config["answer_threshold"] = str(
            search_cfg.get("answer_threshold", "unknown")
        )
        runtime_config["document_threshold"] = str(
            search_cfg.get("document_threshold", "unknown")
        )
    except Exception:
        pass
    return runtime_config


def save_run_metadata(
    run_dir: Path,
    args: argparse.Namespace,
    summary: dict[str, object],
    run_start: datetime,
    run_end: datetime,
) -> None:
    """Write run_metadata.txt with configuration and top-line results."""
    runtime_config = load_runtime_search_config(args.api_mode)

    lines = [
        f"Run timestamp:      {run_start.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration:           {(run_end - run_start).total_seconds():.1f}s",
        f"API mode(s):        {str(summary.get('api_modes_observed', 'n/a')).replace(';', ', ')}",
        f"Provider:           {runtime_config['provider']}",
        f"Model:              {runtime_config['model']}",
        f"API host:           {args.host}",
        f"QA file:            {args.excel}",
        f"Content type:       {args.content_type}",
        f"Timeout:            {args.timeout}s",
        f"Max rows:           {args.max_rows or 'all'}",
        f"Skip rows:          {args.skip_rows}",
        f"Retrieval k:        {args.retrieval_k}",
        f"k_docs:             {runtime_config['k_docs']}",
        f"k_contexts:         {runtime_config['k_contexts']}",
        f"Answer threshold:   {runtime_config['answer_threshold']}",
        f"Document threshold: {runtime_config['document_threshold']}",
        f"Similarity thresh:  {args.similarity_threshold}",
        f"F1 threshold:       {args.f1_threshold}",
        f"Semantic threshold: {args.semantic_threshold}",
        "",
        "--- Summary ---",
        f"Total evaluated:    {summary.get('total_evaluated', 0)}",
        f"Answerable:         {summary.get('answerable_count', 0)}",
        f"Unanswerable:       {summary.get('unanswerable_count', 0)}",
        f"Overall accuracy:   {float(summary.get('overall_accuracy', 0.0)):.3f}",
        f"Answerable accuracy:{float(summary.get('answerable_accuracy', 0.0)):.3f}",
        f"Unanswerable acc.:  {float(summary.get('unanswerable_accuracy', 0.0)):.3f}",
        f"Errors:             {summary.get('error_count', 0)}",
    ]

    if summary.get("token_f1_avg") is not None:
        lines.append(f"Avg Token F1:       {float(summary['token_f1_avg']):.3f}")
    if summary.get("semantic_similarity_avg") is not None:
        lines.append(
            "Avg Semantic Sim:   " f"{float(summary['semantic_similarity_avg']):.3f}"
        )

    output_path = run_dir / "run_metadata.txt"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_run_history(
    run_dir: Path,
    args: argparse.Namespace,
    summary: dict[str, object],
    run_start: datetime,
    run_end: datetime,
) -> Path:
    """Append a single-row run summary to the cross-run history CSV."""
    runtime_config = load_runtime_search_config(args.api_mode)
    history_path = run_dir.parents[1] / "run_history.csv"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    row: dict[str, object] = {
        "run_timestamp": run_start.strftime("%Y-%m-%d %H:%M:%S"),
        "run_started_at": run_start.isoformat(timespec="seconds"),
        "run_finished_at": run_end.isoformat(timespec="seconds"),
        "duration_seconds": round((run_end - run_start).total_seconds(), 3),
        "run_dir": str(run_dir),
        "api_mode_requested": args.api_mode,
        "api_modes_observed": summary.get("api_modes_observed", ""),
        "provider": runtime_config["provider"],
        "model": runtime_config["model"],
        "host": args.host,
        "excel": str(args.excel),
        "content_type": args.content_type,
        "timeout": args.timeout,
        "max_rows": args.max_rows if args.max_rows is not None else "",
        "skip_rows": args.skip_rows,
        "retrieval_k": args.retrieval_k,
        "api_debug_requested": not getattr(args, "no_api_debug", False),
        "similarity_threshold": args.similarity_threshold,
        "f1_threshold": args.f1_threshold,
        "semantic_threshold": args.semantic_threshold,
        "abs_tol": args.abs_tol,
        "rel_tol": args.rel_tol,
        "k_docs": runtime_config["k_docs"],
        "k_contexts": runtime_config["k_contexts"],
        "answer_threshold": runtime_config["answer_threshold"],
        "document_threshold": runtime_config["document_threshold"],
    }
    row.update(summary)

    row_df = pd.DataFrame([row])
    if history_path.exists():
        existing_df = pd.read_csv(history_path)
        history_df = pd.concat([existing_df, row_df], ignore_index=True, sort=False)
    else:
        history_df = row_df
    history_df.to_csv(history_path, index=False)
    return history_path


def save_run_report(
    run_dir: Path,
    results: list[EvaluationResult],
    qa_df: pd.DataFrame,
    summary: dict[str, object],
    retrieval_k: int,
) -> None:
    """Write run_report.md with aggregate metrics and row-level comparisons."""
    lines: list[str] = ["# Evaluation Run Report\n"]

    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Retrieval k | {retrieval_k} |")
    lines.append(f"| Total evaluated | {summary.get('total_evaluated', 0)} |")
    lines.append(f"| Answerable | {summary.get('answerable_count', 0)} |")
    lines.append(f"| Unanswerable | {summary.get('unanswerable_count', 0)} |")
    lines.append(
        f"| Overall accuracy | {float(summary.get('overall_accuracy', 0.0)):.3f} |"
    )
    lines.append(
        f"| Answerable accuracy | {float(summary.get('answerable_accuracy', 0.0)):.3f} |"
    )
    lines.append(
        f"| Unanswerable accuracy | {float(summary.get('unanswerable_accuracy', 0.0)):.3f} |"
    )
    if summary.get("exact_match_avg") is not None:
        lines.append(f"| Exact Match (EM) | {float(summary['exact_match_avg']):.3f} |")
    if summary.get("token_f1_avg") is not None:
        lines.append(f"| Token F1 (avg) | {float(summary['token_f1_avg']):.3f} |")
    if summary.get("semantic_similarity_avg") is not None:
        lines.append(
            "| Semantic Similarity (avg) | "
            f"{float(summary['semantic_similarity_avg']):.3f} |"
        )
    if summary.get("pipeline_precision_at_k_avg") is not None:
        lines.append(
            "| Pipeline Precision@"
            f"{retrieval_k} (avg) | {float(summary['pipeline_precision_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline Recall@{retrieval_k} (avg) | "
            f"{float(summary['pipeline_recall_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline MRR (avg) | {float(summary['pipeline_mrr_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline nDCG (avg) | {float(summary['pipeline_ndcg_avg']):.3f} |"
        )
    if summary.get("pipeline_page_precision_at_k_avg") is not None:
        lines.append(
            f"| Pipeline Page Precision@{retrieval_k} (avg) | "
            f"{float(summary['pipeline_page_precision_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline Page Recall@{retrieval_k} (avg) | "
            f"{float(summary['pipeline_page_recall_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline Page MRR (avg) | "
            f"{float(summary['pipeline_page_mrr_avg']):.3f} |"
        )
        lines.append(
            f"| Pipeline Page nDCG (avg) | "
            f"{float(summary['pipeline_page_ndcg_avg']):.3f} |"
        )
    if summary.get("faiss_proxy_precision_at_k_avg") is not None:
        lines.append(
            f"| FAISS Proxy Precision@{retrieval_k} (avg) | "
            f"{float(summary['faiss_proxy_precision_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| FAISS Proxy Recall@{retrieval_k} (avg) | "
            f"{float(summary['faiss_proxy_recall_at_k_avg']):.3f} |"
        )
        lines.append(
            f"| FAISS Proxy MRR (avg) | {float(summary['faiss_proxy_mrr_avg']):.3f} |"
        )
        lines.append(
            f"| FAISS Proxy nDCG (avg) | {float(summary['faiss_proxy_ndcg_avg']):.3f} |"
        )
    api_modes = summary.get("api_modes_observed")
    if api_modes:
        lines.append(f"| API mode(s) | {str(api_modes).replace(';', ', ')} |")
    retrieval_sources = summary.get("faiss_proxy_metric_sources")
    if retrieval_sources:
        lines.append(
            f"| FAISS proxy source(s) | {str(retrieval_sources).replace(';', ', ')} |"
        )
    lines.append("")

    for result in results:
        row_match = qa_df.loc[
            qa_df["query_id"].astype(str).str.strip() == result.query_id
        ]
        source_text = ""
        evidence_locations = ""
        relevant_doc_ids_raw = ""
        if not row_match.empty:
            source_text = str(row_match.iloc[0].get("source_text", "")).strip()
            evidence_locations = str(
                row_match.iloc[0].get("evidence_locations", "")
            ).strip()
            relevant_doc_ids_raw = str(
                row_match.iloc[0].get("relevant_doc_ids", "")
            ).strip()

        if result.error:
            status = "ERROR"
        elif result.is_correct is True:
            status = "CORRECT"
        elif result.is_correct is False:
            status = "INCORRECT"
        else:
            status = "SKIPPED"

        returned_doc_ids = result.reference_doc_ids_all or result.reference_doc_id
        returned_pages = result.reference_pages_all
        if not returned_pages and result.reference_page is not None:
            returned_pages = str(result.reference_page)

        lines.append("---\n")
        lines.append(f"## {result.query_id} — {status}\n")
        lines.append(f"**Question:** {result.query_text}\n")

        lines.append("### Expected vs Actual\n")
        lines.append("| | Detail |")
        lines.append("|---|---|")
        lines.append(f"| **Golden answer** | {result.golden_answer} |")
        lines.append(
            f"| **Predicted answer** | {result.predicted_answer or '*(empty)*'} |"
        )
        lines.append(f"| **Should answer** | {result.should_answer} |")
        lines.append(f"| **Is refusal** | {result.is_refusal} |")
        lines.append("")

        metrics_parts: list[str] = []
        if result.exact_match is not None:
            metrics_parts.append(f"EM={result.exact_match}")
        if result.token_f1 is not None:
            metrics_parts.append(f"F1={result.token_f1:.3f}")
        if result.semantic_similarity is not None:
            metrics_parts.append(f"Semantic={result.semantic_similarity:.3f}")
        if result.similarity_score is not None:
            metrics_parts.append(f"Fuzzy={result.similarity_score:.1f}")
        if result.evidence_page_match is not None:
            metrics_parts.append(f"EvidenceMatch={result.evidence_page_match}")
        if result.scoring_method:
            metrics_parts.append(f"Scoring={result.scoring_method}")
        if metrics_parts:
            lines.append(f"**Metrics:** {' | '.join(metrics_parts)}\n")

        lines.append("### References\n")
        lines.append("| | Detail |")
        lines.append("|---|---|")
        lines.append(f"| **Expected docs** | {relevant_doc_ids_raw or '*(none)*'} |")
        lines.append(f"| **Returned doc IDs** | {returned_doc_ids or '*(none)*'} |")
        lines.append(f"| **Expected evidence** | {evidence_locations or '*(none)*'} |")
        lines.append(f"| **Returned pages** | {returned_pages or '*(none)*'} |")
        reference_titles = cell_text(result.reference_titles)
        if reference_titles:
            lines.append(
                f"| **Returned titles** | {reference_titles.replace(';', '; ')} |"
            )
        if result.reference_scores:
            lines.append(f"| **Retrieval scores** | {result.reference_scores} |")
        lines.append("")

        if source_text:
            lines.append("### Expected Source Text\n")
            lines.append(
                f"> {source_text[:500]}{'...' if len(source_text) > 500 else ''}\n"
            )

        reasoning = cell_text(result.reasoning)
        context_texts = cell_text(result.context_texts)
        highlighting = cell_text(result.highlighting)
        context_from = cell_text(result.context_from)
        context_reference = cell_text(result.context_reference)
        relevant_publications = cell_text(result.relevant_publications)
        predicted_source_text = cell_text(result.predicted_source_text)

        has_debug = any(
            [
                reasoning,
                context_texts,
                highlighting,
                context_from,
                context_reference,
                relevant_publications,
                predicted_source_text,
            ]
        )
        if has_debug:
            lines.append("### StatsChat Context\n")
            if reasoning:
                lines.append(f"**Reasoning:** {reasoning}\n")
            if highlighting:
                lines.append(f"**Key phrases:** {highlighting}\n")
            if context_from:
                lines.append(f"**Context from:** {context_from}\n")
            if context_reference:
                lines.append(f"**Context reference:** {context_reference}\n")
            if relevant_publications:
                lines.append(f"**Relevant publications:** {relevant_publications}\n")
            if predicted_source_text:
                lines.append("**Predicted source text:**\n")
                lines.append(
                    f"> {predicted_source_text[:500]}"
                    f"{'...' if len(predicted_source_text) > 500 else ''}\n"
                )
            if context_texts:
                lines.append("<details><summary>Retrieved context chunks</summary>\n")
                lines.append(f"```\n{context_texts[:2000]}\n```\n")
                lines.append("</details>\n")

        if result.error:
            lines.append(f"**Error:** `{result.error}`\n")

        lines.append("")

    output_path = run_dir / "run_report.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_summary_metrics_csv(run_dir: Path, summary: dict[str, object]) -> None:
    """Write a machine-readable summary_metrics.csv for cross-run comparison."""
    output_path = run_dir / "summary_metrics.csv"
    pd.DataFrame([summary]).to_csv(output_path, index=False)


def enrich_saved_results_dataframe(
    results_df: pd.DataFrame,
    qa_df: pd.DataFrame,
    *,
    retrieval_k: int,
    similarity_threshold: float,
    abs_tol: float,
    rel_tol: float,
    f1_threshold: float,
    semantic_threshold: float,
) -> pd.DataFrame:
    df = rename_faiss_proxy_columns(results_df.copy())
    qa_lookup = qa_df.set_index("query_id", drop=False)
    matched_query_ids = 0
    unmatched_query_ids: list[str] = []

    for column in [
        "pipeline_doc_hit_at_1",
        "pipeline_doc_hit_at_k",
        "pipeline_precision_at_k",
        "pipeline_recall_at_k",
        "pipeline_mrr",
        "pipeline_ndcg",
        "pipeline_page_precision_at_k",
        "pipeline_page_recall_at_k",
        "pipeline_page_mrr",
        "pipeline_page_ndcg",
        "scoring_method",
        "model_answered",
        "correct_refusal",
        "false_answer",
        "answered_when_expected",
        "answer_missing",
        "is_refusal",
        "is_correct",
        "exact_match",
        "token_f1",
        "similarity_score",
    ]:
        if column not in df.columns:
            df[column] = None

    for idx, row in df.iterrows():
        query_id = cell_text(row.get("query_id", ""))
        if not query_id or query_id not in qa_lookup.index:
            if query_id:
                unmatched_query_ids.append(query_id)
            continue
        matched_query_ids += 1

        qa_row = qa_lookup.loc[query_id]
        if isinstance(qa_row, pd.DataFrame):
            qa_row = qa_row.iloc[0]

        relevant_doc_ids_raw = cell_text(qa_row.get("relevant_doc_ids", ""))
        evidence_locations_raw = cell_text(qa_row.get("evidence_locations", ""))
        relevant_doc_ids = (
            split_semicolon(relevant_doc_ids_raw) if relevant_doc_ids_raw else []
        )
        evidence_locations = (
            split_semicolon(evidence_locations_raw) if evidence_locations_raw else []
        )
        evidence_pages = parse_evidence_pages(relevant_doc_ids, evidence_locations)

        reference_pairs = parse_predicted_evidence_pairs(
            row.get("predicted_evidence_locations")
        )
        reference_doc_ids_all = cell_text(row.get("reference_doc_ids_all", ""))
        reference_doc_ids = (
            split_semicolon(reference_doc_ids_all) if reference_doc_ids_all else []
        )

        pipeline_metrics = compute_pipeline_reference_metrics(
            relevant_doc_ids=relevant_doc_ids,
            evidence_pages=evidence_pages,
            reference_doc_ids=reference_doc_ids,
            reference_pairs=reference_pairs,
            k=retrieval_k,
        )
        for key, value in pipeline_metrics.items():
            df.at[idx, key] = value

        should_answer = normalize_bool(
            qa_row.get("should_answer", row.get("should_answer"))
        )
        golden_answer = cell_text(
            qa_row.get("golden_answer", row.get("golden_answer", ""))
        )
        predicted_answer = cell_text(row.get("predicted_answer", ""))
        df.at[idx, "should_answer"] = should_answer
        df.at[idx, "golden_answer"] = golden_answer

        exact_match_value: Optional[int] = None
        token_f1_value: Optional[float] = None
        similarity_score_value: Optional[float] = None
        if should_answer is True:
            exact_match_value = exact_match_score(golden_answer, predicted_answer)
            token_f1_value = token_f1_score(golden_answer, predicted_answer)
            similarity_score_value = text_match(golden_answer, predicted_answer)

        semantic_similarity = pd.to_numeric(
            row.get("semantic_similarity"), errors="coerce"
        )
        refusal = is_refusal_answer(predicted_answer, DEFAULT_REFUSAL_PHRASES) or (
            should_answer is False and not predicted_answer
        )
        model_answered = bool(predicted_answer) and not refusal
        numeric_correct = numeric_match(
            golden_answer, predicted_answer, abs_tol=abs_tol, rel_tol=rel_tol
        )
        golden_has_numbers = bool(parse_scaled_numbers(golden_answer))

        if should_answer is True:
            passes_f1 = (
                token_f1_value >= f1_threshold if token_f1_value is not None else False
            )
            passes_semantic = (
                semantic_similarity >= semantic_threshold
                if not pd.isna(semantic_similarity)
                else False
            )
            if refusal:
                is_correct = False
            elif golden_has_numbers:
                is_correct = exact_match_value == 1 or numeric_correct
            else:
                is_correct = (
                    exact_match_value == 1
                    or numeric_correct
                    or (
                        similarity_score_value is not None
                        and similarity_score_value >= similarity_threshold
                    )
                    or passes_f1
                    or passes_semantic
                )
            correct_refusal = None
            false_answer = None
            answered_when_expected = model_answered
            answer_missing = not model_answered
        elif should_answer is False:
            is_correct = refusal
            correct_refusal = refusal
            false_answer = not refusal
            answered_when_expected = None
            answer_missing = None
        else:
            is_correct = None
            correct_refusal = None
            false_answer = None
            answered_when_expected = None
            answer_missing = None

        scoring_method = determine_scoring_method(
            should_answer=should_answer,
            refusal=refusal,
            exact_match=exact_match_value,
            numeric_correct=numeric_correct,
            golden_has_numbers=golden_has_numbers,
            similarity_score=similarity_score_value,
            similarity_threshold=similarity_threshold,
            token_f1=token_f1_value,
            f1_threshold=f1_threshold,
            semantic_similarity=(
                float(semantic_similarity) if not pd.isna(semantic_similarity) else None
            ),
            semantic_threshold=semantic_threshold,
        )
        df.at[idx, "exact_match"] = exact_match_value
        df.at[idx, "token_f1"] = token_f1_value
        df.at[idx, "similarity_score"] = similarity_score_value
        df.at[idx, "is_refusal"] = refusal
        df.at[idx, "model_answered"] = model_answered
        df.at[idx, "is_correct"] = is_correct
        df.at[idx, "correct_refusal"] = correct_refusal
        df.at[idx, "false_answer"] = false_answer
        df.at[idx, "answered_when_expected"] = answered_when_expected
        df.at[idx, "answer_missing"] = answer_missing
        df.at[idx, "scoring_method"] = scoring_method

    if len(df) > 0 and matched_query_ids == 0:
        sample_unmatched = ", ".join(unmatched_query_ids[:5]) or "(none)"
        raise ValueError(
            "Rescoring matched zero rows between results CSV and QA sheet by query_id. "
            f"Sample result query_ids: {sample_unmatched}. "
            "Pass the correct --excel file or update the saved run metadata."
        )

    return df


def load_generation_metadata(excel_path: Path) -> dict[str, str]:
    try:
        df = pd.read_excel(excel_path, sheet_name="Generation_Metadata")
    except ValueError:
        return {}
    if "field" not in df.columns or "value" not in df.columns:
        return {}
    data: dict[str, str] = {}
    for _, row in df.iterrows():
        field = str(row.get("field", "")).strip()
        if not field:
            continue
        data[field] = str(row.get("value", "")).strip()
    return data


def report_condition_alignment(excel_path: Path, content_type: str) -> None:
    metadata = load_generation_metadata(excel_path)
    if not metadata:
        return

    expected: dict[str, str] = {}
    try:
        from statschat import load_config

        cfg = load_config(name="main")
        search = cfg.get("search", {})
        expected = {
            "eval.k_docs": str(search.get("k_docs", "")),
            "eval.k_contexts": str(search.get("k_contexts", "")),
            "eval.similarity_threshold": str(search.get("similarity_threshold", "")),
            "eval.answer_threshold": str(search.get("answer_threshold", "")),
            "eval.document_threshold": str(search.get("document_threshold", "")),
        }
    except Exception:
        pass

    print("\nGeneration/Evaluation condition check")
    print(
        f"Generated provider/model: {metadata.get('provider', '')} / {metadata.get('model', '')}"
    )
    print(f"Generation strict filters: {metadata.get('strict_filters', '')}")
    print(f"Evaluation content_type: {content_type}")

    mismatches: list[str] = []
    for key, current in expected.items():
        generated = metadata.get(key, "")
        if generated and current and generated != current:
            mismatches.append(f"{key}: generated={generated}, current={current}")

    if mismatches:
        print("WARNING: Config differs from generation-time settings:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
    else:
        print("Config alignment OK (or no comparable metadata fields).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate StatsChat QA accuracy.")
    parser.add_argument(
        "--excel",
        type=Path,
        default=Path("tests/accuracy/StatsChat_QA_Verified_Audited.xlsx"),
        help="Path to the Excel QA template",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL for the StatsChat API",
    )
    parser.add_argument(
        "--content-type",
        type=str,
        default="latest",
        choices=["latest", "all"],
        help="Content type passed to /search",
    )
    parser.add_argument(
        "--api-mode",
        type=str,
        default="auto",
        choices=["auto", "local", "cloud"],
        help="Expected API contract. Use 'auto' to detect from the /search response.",
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0, help="Request timeout seconds"
    )
    parser.add_argument(
        "--max-rows", type=int, default=None, help="Limit number of rows evaluated"
    )
    parser.add_argument(
        "--skip-rows",
        type=int,
        default=0,
        help="Skip the first N rows before evaluation",
    )
    parser.add_argument(
        "--sleep", type=float, default=0.0, help="Sleep between requests"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=85.0,
        help="RapidFuzz token set ratio threshold",
    )
    parser.add_argument(
        "--f1-threshold",
        type=float,
        default=0.80,
        help="Token F1 threshold for considering an answer correct",
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.90,
        help="Semantic similarity threshold for considering an answer correct",
    )
    parser.add_argument(
        "--abs-tol",
        type=float,
        default=0.1,
        help="Absolute tolerance for numeric matches",
    )
    parser.add_argument(
        "--rel-tol",
        type=float,
        default=0.01,
        help="Relative tolerance for numeric matches",
    )
    parser.add_argument(
        "--results-output",
        type=Path,
        default=Path("tests/accuracy/accuracy_results.csv"),
        help="CSV output for per-question evaluation results",
    )
    parser.add_argument(
        "--results-input",
        type=Path,
        default=None,
        help=(
            "Existing accuracy_results.csv to re-score locally without calling the API. "
            "When provided, the evaluator enriches the saved run with pipeline metrics "
            "and scoring_method and writes a new CSV/summary."
        ),
    )
    parser.add_argument(
        "--answers-output",
        type=Path,
        default=Path("tests/accuracy/StatsChat_QA_With_Answers.xlsx"),
        help="Excel output with answers and metrics merged into QA_Data",
    )
    parser.add_argument(
        "--write-answers-excel",
        action="store_true",
        help="Write predictions and metrics into a new Excel file",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=Path("tests/accuracy/qa_data_issues.csv"),
        help="CSV output for QA data quality issues",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help=(
            "CSV output for aggregate summary metrics. "
            "Defaults to <results-output stem>_summary.csv"
        ),
    )
    parser.add_argument(
        "--retrieval-k",
        type=int,
        default=8,
        help="k for Precision@k/Recall@k/MRR/nDCG",
    )
    parser.add_argument(
        "--no-retrieval",
        action="store_true",
        help="Disable retrieval metrics (local FAISS search)",
    )
    parser.add_argument(
        "--semantic-model",
        type=str,
        default="sentence-transformers/all-mpnet-base-v2",
        help="SentenceTransformers model for semantic similarity",
    )
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Disable semantic similarity metric",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate QA data without calling the API",
    )
    parser.add_argument(
        "--query-id-prefix",
        type=str,
        default="QQ",
        help="Expected query ID prefix in QA_Data (default: QQ)",
    )
    parser.add_argument(
        "--require-reviewers",
        action="store_true",
        help="Require Reviewers to contain at least two initials for answerable rows",
    )
    parser.add_argument(
        "--no-api-debug",
        action="store_true",
        help=(
            "Do not request debug payloads from the API. "
            "By default the evaluator requests debug details so cloud runs can "
            "capture reasoning and retrieved context."
        ),
    )
    parser.add_argument(
        "--sheet-name",
        type=str,
        default="QA_Data",
        help="Preferred worksheet name containing the QA table; auto-detected if absent",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.excel.exists():
        print(f"Excel file not found: {args.excel}", file=sys.stderr)
        sys.exit(1)

    qa_sheet_name, workbook_sheet_names = detect_qa_sheet_name(
        args.excel, preferred_sheet=args.sheet_name
    )

    df = pd.read_excel(args.excel, sheet_name=qa_sheet_name)
    df = df.rename(columns=lambda c: str(c).strip())

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        print(f"Missing required columns: {sorted(missing_columns)}", file=sys.stderr)
        sys.exit(1)

    report_condition_alignment(args.excel, args.content_type)

    issues = validate_rows(
        df,
        require_reviewers=args.require_reviewers,
        query_id_prefix=args.query_id_prefix.upper(),
    )
    if issues:
        save_issues(issues, args.issues_output)
        print(f"Data quality issues saved to: {args.issues_output}")
    elif args.validate_only:
        print("No data quality issues found.")

    if args.validate_only:
        return

    if args.results_input is not None:
        if not args.results_input.exists():
            print(f"Results CSV not found: {args.results_input}", file=sys.stderr)
            sys.exit(1)

        results_output = args.results_output
        if results_output == Path("tests/accuracy/accuracy_results.csv"):
            results_output = args.results_input.with_name(
                f"{args.results_input.stem}_rescored.csv"
            )
        summary_output = args.summary_output
        if summary_output is None:
            summary_output = results_output.with_name(
                f"{results_output.stem}_summary.csv"
            )

        results_df = pd.read_csv(args.results_input)
        results_df = enrich_saved_results_dataframe(
            results_df,
            df,
            retrieval_k=args.retrieval_k,
            similarity_threshold=args.similarity_threshold,
            abs_tol=args.abs_tol,
            rel_tol=args.rel_tol,
            f1_threshold=args.f1_threshold,
            semantic_threshold=args.semantic_threshold,
        )
        results_df.to_csv(results_output, index=False)
        print(f"Rescored results saved to: {results_output}")

        summary = build_summary_from_dataframe(results_df, retrieval_k=args.retrieval_k)
        save_summary(summary, summary_output)
        print(f"Summary saved to: {summary_output}")
        report_output = results_output.with_name(f"{results_output.stem}_report.md")
        save_run_report(
            report_output.parent,
            dataframe_to_results(results_df),
            df,
            summary,
            retrieval_k=args.retrieval_k,
        )
        generated_report = report_output.parent / "run_report.md"
        if generated_report.exists():
            generated_report.replace(report_output)
        print(f"Run report saved to: {report_output}")
        print_summary(summary, retrieval_k=args.retrieval_k)
        return

    semantic_model = None
    if not args.no_semantic:
        semantic_model = SemanticSimilarityEvaluator(args.semantic_model)

    run_start = datetime.now()
    results = evaluate(
        df=df,
        base_url=args.host,
        content_type=args.content_type,
        api_mode=args.api_mode,
        timeout=args.timeout,
        max_rows=args.max_rows,
        sleep_seconds=args.sleep,
        refusal_phrases=DEFAULT_REFUSAL_PHRASES,
        similarity_threshold=args.similarity_threshold,
        abs_tol=args.abs_tol,
        rel_tol=args.rel_tol,
        retrieval_k=args.retrieval_k,
        compute_retrieval=not args.no_retrieval,
        semantic_model=semantic_model,
        f1_threshold=args.f1_threshold,
        semantic_threshold=args.semantic_threshold,
        skip_rows=args.skip_rows,
        request_api_debug=not args.no_api_debug,
    )
    run_end = datetime.now()

    save_results(results, args.results_output)
    print(f"Results saved to: {args.results_output}")
    summary_output = args.summary_output
    if summary_output is None:
        summary_output = args.results_output.with_name(
            f"{args.results_output.stem}_summary.csv"
        )
    summary = build_summary(results, retrieval_k=args.retrieval_k)
    save_summary(summary, summary_output)
    print(f"Summary saved to: {summary_output}")
    if args.write_answers_excel:
        save_results_excel(
            args.excel,
            qa_sheet_name,
            workbook_sheet_names,
            results,
            args.answers_output,
        )
        print(f"Excel with answers saved to: {args.answers_output}")

    run_dir = create_run_dir(determine_effective_api_mode(args.api_mode, results))
    run_results_output = run_dir / "accuracy_results.csv"
    save_results(results, run_results_output)
    print(f"Run results saved to: {run_results_output}")
    if issues:
        run_issues_output = run_dir / "qa_data_issues.csv"
        save_issues(issues, run_issues_output)
        print(f"Run data quality issues saved to: {run_issues_output}")
    save_run_metadata(run_dir, args, summary, run_start, run_end)
    print(f"Run metadata saved to: {run_dir / 'run_metadata.txt'}")
    save_run_report(
        run_dir,
        results,
        df,
        summary,
        retrieval_k=args.retrieval_k,
    )
    print(f"Run report saved to: {run_dir / 'run_report.md'}")
    save_summary_metrics_csv(run_dir, summary)
    print(f"Summary metrics saved to: {run_dir / 'summary_metrics.csv'}")
    history_path = append_run_history(run_dir, args, summary, run_start, run_end)
    print(f"Run history updated: {history_path}")

    print_summary(summary, retrieval_k=args.retrieval_k)


if __name__ == "__main__":
    main()
