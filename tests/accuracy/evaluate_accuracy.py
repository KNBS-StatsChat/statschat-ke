#!/usr/bin/env python3
"""Evaluate StatsChat accuracy against the KNBS QA template."""
from __future__ import annotations

import argparse
import math
import re
import string
import sys
import time
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests
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
QUOTE_PATTERN = re.compile(r"[\"“”]")
ARTICLE_PATTERN = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
REVIEWER_TOKEN_PATTERN = re.compile(r"^[A-Za-z]{1,4}$")

PERCENT_KEYWORDS = re.compile(
    r"(percent|percentage|rate|inflation|growth|share|proportion)",
    re.IGNORECASE,
)


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
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip() == ""


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
    golden_numbers = (
        parse_percent_numbers(golden) if expects_percent else parse_numbers(golden)
    )
    if not golden_numbers:
        golden_numbers = parse_numbers(golden)
    if not golden_numbers:
        return False

    if expects_percent:
        candidates = parse_percent_numbers(answer)
    else:
        candidates = parse_numbers(answer)

    if not candidates:
        return False

    def matches_expected(expected: float, candidate: float) -> bool:
        if expected == 0:
            if abs(candidate) <= abs_tol:
                return True
            return False
        abs_diff = abs(candidate - expected)
        rel_diff = abs_diff / abs(expected)
        if abs_diff <= abs_tol or rel_diff <= rel_tol:
            return True

        if expects_percent and expected >= 1:
            candidate_pct = candidate * 100
            pct_abs_diff = abs(candidate_pct - expected)
            pct_rel_diff = pct_abs_diff / abs(expected)
            if pct_abs_diff <= abs_tol or pct_rel_diff <= rel_tol:
                return True
        if expects_percent and expected < 1:
            candidate_ratio = candidate / 100
            ratio_abs_diff = abs(candidate_ratio - expected)
            ratio_rel_diff = ratio_abs_diff / abs(expected)
            if ratio_abs_diff <= abs_tol or ratio_rel_diff <= rel_tol:
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
                candidate = str(item.get("page_url") or item.get("url") or "").strip()
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


def compute_retrieval_metrics(
    relevant_doc_ids: list[str],
    retrieved_doc_ids: list[str],
    k: int,
) -> tuple[float, float, float, float]:
    relevant_set = {normalize_doc_id(doc_id) for doc_id in relevant_doc_ids}
    retrieved_norm_all = [normalize_doc_id(doc_id) for doc_id in retrieved_doc_ids]
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
) -> tuple[bool, bool]:
    relevant_set = {normalize_doc_id(doc_id) for doc_id in relevant_doc_ids}
    retrieved_norm_all = [normalize_doc_id(doc_id) for doc_id in retrieved_doc_ids]
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
        query_id = str(row.get("query_id", "")).strip()
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

        golden_answer = str(row.get("golden_answer", "")).strip()
        source_text = str(row.get("source_text", "")).strip()
        relevant_doc_ids = str(row.get("relevant_doc_ids", "")).strip()
        evidence_locations = str(row.get("evidence_locations", "")).strip()
        query_text = str(row.get("query_text", "")).strip()

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
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []

    if skip_rows:
        df = df.iloc[skip_rows:]
    if max_rows:
        df = df.head(max_rows)

    for _, row in df.iterrows():
        query_id = str(row.get("query_id", "")).strip()
        query_text = str(row.get("query_text", "")).strip()
        golden_answer = str(row.get("golden_answer", "")).strip()
        relevant_doc_ids_raw = str(row.get("relevant_doc_ids", "")).strip()
        evidence_locations_raw = str(row.get("evidence_locations", "")).strip()
        should_answer = normalize_bool(row.get("should_answer"))
        relevant_doc_ids = (
            split_semicolon(relevant_doc_ids_raw) if relevant_doc_ids_raw else []
        )
        evidence_locations = (
            split_semicolon(evidence_locations_raw) if evidence_locations_raw else []
        )
        evidence_pages = parse_evidence_pages(relevant_doc_ids, evidence_locations)

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
                )
            )
            continue

        try:
            response = requests.get(
                f"{base_url}/search",
                params={
                    "q": query_text,
                    "content_type": content_type,
                    "debug": "false",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            predicted = str(payload.get("answer", "")).strip()
            predicted_source_text = str(payload.get("context_reference", "")).strip()
            detected_api_mode = detect_api_mode(payload)
            api_mode_used = detected_api_mode if api_mode == "auto" else api_mode
            (
                reference_url,
                reference_doc_id,
                reference_page,
                reference_count,
                reference_urls,
            ) = extract_reference_details(payload)
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

        if compute_retrieval and relevant_doc_ids and api_mode_used == "local":
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

        refusal = is_refusal_answer(predicted, refusal_phrases)
        model_answered = bool(predicted) and not refusal
        similarity_score: Optional[float] = None
        is_correct: Optional[bool] = None
        exact_match: Optional[int] = None
        token_f1: Optional[float] = None
        semantic_similarity: Optional[float] = None

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
                is_correct = (
                    exact_match == 1
                    or numeric_correct
                    or similarity_score >= similarity_threshold
                    or passes_f1
                    or passes_semantic
                )
            answered_when_expected = model_answered
            answer_missing = not model_answered
        elif should_answer is False:
            is_correct = refusal
            correct_refusal = refusal
            false_answer = not refusal

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
            )
        )

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return results


