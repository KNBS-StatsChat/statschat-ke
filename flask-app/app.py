import logging
import os
import re
from datetime import datetime
from html import unescape
from typing import Any

import requests
from flask import Flask, render_template, request, session
from flask.logging import default_handler
from markupsafe import escape

# StatsChat API endpoint. Default to the cloud API demo port, but allow
# overrides so the same frontend can point at either local or cloud mode.
ENDPOINT = os.getenv("STATSCHAT_FRONTEND_API_URL", "http://127.0.0.1:8001/")
API_KEY = os.getenv("STATSCHAT_API_KEY")
REQUEST_TIMEOUT = float(os.getenv("STATSCHAT_FRONTEND_TIMEOUT", "120"))

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_app_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    # filename=f"log/{SESSION_NAME}.log",
    filemode="a",
)
logger.addHandler(default_handler)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"

DEMO_UNSUPPORTED_MESSAGE = (
    "I can only answer questions grounded in KNBS publications. "
    "I could not find a supported KNBS source for this question."
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
NUMBER_PATTERN = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
DEMO_CITATION_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "by",
        "for",
        "how",
        "in",
        "is",
        "kenya",
        "of",
        "on",
        "or",
        "the",
        "to",
        "total",
        "was",
        "were",
        "what",
    }
)


def plain_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", str(text or ""))
    normalised = unescape(without_tags)
    return re.sub(r"\s+", " ", normalised).strip()


def api_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def make_context_preview(text: str, limit: int = 420) -> str:
    collapsed = plain_text(text)
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def is_demo_unsupported_answer(answer: str) -> bool:
    normalised = str(answer or "").strip().lower()
    if not normalised:
        return True
    return normalised.startswith("no suitable pdfs found for this question")


def extract_debug_highlight_phrases(payload: dict[str, Any]) -> list[str]:
    debug_response = payload.get("debug_response", {}) or {}
    phrases: list[str] = []
    rendered_answer = plain_text(str(payload.get("answer", "")))
    if rendered_answer:
        phrases.append(rendered_answer)
    most_likely_answer = plain_text(str(debug_response.get("most_likely_answer", "")))
    if most_likely_answer:
        phrases.append(most_likely_answer)
    for key in ("highlighting1", "highlighting2", "highlighting3"):
        value = debug_response.get(key)
        if isinstance(value, list):
            phrases.extend(
                plain_text(str(item)) for item in value if plain_text(str(item))
            )

    deduped: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        normalised = plain_text(phrase).lower()
        if normalised in seen:
            continue
        seen.add(normalised)
        deduped.append(phrase)
    if not deduped:
        return []
    prioritized = [deduped[0]]
    prioritized.extend(
        sorted(
            deduped[1:],
            key=lambda phrase: (bool(re.search(r"\d", phrase)), len(phrase)),
            reverse=True,
        )
    )
    return prioritized


def numeric_tokens(text: str) -> set[str]:
    return {
        token.replace(",", "")
        for token in NUMBER_PATTERN.findall(plain_text(text))
        if token.strip()
    }


def content_tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(plain_text(text).lower())
        if len(token) > 2 and token not in DEMO_CITATION_STOPWORDS
    }


def best_reference_source_match(
    references: list[dict[str, Any]], phrases: list[str]
) -> tuple[dict[str, str] | None, int, dict[str, str] | None, int]:
    prepared_references = [
        (
            reference,
            plain_text(str(reference.get("page_content") or "")).lower(),
            numeric_tokens(str(reference.get("page_content") or "")),
            content_tokens(str(reference.get("page_content") or "")),
        )
        for reference in references
    ]

    best_match: dict[str, str] | None = None
    best_score = -1
    first_strong_match: dict[str, str] | None = None
    first_strong_score = -1

    for phrase in phrases:
        normalized_phrase = plain_text(phrase).lower()
        if not normalized_phrase:
            continue
        phrase_numbers = numeric_tokens(phrase)
        phrase_terms = content_tokens(phrase)

        for (
            reference,
            lowered_page_content,
            reference_numbers,
            reference_terms,
        ) in prepared_references:
            score = -1
            if normalized_phrase in lowered_page_content:
                score = 1000 + len(normalized_phrase)
            else:
                numbers_match = bool(phrase_numbers) and phrase_numbers.issubset(
                    reference_numbers
                )
                term_overlap = len(phrase_terms & reference_terms)
                if numbers_match and term_overlap >= 2:
                    score = 500 + (50 * len(phrase_numbers)) + (10 * term_overlap)
                elif not phrase_numbers and term_overlap >= max(
                    3, min(5, len(phrase_terms))
                ):
                    score = 200 + (10 * term_overlap)

            if score <= best_score:
                continue

            title = str(
                reference.get("title")
                or reference.get("reference_doc_id")
                or "Reference"
            ).strip()
            page_number = str(reference.get("page_number") or "").strip()
            source_label = title
            if page_number:
                source_label = f"{title}, page {page_number}"

            candidate_match = {
                "label": source_label,
                "url": str(reference.get("page_url") or reference.get("url") or ""),
                "quote": phrase,
            }
            if first_strong_match is None and score >= 500:
                first_strong_match = candidate_match
                first_strong_score = score

            best_score = score
            best_match = candidate_match

    return best_match, best_score, first_strong_match, first_strong_score


