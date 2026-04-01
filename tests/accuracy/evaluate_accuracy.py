#!/usr/bin/env python3
"""Evaluate StatsChat accuracy against the KNBS QA template."""
from __future__ import annotations

import argparse
import math
import os
import re
import string
import sys
import time
from datetime import datetime
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
    api_mode: Optional[str]
    reference_count: Optional[int]
    reference_urls: Optional[str]
    reference_doc_ids: Optional[str]
    reference_pages: Optional[str]
    evidence_page_match: Optional[bool]
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
    # Debug / reasoning fields (populated when API returns debug info)
    reasoning: Optional[str] = None
    context_texts: Optional[str] = None
    reference_scores: Optional[str] = None
    reference_titles: Optional[str] = None
    highlighting: Optional[str] = None
    context_from: Optional[str] = None
    context_reference: Optional[str] = None
    relevant_publications: Optional[str] = None


@dataclass
class Issue:
    query_id: str
    issue: str
    detail: str


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
        self.model = SentenceTransformer(model_name)

    def similarity(self, golden: str, answer: str) -> float:
        embeddings = self.model.encode([golden, answer], convert_to_tensor=True)
        return float(cos_sim(embeddings[0], embeddings[1]).item())


def normalize_doc_id(value: str) -> str:
    original = value.strip().lower()
    text = original
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
    result = text.strip("-")
    return result if result else original


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
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    """Extract reference URLs, doc IDs, and pages from the API response.

    Returns semicolon-joined strings for URLs, doc IDs, and pages so that
    all documents returned by the API are captured (not just the first).
    """
    references = payload.get("references")
    urls: list[str] = []
    if isinstance(references, str):
        url = references.strip()
        if url:
            urls.append(url)
    elif isinstance(references, list):
        for item in references:
            if isinstance(item, dict):
                candidate = str(item.get("page_url", "")).strip()
                if candidate:
                    urls.append(candidate)
            elif isinstance(item, str) and item.strip():
                urls.append(item.strip())
    reference_count = len(urls) if isinstance(references, (str, list)) else None

    doc_ids: list[str] = []
    pages: list[str] = []
    for url in urls:
        parsed_ref = urlparse(url)
        doc_ids.append(normalize_doc_id(Path(parsed_ref.path).name))
        page = extract_page_from_url(url)
        pages.append(str(page) if page is not None else "")

    reference_urls = ";".join(urls) if urls else None
    reference_doc_ids = ";".join(doc_ids) if doc_ids else None
    reference_pages = ";".join(pages) if pages else None
    return reference_urls, reference_doc_ids, reference_pages, reference_count


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
        reference_urls: Optional[str] = None
        reference_doc_ids: Optional[str] = None
        reference_pages: Optional[str] = None
        evidence_page_match: Optional[bool] = None
        retrieval_metric_source: Optional[str] = None

        if not query_text:
            results.append(
                EvaluationResult(
                    query_id=query_id,
                    query_text=query_text,
                    should_answer=should_answer,
                    golden_answer=golden_answer,
                    predicted_answer="",
                    api_mode=None,
                    reference_count=None,
                    reference_urls=None,
                    reference_doc_ids=None,
                    reference_pages=None,
                    evidence_page_match=None,
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
                    "debug": "true",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            predicted = str(payload.get("answer", "")).strip()
            detected_api_mode = detect_api_mode(payload)
            api_mode_used = detected_api_mode if api_mode == "auto" else api_mode
            reference_urls, reference_doc_ids, reference_pages, reference_count = (
                extract_reference_details(payload)
            )

            # --- Extract debug / context fields ---
            debug_response = payload.get("debug_response", {}) or {}
            reasoning = debug_response.get("reasoning")
            highlights = []
            for h_key in ("highlighting1", "highlighting2", "highlighting3"):
                h_val = debug_response.get(h_key)
                if h_val:
                    if isinstance(h_val, list):
                        highlights.extend(h_val)
                    else:
                        highlights.append(str(h_val))
            highlighting_str = "; ".join(highlights) if highlights else None

            # Cloud: extract page_content and score from references
            refs = payload.get("references")
            context_texts_list: list[str] = []
            ref_scores_list: list[str] = []
            ref_titles_list: list[str] = []
            if isinstance(refs, list):
                for item in refs:
                    if isinstance(item, dict):
                        pc = str(item.get("page_content", "")).strip()
                        if pc:
                            context_texts_list.append(pc)
                        sc = item.get("score")
                        if sc is not None:
                            ref_scores_list.append(str(round(float(sc), 4)))
                        ti = str(item.get("title", "")).strip()
                        if ti:
                            ref_titles_list.append(ti)

            # Local: capture local-only fields
            local_context_from = str(payload.get("context_from", "")).strip() or None
            local_context_ref = (
                str(payload.get("context_reference", "")).strip() or None
            )
            pub_one = str(payload.get("relevant_publication_one", "")).strip()
            pub_two = str(payload.get("relevant_publication_two", "")).strip()
            relevant_pubs = "; ".join(p for p in (pub_one, pub_two) if p) or None

            context_texts_str = (
                "\n---\n".join(context_texts_list) if context_texts_list else None
            )
            ref_scores_str = ";".join(ref_scores_list) if ref_scores_list else None
            ref_titles_str = ";".join(ref_titles_list) if ref_titles_list else None
            if reference_doc_ids and reference_pages:
                ref_doc_list = reference_doc_ids.split(";")
                ref_page_list = reference_pages.split(";")
                evidence_page_match = False
                for ref_doc, ref_page_str in zip(ref_doc_list, ref_page_list):
                    if not ref_page_str:
                        continue
                    pages = evidence_pages.get(ref_doc, set())
                    if int(ref_page_str) in pages:
                        evidence_page_match = True
                        break
        except Exception as exc:  # noqa: BLE001
            results.append(
                EvaluationResult(
                    query_id=query_id,
                    query_text=query_text,
                    should_answer=should_answer,
                    golden_answer=golden_answer,
                    predicted_answer="",
                    api_mode=api_mode_used,
                    reference_count=reference_count,
                    reference_urls=reference_urls,
                    reference_doc_ids=reference_doc_ids,
                    reference_pages=reference_pages,
                    evidence_page_match=evidence_page_match,
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
                precision_at_k, recall_at_k, mrr, ndcg = compute_retrieval_metrics(
                    relevant_doc_ids=relevant_doc_ids,
                    retrieved_doc_ids=retrieved_raw,
                    k=retrieval_k,
                )
            except Exception as exc:  # noqa: BLE001
                precision_at_k = None
                recall_at_k = None
                mrr = None
                ndcg = None
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
        elif should_answer is False:
            is_correct = refusal

        results.append(
            EvaluationResult(
                query_id=query_id,
                query_text=query_text,
                should_answer=should_answer,
                golden_answer=golden_answer,
                predicted_answer=predicted,
                api_mode=api_mode_used,
                reference_count=reference_count,
                reference_urls=reference_urls,
                reference_doc_ids=reference_doc_ids,
                reference_pages=reference_pages,
                evidence_page_match=evidence_page_match,
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
                context_texts=context_texts_str,
                reference_scores=ref_scores_str,
                reference_titles=ref_titles_str,
                highlighting=highlighting_str,
                context_from=local_context_from,
                context_reference=local_context_ref,
                relevant_publications=relevant_pubs,
            )
        )

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return results


def print_summary(results: list[EvaluationResult]) -> None:
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

    print("\nAccuracy summary")
    print(f"Total evaluated: {total}")
    print(f"Answerable: {len(answerable)}")
    print(f"Unanswerable: {len(unanswerable)}")
    print(f"Answerable accuracy: {answerable_accuracy:.3f}")
    print(f"Unanswerable accuracy: {unanswerable_accuracy:.3f}")
    print(f"Overall accuracy: {overall_accuracy:.3f}")

    api_modes = sorted({r.api_mode for r in results if r.api_mode})
    if api_modes:
        print(f"API mode(s) observed: {', '.join(api_modes)}")

    em_scores = [r.exact_match for r in answerable if r.exact_match is not None]
    f1_scores = [r.token_f1 for r in answerable if r.token_f1 is not None]
    semantic_scores = [
        r.semantic_similarity for r in answerable if r.semantic_similarity is not None
    ]
    if em_scores:
        print(f"Exact Match (EM): {sum(em_scores) / len(em_scores):.3f}")
    if f1_scores:
        print(f"Token F1 (avg): {sum(f1_scores) / len(f1_scores):.3f}")
    if semantic_scores:
        print(
            f"Semantic Similarity (avg): {sum(semantic_scores) / len(semantic_scores):.3f}"
        )

    retrieval_metrics = [
        r
        for r in evaluated
        if r.precision_at_k is not None and r.recall_at_k is not None
    ]
    if retrieval_metrics:
        avg_precision = sum(r.precision_at_k for r in retrieval_metrics) / len(
            retrieval_metrics
        )
        avg_recall = sum(r.recall_at_k for r in retrieval_metrics) / len(
            retrieval_metrics
        )
        avg_mrr = sum(r.mrr for r in retrieval_metrics if r.mrr is not None) / len(
            retrieval_metrics
        )
        avg_ndcg = sum(r.ndcg for r in retrieval_metrics if r.ndcg is not None) / len(
            retrieval_metrics
        )
        print(f"Precision@k (avg): {avg_precision:.3f}")
        print(f"Recall@k (avg): {avg_recall:.3f}")
        print(f"MRR (avg): {avg_mrr:.3f}")
        print(f"nDCG (avg): {avg_ndcg:.3f}")

    retrieval_sources = sorted(
        {r.retrieval_metric_source for r in results if r.retrieval_metric_source}
    )
    if retrieval_sources:
        print(f"Retrieval metric source(s): {', '.join(retrieval_sources)}")

    safe_response_rate = overall_accuracy
    print(f"Safe response rate: {safe_response_rate:.3f}")

    errors = [r for r in results if r.error]
    if errors:
        print(f"\nErrors: {len(errors)} (see output file for details)")


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


def save_results_excel(
    source_excel: Path, results: list[EvaluationResult], output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    qa_df = pd.read_excel(source_excel, sheet_name="QA_Data")
    qa_df = qa_df.rename(columns=lambda c: str(c).strip())
    results_df = pd.DataFrame([result.__dict__ for result in results])
    merged = qa_df.merge(results_df, on=["query_id", "query_text"], how="left")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        merged.to_excel(writer, sheet_name="QA_Data", index=False)
        for sheet in ["Instructions", "Explanation"]:
            try:
                df_sheet = pd.read_excel(source_excel, sheet_name=sheet, header=None)
                df_sheet.to_excel(writer, sheet_name=sheet, header=False, index=False)
            except ValueError:
                continue


def create_run_dir(api_mode: str) -> Path:
    """Create a timestamped run directory under tests/accuracy/runs/{mode}/."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    mode_label = api_mode if api_mode in {"local", "cloud"} else "auto"
    run_dir = Path("tests/accuracy/runs") / mode_label / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_run_metadata(
    run_dir: Path,
    args: argparse.Namespace,
    results: list[EvaluationResult],
    run_start: datetime,
    run_end: datetime,
) -> None:
    """Write run_metadata.txt summarising the evaluation configuration and results."""
    evaluated = [r for r in results if r.is_correct is not None]
    answerable = [r for r in evaluated if r.should_answer is True]
    unanswerable = [r for r in evaluated if r.should_answer is False]
    answerable_correct = sum(1 for r in answerable if r.is_correct)
    unanswerable_correct = sum(1 for r in unanswerable if r.is_correct)
    overall = (
        (answerable_correct + unanswerable_correct) / len(evaluated)
        if evaluated
        else 0.0
    )

    api_modes = sorted({r.api_mode for r in results if r.api_mode})
    errors = sum(1 for r in results if r.error)

    # Try to read model info from config
    model_info = "unknown"
    provider_info = "unknown"
    try:
        from statschat import load_config

        cfg = load_config(name="main")
        search_cfg = cfg.get("search", {})
        provider_info = search_cfg.get("provider", "unknown")
        model_info = search_cfg.get("generative_model_name", "unknown")
        k_docs = search_cfg.get("k_docs", "unknown")
        k_contexts = search_cfg.get("k_contexts", "unknown")
        answer_threshold = search_cfg.get("answer_threshold", "unknown")
        document_threshold = search_cfg.get("document_threshold", "unknown")
    except Exception:
        k_docs = k_contexts = answer_threshold = document_threshold = "unknown"
        pass

    lines = [
        f"Run timestamp:      {run_start.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration:           {(run_end - run_start).total_seconds():.1f}s",
        f"API mode(s):        {', '.join(api_modes) if api_modes else 'n/a'}",
        f"Provider:           {provider_info}",
        f"Model:              {model_info}",
        f"API host:           {args.host}",
        f"QA file:            {args.excel}",
        f"Content type:       {args.content_type}",
        f"Timeout:            {args.timeout}s",
        f"Max rows:           {args.max_rows or 'all'}",
        f"Skip rows:          {args.skip_rows}",
        f"Retrieval k:        {args.retrieval_k}",
        f"k_docs:             {k_docs}",
        f"k_contexts:         {k_contexts}",
        f"Answer threshold:   {answer_threshold}",
        f"Document threshold: {document_threshold}",
        f"Similarity thresh:  {args.similarity_threshold}",
        f"F1 threshold:       {args.f1_threshold}",
        f"Semantic threshold: {args.semantic_threshold}",
        "",
        "--- Summary ---",
        f"Total evaluated:    {len(evaluated)}",
        f"Answerable:         {len(answerable)} ({answerable_correct} correct)",
        f"Unanswerable:       {len(unanswerable)} ({unanswerable_correct} correct)",
        f"Overall accuracy:   {overall:.3f}",
        f"Errors:             {errors}",
    ]

    f1_scores = [r.token_f1 for r in answerable if r.token_f1 is not None]
    sem_scores = [
        r.semantic_similarity for r in answerable if r.semantic_similarity is not None
    ]
    if f1_scores:
        lines.append(f"Avg Token F1:       {sum(f1_scores) / len(f1_scores):.3f}")
    if sem_scores:
        lines.append(f"Avg Semantic Sim:   {sum(sem_scores) / len(sem_scores):.3f}")

    output_path = run_dir / "run_metadata.txt"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_run_report(
    run_dir: Path,
    results: list[EvaluationResult],
    df: pd.DataFrame,
) -> None:
    """Write run_report.md — a human-readable comparison of each QA pair."""
    lines: list[str] = []
    lines.append("# Evaluation Run Report\n")

    # Summary metrics table
    evaluated = [r for r in results if r.is_correct is not None]
    answerable = [r for r in evaluated if r.should_answer is True]
    unanswerable = [r for r in evaluated if r.should_answer is False]
    correct = sum(1 for r in evaluated if r.is_correct)
    answerable_correct = sum(1 for r in answerable if r.is_correct)
    unanswerable_correct = sum(1 for r in unanswerable if r.is_correct)
    errors = sum(1 for r in results if r.error)
    overall_acc = correct / len(evaluated) if evaluated else 0.0
    answerable_acc = answerable_correct / len(answerable) if answerable else 0.0
    unanswerable_acc = unanswerable_correct / len(unanswerable) if unanswerable else 0.0

    em_scores = [r.exact_match for r in answerable if r.exact_match is not None]
    f1_scores = [r.token_f1 for r in answerable if r.token_f1 is not None]
    sem_scores = [
        r.semantic_similarity for r in answerable if r.semantic_similarity is not None
    ]
    retrieval = [
        r
        for r in evaluated
        if r.precision_at_k is not None and r.recall_at_k is not None
    ]

    avg_em = sum(em_scores) / len(em_scores) if em_scores else 0.0
    avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    avg_sem = sum(sem_scores) / len(sem_scores) if sem_scores else 0.0
    avg_prec = (
        sum(r.precision_at_k for r in retrieval) / len(retrieval) if retrieval else 0.0
    )
    avg_recall = (
        sum(r.recall_at_k for r in retrieval) / len(retrieval) if retrieval else 0.0
    )
    avg_mrr = (
        sum(r.mrr for r in retrieval if r.mrr is not None) / len(retrieval)
        if retrieval
        else 0.0
    )
    avg_ndcg = (
        sum(r.ndcg for r in retrieval if r.ndcg is not None) / len(retrieval)
        if retrieval
        else 0.0
    )

    api_modes = sorted({r.api_mode for r in results if r.api_mode})
    retrieval_sources = sorted(
        {r.retrieval_metric_source for r in results if r.retrieval_metric_source}
    )

    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total evaluated | {len(evaluated)} |")
    lines.append(f"| Answerable | {len(answerable)} |")
    lines.append(f"| Unanswerable | {len(unanswerable)} |")
    lines.append(f"| Errors | {errors} |")
    lines.append(f"| Overall accuracy | {overall_acc:.3f} |")
    lines.append(f"| Answerable accuracy | {answerable_acc:.3f} |")
    lines.append(f"| Unanswerable accuracy | {unanswerable_acc:.3f} |")
    lines.append(f"| Exact Match (EM) | {avg_em:.3f} |")
    lines.append(f"| Token F1 (avg) | {avg_f1:.3f} |")
    lines.append(f"| Semantic Similarity (avg) | {avg_sem:.3f} |")
    lines.append(f"| Precision@k (avg) | {avg_prec:.3f} |")
    lines.append(f"| Recall@k (avg) | {avg_recall:.3f} |")
    lines.append(f"| MRR (avg) | {avg_mrr:.3f} |")
    lines.append(f"| nDCG (avg) | {avg_ndcg:.3f} |")
    lines.append(f"| Safe response rate | {overall_acc:.3f} |")
    if api_modes:
        lines.append(f"| API mode(s) | {', '.join(api_modes)} |")
    if retrieval_sources:
        lines.append(f"| Retrieval source(s) | {', '.join(retrieval_sources)} |")
    lines.append("")

    for r in results:
        # Lookup source_text and evidence from original QA data
        row_match = df.loc[df["query_id"].astype(str).str.strip() == r.query_id]
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

        # Status marker
        if r.error:
            status = "ERROR"
        elif r.is_correct is True:
            status = "CORRECT"
        elif r.is_correct is False:
            status = "INCORRECT"
        else:
            status = "SKIPPED"

        lines.append("---\n")
        lines.append(f"## {r.query_id} — {status}\n")
        lines.append(f"**Question:** {r.query_text}\n")

        # Side-by-side answers
        lines.append("### Expected vs Actual\n")
        lines.append("| | Detail |")
        lines.append("|---|---|")
        lines.append(f"| **Golden answer** | {r.golden_answer} |")
        lines.append(f"| **Predicted answer** | {r.predicted_answer or '*(empty)*'} |")
        lines.append(f"| **Should answer** | {r.should_answer} |")
        lines.append(f"| **Is refusal** | {r.is_refusal} |")
        lines.append("")

        # Metrics
        metrics_parts: list[str] = []
        if r.exact_match is not None:
            metrics_parts.append(f"EM={r.exact_match}")
        if r.token_f1 is not None:
            metrics_parts.append(f"F1={r.token_f1:.3f}")
        if r.semantic_similarity is not None:
            metrics_parts.append(f"Semantic={r.semantic_similarity:.3f}")
        if r.similarity_score is not None:
            metrics_parts.append(f"Fuzzy={r.similarity_score:.1f}")
        if r.evidence_page_match is not None:
            metrics_parts.append(f"EvidenceMatch={r.evidence_page_match}")
        if metrics_parts:
            lines.append(f"**Metrics:** {' | '.join(metrics_parts)}\n")

        # References comparison
        lines.append("### References\n")
        lines.append("| | Detail |")
        lines.append("|---|---|")
        lines.append(f"| **Expected docs** | {relevant_doc_ids_raw or '*(none)*'} |")
        lines.append(f"| **Returned doc IDs** | {r.reference_doc_ids or '*(none)*'} |")
        lines.append(f"| **Expected evidence** | {evidence_locations or '*(none)*'} |")
        lines.append(f"| **Returned pages** | {r.reference_pages or '*(none)*'} |")
        if r.reference_titles:
            lines.append(
                f"| **Returned titles** | {r.reference_titles.replace(';', '; ')} |"
            )
        if r.reference_scores:
            lines.append(f"| **Retrieval scores** | {r.reference_scores} |")
        lines.append("")

        # Source text comparison
        if source_text:
            lines.append("### Expected Source Text\n")
            lines.append(
                f"> {source_text[:500]}{'...' if len(source_text) > 500 else ''}\n"
            )

        # StatsChat's reasoning / context
        has_debug = any(
            [
                r.reasoning,
                r.context_texts,
                r.highlighting,
                r.context_from,
                r.context_reference,
            ]
        )
        if has_debug:
            lines.append("### StatsChat Reasoning\n")
            if r.reasoning:
                lines.append(f"**Reasoning:** {r.reasoning}\n")
            if r.highlighting:
                lines.append(f"**Key phrases:** {r.highlighting}\n")
            if r.context_from:
                lines.append(f"**Context from:** {r.context_from}\n")
            if r.context_reference:
                lines.append(f"**Context reference:** {r.context_reference}\n")
            if r.relevant_publications:
                lines.append(f"**Relevant publications:** {r.relevant_publications}\n")
            if r.context_texts:
                lines.append("<details><summary>Retrieved context chunks</summary>\n")
                lines.append(f"```\n{r.context_texts[:2000]}\n```\n")
                lines.append("</details>\n")

        # Error
        if r.error:
            lines.append(f"**Error:** `{r.error}`\n")

        lines.append("")

    output_path = run_dir / "run_report.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_summary_metrics_csv(
    run_dir: Path,
    results: list[EvaluationResult],
) -> None:
    """Write summary_metrics.csv — a single-row CSV of aggregate metrics."""
    evaluated = [r for r in results if r.is_correct is not None]
    answerable = [r for r in evaluated if r.should_answer is True]
    unanswerable = [r for r in evaluated if r.should_answer is False]
    answerable_correct = sum(1 for r in answerable if r.is_correct)
    unanswerable_correct = sum(1 for r in unanswerable if r.is_correct)
    overall_correct = answerable_correct + unanswerable_correct
    errors = sum(1 for r in results if r.error)

    em_scores = [r.exact_match for r in answerable if r.exact_match is not None]
    f1_scores = [r.token_f1 for r in answerable if r.token_f1 is not None]
    sem_scores = [
        r.semantic_similarity for r in answerable if r.semantic_similarity is not None
    ]
    retrieval = [
        r
        for r in evaluated
        if r.precision_at_k is not None and r.recall_at_k is not None
    ]

    def _avg(vals: list) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    row = {
        "total_evaluated": len(evaluated),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "errors": errors,
        "overall_accuracy": (
            round(overall_correct / len(evaluated), 4) if evaluated else 0.0
        ),
        "answerable_accuracy": (
            round(answerable_correct / len(answerable), 4) if answerable else 0.0
        ),
        "unanswerable_accuracy": (
            round(unanswerable_correct / len(unanswerable), 4) if unanswerable else 0.0
        ),
        "exact_match_avg": round(_avg(em_scores), 4),
        "token_f1_avg": round(_avg(f1_scores), 4),
        "semantic_similarity_avg": round(_avg(sem_scores), 4),
        "precision_at_k_avg": round(_avg([r.precision_at_k for r in retrieval]), 4),
        "recall_at_k_avg": round(_avg([r.recall_at_k for r in retrieval]), 4),
        "mrr_avg": round(_avg([r.mrr for r in retrieval if r.mrr is not None]), 4),
        "ndcg_avg": round(_avg([r.ndcg for r in retrieval if r.ndcg is not None]), 4),
        "safe_response_rate": (
            round(overall_correct / len(evaluated), 4) if evaluated else 0.0
        ),
        "api_modes": ";".join(sorted({r.api_mode for r in results if r.api_mode})),
        "retrieval_sources": ";".join(
            sorted(
                {
                    r.retrieval_metric_source
                    for r in results
                    if r.retrieval_metric_source
                }
            )
        ),
    }

    output_path = run_dir / "summary_metrics.csv"
    pd.DataFrame([row]).to_csv(output_path, index=False)


def load_generation_metadata(excel_path: Path) -> dict[str, str]:
    try:
        df = pd.read_excel(excel_path, sheet_name="Generation_Metadata")
    except ValueError:
        return {}
    if "field" not in df.columns or "value" not in df.columns:
        return {}
    data: dict[str, str] = {}
    for _, row in df.iterrows():
        field_name = str(row.get("field", "")).strip()
        if not field_name:
            continue
        data[field_name] = str(row.get("value", "")).strip()
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


_PROVIDER_ENV_KEYS: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "huggingface_inference": "HF_TOKEN",
}


def _check_cloud_api_key() -> None:
    """Fail fast when required cloud API key is missing."""
    try:
        from statschat import load_config

        cfg = load_config(name="main")
        provider = cfg.get("search", {}).get("provider", "openrouter")
    except Exception:
        provider = "openrouter"

    env_var = _PROVIDER_ENV_KEYS.get(provider, "")
    if env_var and not os.environ.get(env_var):
        print(
            f"Cloud mode requires the {env_var} environment variable "
            f"(provider={provider}). Set it and retry.",
            file=sys.stderr,
        )
        sys.exit(1)


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.excel.exists():
        print(f"Excel file not found: {args.excel}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_excel(args.excel, sheet_name="QA_Data")
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

    if args.api_mode == "cloud":
        _check_cloud_api_key()

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
    )

    run_end = datetime.now()

    # Determine effective API mode for the run folder name
    effective_mode = args.api_mode
    if effective_mode == "auto":
        observed = {r.api_mode for r in results if r.api_mode}
        effective_mode = observed.pop() if len(observed) == 1 else "auto"

    run_dir = create_run_dir(effective_mode)

    # Save all outputs into the run folder
    results_path = run_dir / "accuracy_results.csv"
    save_results(results, results_path)
    print(f"Results saved to: {results_path}")

    if issues:
        issues_path = run_dir / "qa_data_issues.csv"
        save_issues(issues, issues_path)
        print(f"Data quality issues saved to: {issues_path}")

    if args.write_answers_excel:
        answers_path = run_dir / "StatsChat_QA_With_Answers.xlsx"
        save_results_excel(args.excel, results, answers_path)
        print(f"Excel with answers saved to: {answers_path}")

    save_run_metadata(run_dir, args, results, run_start, run_end)
    print(f"Run metadata saved to: {run_dir / 'run_metadata.txt'}")

    save_run_report(run_dir, results, df)
    print(f"Run report saved to: {run_dir / 'run_report.md'}")

    save_summary_metrics_csv(run_dir, results)
    print(f"Summary metrics saved to: {run_dir / 'summary_metrics.csv'}")

    print_summary(results)


if __name__ == "__main__":
    main()