def build_summary(
    results: list[EvaluationResult], retrieval_k: int
) -> dict[str, object]:
    evaluated = [r for r in results if r.is_correct is not None]
    total = len(evaluated)
    answerable = [r for r in evaluated if r.should_answer is True]
    unanswerable = [r for r in evaluated if r.should_answer is False]

    answerable_correct = sum(1 for r in answerable if r.is_correct)
    unanswerable_correct = sum(1 for r in unanswerable if r.is_correct)

    overall_correct = answerable_correct + unanswerable_correct
    overall_accuracy = overall_correct / total if total else 0.0

    answerable_accuracy = answerable_correct / len(answerable) if answerable else 0.0
    unanswerable_accuracy = (
        unanswerable_correct / len(unanswerable) if unanswerable else 0.0
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

    api_modes = sorted({r.api_mode for r in results if r.api_mode})
    if api_modes:
        summary["api_modes_observed"] = ";".join(api_modes)

    em_scores = [r.exact_match for r in answerable if r.exact_match is not None]
    f1_scores = [r.token_f1 for r in answerable if r.token_f1 is not None]
    semantic_scores = [
        r.semantic_similarity for r in answerable if r.semantic_similarity is not None
    ]
    if em_scores:
        summary["exact_match_avg"] = sum(em_scores) / len(em_scores)
    if f1_scores:
        summary["token_f1_avg"] = sum(f1_scores) / len(f1_scores)
    if semantic_scores:
        summary["semantic_similarity_avg"] = sum(semantic_scores) / len(semantic_scores)

    retrieval_metrics = [
        r
        for r in evaluated
        if r.precision_at_k is not None and r.recall_at_k is not None
    ]
    if retrieval_metrics:
        summary["precision_at_k_avg"] = sum(
            r.precision_at_k for r in retrieval_metrics
        ) / len(retrieval_metrics)
        summary["recall_at_k_avg"] = sum(
            r.recall_at_k for r in retrieval_metrics
        ) / len(retrieval_metrics)
        summary["mrr_avg"] = sum(
            r.mrr for r in retrieval_metrics if r.mrr is not None
        ) / len(retrieval_metrics)
        summary["ndcg_avg"] = sum(
            r.ndcg for r in retrieval_metrics if r.ndcg is not None
        ) / len(retrieval_metrics)

    retrieval_sources = sorted(
        {r.retrieval_metric_source for r in results if r.retrieval_metric_source}
    )
    if retrieval_sources:
        summary["retrieval_metric_sources"] = ";".join(retrieval_sources)

    doc_hit_rows = [r for r in evaluated if r.doc_hit_at_k is not None]
    if doc_hit_rows:
        doc_hit_1_count = sum(1 for r in doc_hit_rows if r.doc_hit_at_1)
        doc_hit_k_count = sum(1 for r in doc_hit_rows if r.doc_hit_at_k)
        summary["doc_hit_at_1_rate"] = doc_hit_1_count / len(doc_hit_rows)
        summary["doc_hit_at_1_count"] = doc_hit_1_count
        summary["doc_hit_at_1_denom"] = len(doc_hit_rows)
        summary["doc_hit_at_k_rate"] = doc_hit_k_count / len(doc_hit_rows)
        summary["doc_hit_at_k_count"] = doc_hit_k_count
        summary["doc_hit_at_k_denom"] = len(doc_hit_rows)

    first_reference_doc_rows = [
        r for r in evaluated if r.reference_doc_match is not None
    ]
    if first_reference_doc_rows:
        first_reference_doc_count = sum(
            1 for r in first_reference_doc_rows if r.reference_doc_match
        )
        summary["first_reference_doc_match_rate"] = first_reference_doc_count / len(
            first_reference_doc_rows
        )
        summary["first_reference_doc_match_count"] = first_reference_doc_count
        summary["first_reference_doc_match_denom"] = len(first_reference_doc_rows)

    any_reference_doc_rows = [
        r for r in evaluated if r.any_reference_doc_match is not None
    ]
    if any_reference_doc_rows:
        any_reference_doc_count = sum(
            1 for r in any_reference_doc_rows if r.any_reference_doc_match
        )
        summary["any_reference_doc_match_rate"] = any_reference_doc_count / len(
            any_reference_doc_rows
        )
        summary["any_reference_doc_match_count"] = any_reference_doc_count
        summary["any_reference_doc_match_denom"] = len(any_reference_doc_rows)

    first_reference_page_rows = [
        r for r in evaluated if r.evidence_page_match is not None
    ]
    if first_reference_page_rows:
        first_reference_page_count = sum(
            1 for r in first_reference_page_rows if r.evidence_page_match
        )
        summary["first_reference_page_hit_rate"] = first_reference_page_count / len(
            first_reference_page_rows
        )
        summary["first_reference_page_hit_count"] = first_reference_page_count
        summary["first_reference_page_hit_denom"] = len(first_reference_page_rows)

    any_reference_page_rows = [
        r for r in evaluated if r.any_reference_page_match is not None
    ]
    if any_reference_page_rows:
        any_reference_page_count = sum(
            1 for r in any_reference_page_rows if r.any_reference_page_match
        )
        summary["any_reference_page_hit_rate"] = any_reference_page_count / len(
            any_reference_page_rows
        )
        summary["any_reference_page_hit_count"] = any_reference_page_count
        summary["any_reference_page_hit_denom"] = len(any_reference_page_rows)

    if unanswerable:
        correct_refusal_count = sum(1 for r in unanswerable if r.correct_refusal)
        false_answer_count = sum(1 for r in unanswerable if r.false_answer)
        summary["correct_refusal_rate"] = correct_refusal_count / len(unanswerable)
        summary["correct_refusal_count"] = correct_refusal_count
        summary["correct_refusal_denom"] = len(unanswerable)
        summary["false_answer_rate"] = false_answer_count / len(unanswerable)
        summary["false_answer_count"] = false_answer_count
        summary["false_answer_denom"] = len(unanswerable)

    if answerable:
        answered_when_expected_count = sum(
            1 for r in answerable if r.answered_when_expected
        )
        answer_missing_count = sum(1 for r in answerable if r.answer_missing)
        summary["answer_coverage"] = answered_when_expected_count / len(answerable)
        summary["answer_coverage_count"] = answered_when_expected_count
        summary["answer_coverage_denom"] = len(answerable)
        summary["answer_missing_rate"] = answer_missing_count / len(answerable)
        summary["answer_missing_count"] = answer_missing_count
        summary["answer_missing_denom"] = len(answerable)

    safe_response_rate = overall_accuracy
    summary["safe_response_rate"] = safe_response_rate

    errors = [r for r in results if r.error]
    summary["error_count"] = len(errors)

    return summary


def print_summary(summary: dict[str, object], retrieval_k: int) -> None:
    print("\nAccuracy summary")
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

    if summary.get("precision_at_k_avg") is not None:
        print(f"Precision@k (avg): {summary['precision_at_k_avg']:.3f}")
        print(f"Recall@k (avg): {summary['recall_at_k_avg']:.3f}")
        print(f"MRR (avg): {summary['mrr_avg']:.3f}")
        print(f"nDCG (avg): {summary['ndcg_avg']:.3f}")

    retrieval_sources = summary.get("retrieval_metric_sources")
    if retrieval_sources:
        print(
            f"Retrieval metric source(s): {str(retrieval_sources).replace(';', ', ')}"
        )

    if summary.get("doc_hit_at_1_rate") is not None:
        print(
            f"Doc Hit@1: {summary['doc_hit_at_1_rate']:.3f} "
            f"({summary['doc_hit_at_1_count']}/{summary['doc_hit_at_1_denom']})"
        )
        print(
            f"Doc Hit@{retrieval_k}: {summary['doc_hit_at_k_rate']:.3f} "
            f"({summary['doc_hit_at_k_count']}/{summary['doc_hit_at_k_denom']})"
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
    df = pd.DataFrame([result.__dict__ for result in results])
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
    results_df = pd.DataFrame([result.__dict__ for result in results])
    merged = qa_df.merge(results_df, on=["query_id", "query_text"], how="left")

    predicted_answers_df = merged[
        [
            "query_id",
            "query_text",
            "predicted_answer",
            "predicted_relevant_doc_ids",
            "predicted_evidence_locations",
            "predicted_source_text",
            "reference_url",
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
        default=Path("tests/accuracy/StatsChat_QA_Template_2.xlsx"),
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
        default=5,
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
        default="Q",
        help="Expected query ID prefix in QA_Data (default: Q)",
    )
    parser.add_argument(
        "--require-reviewers",
        action="store_true",
        help="Require Reviewers to contain at least two initials for answerable rows",
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

    semantic_model = None
    if not args.no_semantic:
        semantic_model = SemanticSimilarityEvaluator(args.semantic_model)

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
    )

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
    print_summary(summary, retrieval_k=args.retrieval_k)


if __name__ == "__main__":
    main()
