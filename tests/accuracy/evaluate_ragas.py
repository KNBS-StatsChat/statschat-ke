#!/usr/bin/env python3
"""Evaluate saved StatsChat runs with deterministic evidence-span diagnostics."""
from __future__ import annotations

import argparse
import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from rapidfuzz import fuzz

REQUIRED_QA_COLUMNS = {
    "query_id",
    "query_text",
    "golden_answer",
    "source_text",
    "should_answer",
}

DEFAULT_EXCEL = Path("tests/accuracy/StatsChat_QA_Verified_Audited.xlsx")
CONTEXT_DELIMITER = "\n---\n"
DEFAULT_FUZZY_THRESHOLD = 85.0


@dataclass
class SpanRecallRow:
    query_id: str
    query_text: str
    golden_answer: str
    predicted_answer: str
    source_text: str
    retrieved_contexts: list[str]
    span_exact_hit: Optional[bool]
    span_fuzzy_hit: Optional[bool]
    span_hit: Optional[bool]
    span_best_partial_ratio: Optional[float]
    span_eval_eligible: bool
    span_skip_reason: Optional[str]


def detect_qa_sheet_name(
    excel_path: Path, preferred_sheet: str = "QA_Data"
) -> tuple[str, list[str]]:
    """Return the worksheet containing the QA table and all sheet names."""
    workbook = pd.ExcelFile(excel_path)
    sheet_names = workbook.sheet_names

    if preferred_sheet in sheet_names:
        header_df = pd.read_excel(excel_path, sheet_name=preferred_sheet, nrows=0)
        columns = {str(col).strip() for col in header_df.columns}
        if REQUIRED_QA_COLUMNS.issubset(columns):
            return preferred_sheet, sheet_names

    matching_sheets: list[str] = []
    for sheet_name in sheet_names:
        header_df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=0)
        columns = {str(col).strip() for col in header_df.columns}
        if REQUIRED_QA_COLUMNS.issubset(columns):
            matching_sheets.append(sheet_name)

    if not matching_sheets:
        raise ValueError(
            "No worksheet contains the required QA columns. "
            f"Required columns: {sorted(REQUIRED_QA_COLUMNS)}"
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
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1 or value == 1.0:
            return True
        if value == 0 or value == 0.0:
            return False
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0"}:
        return False
    return None


def split_context_texts(context_texts: object) -> list[str]:
    """Split evaluator context blocks into retrieved chunks."""
    if is_blank(context_texts):
        return []
    return [
        part.strip()
        for part in str(context_texts).split(CONTEXT_DELIMITER)
        if part.strip()
    ]


def normalize_span_text(text: str) -> str:
    """Normalize evidence text for deterministic containment checks."""
    normalized = str(text).lower().strip()
    normalized = normalized.translate(str.maketrans("", "", string.punctuation))
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def compute_span_match(
    source_text: str,
    retrieved_contexts: list[str],
    *,
    fuzzy_threshold: float,
) -> tuple[bool, bool, bool, float]:
    """Compare audited evidence span against retrieved chunks."""
    normalized_source = normalize_span_text(source_text)
    normalized_contexts = [
        normalize_span_text(context)
        for context in retrieved_contexts
        if normalize_span_text(context)
    ]

    if not normalized_source or not normalized_contexts:
        return False, False, False, 0.0

    exact_hit = any(normalized_source in context for context in normalized_contexts)
    best_partial_ratio = max(
        float(fuzz.partial_ratio(normalized_source, context))
        for context in normalized_contexts
    )
    fuzzy_hit = best_partial_ratio >= fuzzy_threshold
    return exact_hit, fuzzy_hit, (exact_hit or fuzzy_hit), best_partial_ratio


def resolve_output_path(
    explicit_path: Optional[Path], results_input: Path, default_filename: str
) -> Path:
    if explicit_path is not None:
        return explicit_path
    return results_input.parent / default_filename


def load_inputs(
    excel_path: Path, sheet_name: Optional[str], results_input: Path
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    if not results_input.exists():
        raise FileNotFoundError(f"Results CSV not found: {results_input}")

    resolved_sheet = sheet_name
    if resolved_sheet is None:
        resolved_sheet, _ = detect_qa_sheet_name(excel_path)

    qa_df = pd.read_excel(excel_path, sheet_name=resolved_sheet)
    results_df = pd.read_csv(results_input)

    missing_qa = REQUIRED_QA_COLUMNS.difference(qa_df.columns)
    if missing_qa:
        raise ValueError(f"QA sheet is missing required columns: {sorted(missing_qa)}")

    required_result_columns = {"query_id", "predicted_answer", "context_texts"}
    missing_results = required_result_columns.difference(results_df.columns)
    if missing_results:
        raise ValueError(
            f"Results CSV is missing required columns: {sorted(missing_results)}"
        )

    return qa_df, results_df, resolved_sheet


def join_inputs(qa_df: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
    qa_subset = qa_df[
        ["query_id", "query_text", "golden_answer", "source_text", "should_answer"]
    ].copy()
    merged = results_df.merge(
        qa_subset,
        on="query_id",
        how="left",
        suffixes=("", "_qa"),
        validate="one_to_one",
    )

    matched = 0
    if "query_text_qa" in merged.columns:
        matched = int(merged["query_text_qa"].notna().sum())
    if matched == 0:
        sample_ids = ", ".join(merged["query_id"].astype(str).head(5).tolist())
        raise ValueError(
            "Span evaluation matched zero rows between results CSV and QA sheet "
            f"by query_id. Sample result query_ids: {sample_ids}"
        )

    if "query_text_qa" in merged.columns:
        merged["query_text"] = merged["query_text_qa"].fillna(merged["query_text"])
    if "golden_answer_qa" in merged.columns:
        merged["golden_answer"] = merged["golden_answer_qa"].fillna(
            merged["golden_answer"]
        )
    if "source_text_qa" in merged.columns:
        merged["source_text"] = merged["source_text_qa"]
    if "should_answer_qa" in merged.columns:
        merged["should_answer"] = merged["should_answer_qa"]

    drop_columns = [
        column
        for column in [
            "query_text_qa",
            "golden_answer_qa",
            "source_text_qa",
            "should_answer_qa",
        ]
        if column in merged.columns
    ]
    return merged.drop(columns=drop_columns)


def determine_skip_reason(row: pd.Series) -> Optional[str]:
    should_answer = normalize_bool(row.get("should_answer"))
    if should_answer is not True:
        return "should_answer_false"
    if is_blank(row.get("predicted_answer")):
        return "missing_predicted_answer"
    if is_blank(row.get("source_text")):
        return "missing_source_text"
    if not split_context_texts(row.get("context_texts")):
        return "missing_retrieved_contexts"
    return None


def prepare_rows(df: pd.DataFrame) -> tuple[list[SpanRecallRow], dict[str, int]]:
    rows: list[SpanRecallRow] = []
    skip_counts: dict[str, int] = {}

    for _, source_row in df.iterrows():
        skip_reason = determine_skip_reason(source_row)
        retrieved_contexts = split_context_texts(source_row.get("context_texts"))

        if skip_reason is not None:
            skip_counts[skip_reason] = skip_counts.get(skip_reason, 0) + 1
            rows.append(
                SpanRecallRow(
                    query_id=str(source_row.get("query_id", "")),
                    query_text=str(source_row.get("query_text", "") or ""),
                    golden_answer=str(source_row.get("golden_answer", "") or ""),
                    predicted_answer=str(source_row.get("predicted_answer", "") or ""),
                    source_text=str(source_row.get("source_text", "") or ""),
                    retrieved_contexts=retrieved_contexts,
                    span_exact_hit=None,
                    span_fuzzy_hit=None,
                    span_hit=None,
                    span_best_partial_ratio=None,
                    span_eval_eligible=False,
                    span_skip_reason=skip_reason,
                )
            )
            continue

        rows.append(
            SpanRecallRow(
                query_id=str(source_row.get("query_id", "")),
                query_text=str(source_row.get("query_text", "") or ""),
                golden_answer=str(source_row.get("golden_answer", "") or ""),
                predicted_answer=str(source_row.get("predicted_answer", "") or ""),
                source_text=str(source_row.get("source_text", "") or ""),
                retrieved_contexts=retrieved_contexts,
                span_exact_hit=None,
                span_fuzzy_hit=None,
                span_hit=None,
                span_best_partial_ratio=None,
                span_eval_eligible=True,
                span_skip_reason=None,
            )
        )

    return rows, skip_counts


def score_rows(rows: list[SpanRecallRow], *, fuzzy_threshold: float) -> None:
    for row in rows:
        if not row.span_eval_eligible:
            continue
        (
            row.span_exact_hit,
            row.span_fuzzy_hit,
            row.span_hit,
            row.span_best_partial_ratio,
        ) = compute_span_match(
            row.source_text,
            row.retrieved_contexts,
            fuzzy_threshold=fuzzy_threshold,
        )


def rows_to_dataframe(rows: list[SpanRecallRow]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "query_id": row.query_id,
                "query_text": row.query_text,
                "golden_answer": row.golden_answer,
                "predicted_answer": row.predicted_answer,
                "source_text": row.source_text,
                "retrieved_context_count": len(row.retrieved_contexts),
                "span_eval_eligible": row.span_eval_eligible,
                "span_skip_reason": row.span_skip_reason,
                "span_exact_hit": row.span_exact_hit,
                "span_fuzzy_hit": row.span_fuzzy_hit,
                "span_hit": row.span_hit,
                "span_best_partial_ratio": row.span_best_partial_ratio,
            }
            for row in rows
        ]
    )


def build_summary(
    rows_df: pd.DataFrame,
    *,
    excel_path: Path,
    qa_sheet: str,
    results_input: Path,
    fuzzy_threshold: float,
    skip_counts: dict[str, int],
) -> dict[str, object]:
    eligible_mask = rows_df["span_eval_eligible"].fillna(False)
    eligible_df = rows_df[eligible_mask].copy()

    summary: dict[str, object] = {
        "results_input": str(results_input),
        "excel_path": str(excel_path),
        "qa_sheet": qa_sheet,
        "fuzzy_threshold": float(fuzzy_threshold),
        "total_rows": int(len(rows_df)),
        "eligible_rows": int(len(eligible_df)),
        "dropped_rows": int(len(rows_df) - len(eligible_df)),
        "span_exact_hit_rate": None,
        "span_fuzzy_hit_rate": None,
        "span_hit_rate": None,
        "span_best_partial_ratio_avg": None,
    }

    if not eligible_df.empty:
        summary["span_exact_hit_rate"] = float(eligible_df["span_exact_hit"].mean())
        summary["span_fuzzy_hit_rate"] = float(eligible_df["span_fuzzy_hit"].mean())
        summary["span_hit_rate"] = float(eligible_df["span_hit"].mean())
        summary["span_best_partial_ratio_avg"] = float(
            eligible_df["span_best_partial_ratio"].dropna().mean()
        )

    for reason, count in sorted(skip_counts.items()):
        summary[f"dropped_{reason}"] = int(count)

    return summary


def save_summary(summary: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(output_path, index=False)


def save_report(
    report_path: Path,
    summary: dict[str, object],
    rows_df: pd.DataFrame,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# StatsChat Evidence Span Evaluation",
        "",
        f"- Results input: `{summary['results_input']}`",
        f"- QA workbook: `{summary['excel_path']}`",
        f"- QA sheet: `{summary['qa_sheet']}`",
        f"- Fuzzy threshold: `{summary['fuzzy_threshold']}`",
        f"- Total rows: `{summary['total_rows']}`",
        f"- Eligible rows: `{summary['eligible_rows']}`",
        f"- Dropped rows: `{summary['dropped_rows']}`",
        "",
        "## Metrics",
        "",
        f"- Exact span hit rate: `{summary['span_exact_hit_rate']}`",
        f"- Fuzzy span hit rate: `{summary['span_fuzzy_hit_rate']}`",
        f"- Combined span hit rate: `{summary['span_hit_rate']}`",
        f"- Avg best partial ratio: `{summary['span_best_partial_ratio_avg']}`",
        "",
        "## Drop Reasons",
        "",
    ]

    drop_keys = sorted(key for key in summary if key.startswith("dropped_"))
    if drop_keys:
        for key in drop_keys:
            lines.append(f"- `{key}`: `{summary[key]}`")
    else:
        lines.append("- none")

    skipped = rows_df[~rows_df["span_eval_eligible"].fillna(False)]
    if not skipped.empty:
        lines.extend(["", "## Skipped Rows", ""])
        for _, row in skipped.iterrows():
            lines.append(f"- `{row['query_id']}`: `{row['span_skip_reason']}`")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate saved StatsChat runs with deterministic span matching."
    )
    parser.add_argument(
        "--excel",
        type=Path,
        default=DEFAULT_EXCEL,
        help="QA workbook with audited gold answers and source_text.",
    )
    parser.add_argument(
        "--sheet-name",
        default=None,
        help="Worksheet name. If omitted, auto-detect a sheet with QA columns.",
    )
    parser.add_argument(
        "--results-input",
        type=Path,
        required=True,
        help="Existing accuracy_results.csv from a saved run.",
    )
    parser.add_argument(
        "--results-output",
        type=Path,
        default=None,
        help=(
            "Output CSV for per-row span metrics. Defaults to "
            "<results-input dir>/span_recall_results.csv"
        ),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help=(
            "Output CSV for summary metrics. Defaults to "
            "<results-input dir>/span_recall_summary.csv"
        ),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help=(
            "Markdown report path. Defaults to "
            "<results-input dir>/span_recall_report.md"
        ),
    )
    parser.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=DEFAULT_FUZZY_THRESHOLD,
        help="RapidFuzz partial_ratio threshold for fuzzy span hits.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    qa_df, results_df, resolved_sheet = load_inputs(
        args.excel, args.sheet_name, args.results_input
    )
    merged_df = join_inputs(qa_df, results_df)
    rows, skip_counts = prepare_rows(merged_df)
    score_rows(rows, fuzzy_threshold=args.fuzzy_threshold)

    rows_df = rows_to_dataframe(rows)
    summary = build_summary(
        rows_df,
        excel_path=args.excel,
        qa_sheet=resolved_sheet,
        results_input=args.results_input,
        fuzzy_threshold=args.fuzzy_threshold,
        skip_counts=skip_counts,
    )

    results_output = resolve_output_path(
        args.results_output, args.results_input, "span_recall_results.csv"
    )
    summary_output = resolve_output_path(
        args.summary_output, args.results_input, "span_recall_summary.csv"
    )
    report_output = resolve_output_path(
        args.report_output, args.results_input, "span_recall_report.md"
    )

    results_output.parent.mkdir(parents=True, exist_ok=True)
    rows_df.to_csv(results_output, index=False)
    save_summary(summary, summary_output)
    save_report(report_output, summary, rows_df)

    print(f"Span results saved to: {results_output}")
    print(f"Span summary saved to: {summary_output}")
    print(f"Span report saved to: {report_output}")
    print("\nSpan evaluation summary")
    print(f"Total rows: {summary['total_rows']}")
    print(f"Eligible rows: {summary['eligible_rows']}")
    print(f"Dropped rows: {summary['dropped_rows']}")
    print(f"Exact span hit rate: {summary['span_exact_hit_rate']}")
    print(f"Fuzzy span hit rate: {summary['span_fuzzy_hit_rate']}")
    print(f"Combined span hit rate: {summary['span_hit_rate']}")
    print(f"Avg best partial ratio: {summary['span_best_partial_ratio_avg']}")


if __name__ == "__main__":
    main()