def infer_exact_cited_source(
    references: list[dict[str, Any]], payload: dict[str, Any]
) -> dict[str, str] | None:
    debug_response = payload.get("debug_response", {}) or {}
    phrases = extract_debug_highlight_phrases(payload)
    (
        best_reference_match,
        best_reference_score,
        first_strong_reference_match,
        first_strong_reference_score,
    ) = best_reference_source_match(references, phrases)
    if first_strong_reference_match and first_strong_reference_score >= 500:
        return first_strong_reference_match

    exact_cited_source = debug_response.get("exact_cited_source")
    if isinstance(exact_cited_source, dict) and exact_cited_source.get("label"):
        return {
            "label": str(exact_cited_source.get("label", "")).strip(),
            "url": str(exact_cited_source.get("page_url", "")).strip(),
            "quote": str(exact_cited_source.get("quote", "")).strip(),
        }

    if not references or not phrases:
        return None

    return best_reference_match


def extract_generation_context_sources(
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    debug_response = payload.get("debug_response", {}) or {}
    raw_sources = debug_response.get("generation_context_sources")
    if not isinstance(raw_sources, list):
        return []

    sources: list[dict[str, str]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        label = str(source.get("label", "")).strip()
        if not label:
            continue
        sources.append(
            {
                "label": label,
                "url": str(source.get("page_url", "")).strip(),
            }
        )
    return sources


def normalise_references(payload: dict[str, Any]) -> list[dict[str, Any]]:
    references = payload.get("references", [])
    if isinstance(references, str) and references.strip():
        references = [
            {
                "title": payload.get("question", "Reference"),
                "page_url": references,
                "url": references,
                "page_content": payload.get("answer", ""),
            }
        ]
    if not isinstance(references, list):
        return []

    deduped_references: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw_reference in references:
        if not isinstance(raw_reference, dict):
            continue

        reference = dict(raw_reference)
        page_content = str(reference.get("page_content") or "")
        reference["context_preview"] = make_context_preview(page_content)

        dedupe_key = (
            str(reference.get("title") or reference.get("reference_doc_id") or "")
            .strip()
            .lower(),
            str(reference.get("page_number") or "").strip(),
            str(reference.get("page_url") or reference.get("url") or "")
            .strip()
            .lower(),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_references.append(reference)

    return deduped_references


@app.route("/")
def home():
    session["latest_filter"] = request.args.get("latest_filter", "on")
    return render_template(
        "statschat.html", latest_filter=session["latest_filter"], question=""
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    session["question"] = escape(request.args.get("q", "")).strip()
    session["latest_filter"] = request.args.get("latest_filter", "on")
    if session["latest_filter"] in ["on", "On", "True", "true", True, "latest"]:
        session["content_type"] = "latest"
    else:
        session["content_type"] = "all"

    if session["question"]:
        try:
            response = requests.get(
                url=ENDPOINT.rstrip("/") + "/search",
                params={
                    "q": session["question"],
                    "content_type": session["content_type"],
                },
                headers=api_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if response.ok:
                payload = response.json()
                session["answer"] = payload.get("answer", "")
                docs = normalise_references(payload)
                exact_cited_source = infer_exact_cited_source(docs, payload)
                generation_context_sources = extract_generation_context_sources(payload)
                is_demo_refusal = is_demo_unsupported_answer(session["answer"])
                display_answer = (
                    DEMO_UNSUPPORTED_MESSAGE if is_demo_refusal else session["answer"]
                )
                response_time_seconds = payload.get("response_time_seconds")
                timing_label = (
                    "Backend response time"
                    if response_time_seconds is not None
                    else None
                )
                logger.info(
                    f"""QAPAIR: {
                    {"question": session["question"],
            "content_type": session["content_type"],
            "response": payload}}"""
                )
            else:
                session["answer"] = f"Connection to API failed: {response.status_code}"
                docs = []
                exact_cited_source = None
                generation_context_sources = []
                is_demo_refusal = False
                display_answer = session["answer"]
                response_time_seconds = None
                timing_label = None
                logger.warning(
                    f"""API-FAIL: {
                    {"question": session["question"],
            "content_type": session["content_type"],
            "response": response.status_code}}"""
                )
        except requests.exceptions.RequestException as e:
            session["answer"] = f"Connection to API failed: {e}"
            docs = []
            exact_cited_source = None
            generation_context_sources = []
            is_demo_refusal = False
            display_answer = session["answer"]
            response_time_seconds = None
            timing_label = None
            logger.warning(
                f"""API-FAIL: {
                {"question": session["question"],
                 "content_type": session["content_type"],
                 "response": e}}"""
            )
        results = {
            "answer": session["answer"],
            "display_answer": display_answer,
            "references": docs,
            "exact_cited_source": exact_cited_source,
            "generation_context_sources": generation_context_sources,
            "is_demo_refusal": is_demo_refusal,
            "request_duration_seconds": response_time_seconds,
            "request_duration_label": timing_label,
        }

    else:
        results = {}

    return render_template(
        "statschat.html",
        latest_filter=session["latest_filter"],
        question=session["question"],
        results=results,
    )


@app.route("/record_rating", methods=["POST"])
def record_rating():
    rating = request.form["rating"]
    last_answer = {
        "rating": rating,
        "rating_comment": request.form["comment"],
        "question": session["question"],
        "content_type": session["content_type"],
        "answer": session["answer"],
    }
    requests.post(
        ENDPOINT.rstrip("/") + "/feedback",
        json=last_answer,
        headers=api_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    logger.info(f"FEEDBACK: {last_answer}")
    return "", 204  # Return empty response with status code 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
