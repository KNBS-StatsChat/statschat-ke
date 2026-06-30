#!/usr/bin/env python3
"""Generate QA pairs with references from StatsChat JSON conversions.

This script creates a synthetic "silver" QA dataset in the same schema used by
the manual KNBS authoring template, so it can be consumed directly by
``evaluate_accuracy.py``.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import random
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import pandas as pd
from langchain_openai import ChatOpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
QUOTE_EXTRACT_RE = re.compile(r"[\"“”]([^\"“”]+)[\"“”]")
NUMBER_PATTERN = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
TIME_ANCHOR_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b|\bq[1-4]\b|"
    r"\b(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b",
    re.IGNORECASE,
)
LOCATION_ANCHOR_PATTERN = re.compile(
    r"\b(?:county|sub-county|subcounty|district|ward|"
    r"in\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
)
DISALLOWED_QUESTION_PATTERN = re.compile(
    r"\b(?:definition|define|methodology|explain|why|"
    r"according to the knbs|in the context of)\b",
    re.IGNORECASE,
)
DISALLOWED_ANSWER_PATTERN = re.compile(
    r"\b(?:not explicitly mentioned|not available|not provided|"
    r"no suitable answer|unknown|cannot be determined)\b",
    re.IGNORECASE,
)
BOILERPLATE_QUESTION_PATTERN = re.compile(
    r"^(?:what|which)\s+(?:organization|institution|agency|bureau)\b|"
    r"^(?:who)\s+(?:released|issued|published)\b|"
    r"^what\s+does\b.+\b(?:measure|mean)\b",
    re.IGNORECASE,
)
BOILERPLATE_SOURCE_PATTERN = re.compile(
    r"(?:iso\s*9001:2015\s+certified|"
    r"hereby\s+releases\s+consumer\s+price\s+indices|"
    r"\bterms\s+of\s+trade\b|"
    r"\brepublic\s+of\s+kenya\b|"
    r"\bkenya\s+national\s+bureau\s+of\s+statistics\s+is\s+iso\s+9001:2015\s+certified\b)",
    re.IGNORECASE,
)
BOILERPLATE_ANSWER_PATTERN = re.compile(
    r"^(?:kenya\s+national\s+bureau\s+of\s+statistics|knbs)$",
    re.IGNORECASE,
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "what",
    "when",
    "which",
    "who",
    "with",
}


@dataclass
class PageContext:
    doc_id: str
    page_number: int
    page_text: str


@dataclass
class GeneratedQA:
    query_text: str
    golden_answer: str
    source_text: str


def extract_doc_id(json_path: Path, pdf_url: str | None) -> str:
    if pdf_url:
        return Path(pdf_url.split("?")[0]).name
    return f"{json_path.stem}.pdf"


def iter_pages(json_path: Path) -> Iterable[PageContext]:
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    pdf_url = payload.get("url")
    doc_id = extract_doc_id(json_path, pdf_url)
    for page in payload.get("content", []):
        page_text = str(page.get("page_text", "")).strip()
        page_number = int(page.get("page_number", 0))
        if page_text and page_number:
            yield PageContext(
                doc_id=doc_id, page_number=page_number, page_text=page_text
            )


def trim_passage(text: str, max_sentences: int = 3) -> str:
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    if not sentences:
        return text.strip()
    return " ".join(sentences[:max_sentences])


def collapse_ws(text: str) -> str:
    return " ".join(text.split())


def normalize_for_substring(text: str) -> str:
    cleaned = text.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace('"', " ").strip()
    return collapse_ws(cleaned).lower()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def extract_numbers(text: str) -> list[str]:
    return [match.replace(",", "") for match in NUMBER_PATTERN.findall(text)]


def normalize_source_text(text: str) -> str:
    normalized = collapse_ws(text.strip())
    if not normalized:
        return normalized

    quoted = [
        collapse_ws(match.strip())
        for match in QUOTE_EXTRACT_RE.findall(normalized)
        if match.strip()
    ]
    if quoted:
        quoted = quoted[:3]
        return " ".join(f'"{part}"' for part in quoted)

    sentences = split_sentences(normalized)[:3]
    if not sentences:
        return f'"{normalized}"'
    return " ".join(f'"{sentence}"' for sentence in sentences)


def source_is_grounded(source_text: str, page_text: str) -> bool:
    source_norm = normalize_for_substring(source_text)
    page_norm = normalize_for_substring(page_text)
    if not source_norm or not page_norm:
        return False
    return source_norm in page_norm


def fallback_source_from_page(page_text: str, answer: str) -> Optional[str]:
    page_sentences = split_sentences(page_text)
    if not page_sentences:
        return None

    answer_norm = normalize_for_substring(answer)
    if not answer_norm:
        return None

    matched: list[str] = []
    for sentence in page_sentences:
        sentence_norm = normalize_for_substring(sentence)
        if answer_norm in sentence_norm:
            matched.append(collapse_ws(sentence))
            if len(matched) == 3:
                break

    if not matched:
        answer_tokens = [token for token in re.split(r"\W+", answer_norm) if token]
        if not answer_tokens:
            return None
        scored: list[tuple[int, str]] = []
        for sentence in page_sentences:
            sentence_norm = normalize_for_substring(sentence)
            overlap = sum(1 for token in answer_tokens if token in sentence_norm)
            if overlap > 0:
                scored.append((overlap, collapse_ws(sentence)))
        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        matched = [text for _, text in scored[:3]]

    return " ".join(f'"{sentence}"' for sentence in matched if sentence)


def parse_llm_json(content: str) -> Optional[dict[str, Any]]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = JSON_BLOCK_RE.search(text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def build_prompt(context: PageContext) -> str:
    passage = trim_passage(context.page_text, max_sentences=3)
    return (
        "You are creating a QA dataset grounded in a passage from an official KNBS PDF. "
        "Generate ONE question and ONE short factual answer that is explicitly supported by the passage. "
        "Return ONLY a JSON object with keys: query_text, golden_answer, source_text. "
        "Rules:"
        "- query_text is a natural language question."
        "- golden_answer is concise and should appear in the passage."
        "- source_text is 1-3 sentences quoted verbatim from the passage."
        "- Prefer distinctive factual questions with a clear time, location, quantity, or named programme anchor."
        "- Avoid definitions, headings, cover-page boilerplate, certifications, release notices, or facts repeated across many PDFs."
        "- Avoid generic questions like 'What organization...' or 'Who released...'."
        "- Return valid JSON only. Do not include markdown fences."
        "Passage:\n"
        f"{passage}"
    )


def generate_qa(
    llm: ChatOpenAI,
    context: PageContext,
) -> Optional[GeneratedQA]:
    prompt = build_prompt(context)
    response = llm.invoke(prompt)
    data = parse_llm_json(str(response.content))
    if not data:
        return None

    query_text = str(data.get("query_text", "")).strip()
    golden_answer = str(data.get("golden_answer", "")).strip()
    source_text = normalize_source_text(str(data.get("source_text", "")).strip())
    if not query_text or not golden_answer or not source_text:
        return None

    return GeneratedQA(
        query_text=query_text,
        golden_answer=golden_answer,
        source_text=source_text,
    )


def build_local_generator(
    model_id: str,
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16,
        device_map="auto",
    )
    return model, tokenizer


def generate_qa_local(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    context: PageContext,
    max_new_tokens: int = 300,
) -> Optional[GeneratedQA]:
    prompt = build_prompt(context)
    encoded = tokenizer(prompt, return_tensors="pt")
    input_ids = encoded.input_ids.to(model.device)
    attention_mask = encoded.attention_mask.to(model.device)
    output = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    response_text = tokenizer.decode(output[0], skip_special_tokens=True)
    # Strip echoed prompt if present.
    if response_text.startswith(prompt):
        response_text = response_text[len(prompt) :].strip()
    data = parse_llm_json(response_text)
    if not data:
        return None

    query_text = str(data.get("query_text", "")).strip()
    golden_answer = str(data.get("golden_answer", "")).strip()
    source_text = normalize_source_text(str(data.get("source_text", "")).strip())
    if not query_text or not golden_answer or not source_text:
        return None

    return GeneratedQA(
        query_text=query_text,
        golden_answer=golden_answer,
        source_text=source_text,
    )


def select_json_files(json_dir: Path, max_docs: int, seed: int) -> list[Path]:
    json_files = sorted(json_dir.glob("*.json"))
    if not json_files:
        return []
    rng = random.Random(seed)
    rng.shuffle(json_files)
    if max_docs > 0:
        return json_files[:max_docs]
    return json_files


def load_index_pdf_names(index_pkl: Path) -> set[str]:
    with index_pkl.open("rb") as handle:
        store, _ = pickle.load(handle)

    pdf_names: set[str] = set()
    for doc in store._dict.values():
        page_url = str(doc.metadata.get("page_url", "")).strip()
        url = str(doc.metadata.get("url", "")).strip()
        candidate = page_url or url
        if not candidate:
            continue
        parsed = urlparse(candidate)
        name = Path(parsed.path).name
        if name:
            pdf_names.add(name)
    return pdf_names


def filter_json_files_to_index(json_files: list[Path], index_pkl: Path) -> list[Path]:
    if not index_pkl.exists():
        raise FileNotFoundError(f"Index metadata not found: {index_pkl}")

    indexed_pdf_names = load_index_pdf_names(index_pkl)
    filtered: list[Path] = []
    for json_path in json_files:
        try:
            with json_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            continue

        pdf_url = str(payload.get("url", "")).strip()
        pdf_name = (
            Path(urlparse(pdf_url).path).name if pdf_url else f"{json_path.stem}.pdf"
        )
        if pdf_name in indexed_pdf_names:
            filtered.append(json_path)

    return filtered


def is_reasonable_question(text: str) -> bool:
    clean = text.strip()
    return clean.endswith("?") and len(clean) >= 12 and len(clean.split()) >= 4


def has_specific_anchor(question: str) -> bool:
    return bool(
        TIME_ANCHOR_PATTERN.search(question) or LOCATION_ANCHOR_PATTERN.search(question)
    )


def is_disallowed_question_style(question: str) -> bool:
    return bool(DISALLOWED_QUESTION_PATTERN.search(question))


def has_disallowed_answer_text(answer: str) -> bool:
    return bool(DISALLOWED_ANSWER_PATTERN.search(answer))


def is_boilerplate_question(question: str) -> bool:
    return bool(BOILERPLATE_QUESTION_PATTERN.search(question.strip()))


def is_boilerplate_source_text(source_text: str) -> bool:
    normalized = collapse_ws(source_text.replace('"', " "))
    return bool(BOILERPLATE_SOURCE_PATTERN.search(normalized))


def is_boilerplate_answer(answer: str) -> bool:
    return bool(BOILERPLATE_ANSWER_PATTERN.search(answer.strip()))


def answer_is_exact_span(answer: str, source_text: str) -> bool:
    answer_norm = normalize_for_substring(answer)
    source_norm = normalize_for_substring(source_text)
    if not answer_norm or not source_norm:
        return False
    return answer_norm in source_norm


def query_source_overlap_count(query: str, source_text: str) -> int:
    query_tokens = [
        token
        for token in re.findall(r"[A-Za-z0-9]+", query.lower())
        if token not in STOPWORDS and len(token) > 2
    ]
    source_tokens = set(re.findall(r"[A-Za-z0-9]+", source_text.lower()))
    return sum(1 for token in set(query_tokens) if token in source_tokens)


def source_is_table_like(source_text: str) -> bool:
    source_clean = collapse_ws(source_text.replace('"', " "))
    if len(source_clean) < 120:
        return False
    tokens = [token for token in source_clean.split(" ") if token]
    if not tokens:
        return False
    numeric_tokens = [
        token for token in tokens if re.fullmatch(r"\d+(?:[.,]\d+)?%?", token)
    ]
    numeric_ratio = len(numeric_tokens) / len(tokens)
    return numeric_ratio >= 0.30 or len(extract_numbers(source_clean)) >= 12


def contains_answer_in_source(answer: str, source_text: str) -> bool:
    answer_norm = answer.lower().strip()
    source_norm = source_text.lower().replace('"', " ").strip()
    if answer_norm in source_norm:
        return True
    answer_words = [w for w in re.split(r"\W+", answer_norm) if w]
    if not answer_words:
        return False
    overlap = sum(1 for word in answer_words if word in source_norm)
    return (overlap / len(answer_words)) >= 0.7


def build_row(query_id: str, context: PageContext, qa: GeneratedQA) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "query_text": qa.query_text,
        "golden_answer": qa.golden_answer,
        "relevant_doc_ids": context.doc_id,
        "evidence_locations": f"{context.doc_id}:p.{context.page_number}",
        "source_text": qa.source_text,
        "should_answer": True,
        "Reviewers": "",
    }


def qa_columns() -> list[str]:
    return [
        "query_id",
        "query_text",
        "golden_answer",
        "relevant_doc_ids",
        "evidence_locations",
        "source_text",
        "should_answer",
        "Reviewers",
    ]


def build_qa_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=qa_columns())
    df = pd.DataFrame(rows)
    return df[qa_columns()]


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_questions: set[str] = set()
    seen_answer_source_pairs: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        question_key = re.sub(r"\s+", " ", str(row["query_text"]).strip().lower())
        answer_source_key = " || ".join(
            [
                normalize_for_substring(str(row["golden_answer"])),
                normalize_for_substring(str(row["source_text"])),
            ]
        )
        if (
            question_key in seen_questions
            or answer_source_key in seen_answer_source_pairs
        ):
            continue
        seen_questions.add(question_key)
        seen_answer_source_pairs.add(answer_source_key)
        deduped.append(row)
    return deduped


def qa_is_valid(
    qa: GeneratedQA,
    context: PageContext,
    strict_filters: bool,
    max_source_length: int,
    max_source_numbers: int,
    min_query_source_overlap: int,
) -> bool:
    if not is_reasonable_question(qa.query_text):
        return False
    if is_disallowed_question_style(qa.query_text):
        return False
    if is_boilerplate_question(qa.query_text):
        return False
    if len(qa.golden_answer.strip()) < 1:
        return False
    if len(qa.golden_answer.strip()) > 120:
        return False
    if has_disallowed_answer_text(qa.golden_answer):
        return False
    if is_boilerplate_answer(qa.golden_answer):
        return False
    if len(qa.source_text.strip()) < 20:
        return False
    if max_source_length > 0 and len(collapse_ws(qa.source_text)) > max_source_length:
        return False
    if is_boilerplate_source_text(qa.source_text):
        return False
    if not source_is_grounded(qa.source_text, context.page_text):
        return False
    if not answer_is_exact_span(qa.golden_answer, qa.source_text):
        return False
    if not contains_answer_in_source(qa.golden_answer, qa.source_text):
        return False
    if (
        query_source_overlap_count(qa.query_text, qa.source_text)
        < min_query_source_overlap
    ):
        return False

    answer_numbers = extract_numbers(qa.golden_answer)
    source_numbers = extract_numbers(qa.source_text)
    if answer_numbers:
        if strict_filters and not has_specific_anchor(qa.query_text):
            return False
        if max_source_numbers > 0 and len(source_numbers) > max_source_numbers:
            return False
        for number in answer_numbers:
            if source_numbers.count(number) != 1:
                return False
        if strict_filters and source_is_table_like(qa.source_text):
            return False

    return True


def load_template_sheets(template_path: Path) -> dict[str, pd.DataFrame]:
    sheets: dict[str, pd.DataFrame] = {}
    for sheet in ["Instructions", "Explanation"]:
        try:
            sheets[sheet] = pd.read_excel(template_path, sheet_name=sheet, header=None)
        except ValueError:
            continue
    return sheets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate QA pairs with references.")
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=Path("data/json_conversions"),
        help="Directory containing PDF JSON conversions",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("tests/accuracy/StatsChat_QA_Template_2.xlsx"),
        help="Template Excel for Instructions/Explanation sheets",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/accuracy/StatsChat_QA_Auto.xlsx"),
        help="Output Excel path",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Max PDFs to sample (0 means all)",
    )
    parser.add_argument("--pages-per-doc", type=int, default=3, help="Pages per PDF")
    parser.add_argument(
        "--max-questions",
        type=int,
        default=50,
        help="Max generated rows to keep (after filtering/dedup)",
    )
    parser.add_argument(
        "--min-text-length",
        type=int,
        default=200,
        help="Minimum page_text length to include",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument(
        "--provider",
        type=str,
        default="local",
        choices=["local", "openai"],
        help="Generation provider",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.3",
        help="Model ID (local HF model or OpenAI model)",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.2, help="LLM temperature"
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=300,
        help="Max new tokens for local generation",
    )
    parser.add_argument(
        "--query-id-prefix",
        type=str,
        default="Q",
        help="Prefix for generated query IDs (recommended: Q)",
    )
    parser.add_argument(
        "--reviewers-value",
        type=str,
        default="",
        help="Optional value for Reviewers column (leave blank for AI-generated rows)",
    )
    parser.add_argument(
        "--strict-filters",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable stricter QA filters for stable evaluation conditions",
    )
    parser.add_argument(
        "--max-source-length",
        type=int,
        default=380,
        help="Maximum normalized source_text length; longer sources are skipped",
    )
    parser.add_argument(
        "--max-source-numbers",
        type=int,
        default=10,
        help="Maximum count of numbers allowed in source_text for numeric answers",
    )
    parser.add_argument(
        "--min-query-source-overlap",
        type=int,
        default=2,
        help="Minimum overlap count between question keywords and source_text",
    )
    parser.add_argument(
        "--align-with-index",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Restrict candidate JSON files to PDFs present in the current FAISS index.",
    )
    parser.add_argument(
        "--index-pkl",
        type=Path,
        default=Path("data/db_langchain/index.pkl"),
        help="Path to the FAISS metadata pickle used for corpus alignment.",
    )
    return parser.parse_args()


def build_metadata_rows(args: argparse.Namespace) -> pd.DataFrame:
    rows: list[dict[str, str]] = [
        {
            "field": "generated_at_utc",
            "value": datetime.utcnow().isoformat(timespec="seconds"),
        },
        {"field": "provider", "value": str(args.provider)},
        {"field": "model", "value": str(args.model)},
        {"field": "json_dir", "value": str(args.json_dir)},
        {"field": "seed", "value": str(args.seed)},
        {"field": "max_files", "value": str(args.max_files)},
        {"field": "pages_per_doc", "value": str(args.pages_per_doc)},
        {"field": "max_questions", "value": str(args.max_questions)},
        {"field": "min_text_length", "value": str(args.min_text_length)},
        {"field": "max_new_tokens", "value": str(args.max_new_tokens)},
        {"field": "query_id_prefix", "value": str(args.query_id_prefix)},
        {"field": "strict_filters", "value": str(args.strict_filters)},
        {"field": "max_source_length", "value": str(args.max_source_length)},
        {"field": "max_source_numbers", "value": str(args.max_source_numbers)},
        {
            "field": "min_query_source_overlap",
            "value": str(args.min_query_source_overlap),
        },
        {"field": "align_with_index", "value": str(args.align_with_index)},
        {"field": "index_pkl", "value": str(args.index_pkl)},
    ]

    try:
        from statschat import load_config

        cfg = load_config(name="main")
        search_cfg = cfg.get("search", {})
        rows.extend(
            [
                {"field": "eval.k_docs", "value": str(search_cfg.get("k_docs", ""))},
                {
                    "field": "eval.k_contexts",
                    "value": str(search_cfg.get("k_contexts", "")),
                },
                {
                    "field": "eval.similarity_threshold",
                    "value": str(search_cfg.get("similarity_threshold", "")),
                },
                {
                    "field": "eval.answer_threshold",
                    "value": str(search_cfg.get("answer_threshold", "")),
                },
                {
                    "field": "eval.document_threshold",
                    "value": str(search_cfg.get("document_threshold", "")),
                },
            ]
        )
    except Exception:
        rows.append({"field": "eval_config", "value": "unavailable"})

    return pd.DataFrame(rows, columns=["field", "value"])


def main() -> None:
    args = parse_args()

    if not args.json_dir.exists():
        raise SystemExit(f"JSON dir not found: {args.json_dir}")

    if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required when --provider openai.")

    random.seed(args.seed)
    json_files = select_json_files(
        args.json_dir, max_docs=args.max_files, seed=args.seed
    )
    selected_before_alignment = len(json_files)
    if args.align_with_index:
        json_files = filter_json_files_to_index(json_files, args.index_pkl)
        print(
            "Aligned candidate JSONs to current index: "
            f"{len(json_files)}/{selected_before_alignment} files retained"
        )

    llm: Optional[ChatOpenAI] = None
    local_model: Optional[AutoModelForCausalLM] = None
    local_tokenizer: Optional[AutoTokenizer] = None
    if args.provider == "openai":
        llm = ChatOpenAI(model=args.model, temperature=args.temperature)
    else:
        local_model, local_tokenizer = build_local_generator(args.model)

    rows: list[dict] = []
    query_idx = 1

    for json_path in json_files:
        pages = [
            p for p in iter_pages(json_path) if len(p.page_text) >= args.min_text_length
        ]
        if not pages:
            continue
        sample_pages = random.sample(pages, k=min(args.pages_per_doc, len(pages)))
        for page in sample_pages:
            if args.provider == "openai":
                if llm is None:
                    continue
                qa = generate_qa(llm, page)
            else:
                if local_model is None or local_tokenizer is None:
                    continue
                qa = generate_qa_local(
                    local_model,
                    local_tokenizer,
                    page,
                    max_new_tokens=args.max_new_tokens,
                )
            if not qa:
                continue
            if not source_is_grounded(qa.source_text, page.page_text):
                repaired = fallback_source_from_page(page.page_text, qa.golden_answer)
                if repaired:
                    qa = GeneratedQA(
                        query_text=qa.query_text,
                        golden_answer=qa.golden_answer,
                        source_text=repaired,
                    )
            if not qa_is_valid(
                qa,
                page,
                strict_filters=bool(args.strict_filters),
                max_source_length=int(args.max_source_length),
                max_source_numbers=int(args.max_source_numbers),
                min_query_source_overlap=int(args.min_query_source_overlap),
            ):
                continue
            query_id = f"{args.query_id_prefix.upper()}{query_idx:03d}"
            query_idx += 1
            row = build_row(query_id=query_id, context=page, qa=qa)
            row["Reviewers"] = args.reviewers_value
            rows.append(row)

    rows = dedupe_rows(rows)
    if args.max_questions and args.max_questions > 0:
        rows = rows[: args.max_questions]

    # Reindex query IDs after filtering to keep them contiguous.
    for idx, row in enumerate(rows, start=1):
        row["query_id"] = f"{args.query_id_prefix.upper()}{idx:03d}"

    qa_df = build_qa_dataframe(rows)
    metadata_df = build_metadata_rows(args)

    sheets = load_template_sheets(args.template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        qa_df.to_excel(writer, sheet_name="QA_Data", index=False)
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, header=False, index=False)
        metadata_df.to_excel(writer, sheet_name="Generation_Metadata", index=False)

    print(f"Generated {len(rows)} QA rows -> {args.output}")


if __name__ == "__main__":
    main()
