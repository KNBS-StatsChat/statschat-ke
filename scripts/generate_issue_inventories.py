from __future__ import annotations

"""Generate markdown inventories for common pipeline issues.

Purpose
-------
This script produces two lightweight, shareable markdown reports under
docs/investigations/:

1) KNBS download HTTP 404 inventory
     - Reads outputs/pdf_download_report_*.json
     - Deduplicates failures that look like 404s by PDF name
     - Writes: docs/investigations/2026-02-09-knbs-404-download-inventory.md

2) MuPDF warning inventory (PyMuPDF)
     - Reads outputs/pdf_text_extraction_warnings.jsonl
     - Filters to MuPDFWarning items
     - Summarizes counts by PDF and includes compact page ranges
     - Writes: docs/investigations/2026-02-09-mupdf-warning-inventory.md

How to run
----------
    /Users/gregdunlop/projects2/statschat-ke/.venv/bin/python \
        scripts/generate_issue_inventories.py

Notes
-----
- The output filenames are date-stamped in code to match the investigation
    write-up; update them if you want to regenerate on a different date.
- The MuPDF warning inventory is driven entirely by what was captured during
    extraction (STATSCHAT_WRITE_EXTRACTION_WARNINGS=1).
"""

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class DownloadFailure:
    pdf_name: str
    pdf_url: str
    report_page: str
    error: str
    error_type: str
    source_report: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_download_failures(outputs_dir: Path) -> Iterable[DownloadFailure]:
    for path in sorted(outputs_dir.glob("pdf_download_report_*.json")):
        data = _load_json(path)
        failures = data.get("failures") or []
        if not isinstance(failures, list):
            continue

        for item in failures:
            if not isinstance(item, dict):
                continue

            yield DownloadFailure(
                pdf_name=str(item.get("pdf_name", "")),
                pdf_url=str(item.get("pdf_url", "")),
                report_page=str(item.get("report_page", "")),
                error=str(item.get("error", "")),
                error_type=str(item.get("error_type", "")),
                source_report=path.name,
            )


def _as_md_table(rows: list[list[str]], header: list[str]) -> str:
    def esc(s: str) -> str:
        return s.replace("\n", " ").replace("|", "\\|").strip()

    lines = []
    lines.append("| " + " | ".join(esc(h) for h in header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines)


def _compress_page_ranges(pages: Iterable[int]) -> str:
    unique_sorted = sorted({p for p in pages if isinstance(p, int) and p > 0})
    if not unique_sorted:
        return ""

    ranges: list[str] = []
    start = prev = unique_sorted[0]
    for p in unique_sorted[1:]:
        if p == prev + 1:
            prev = p
            continue

        ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = p
    ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(ranges)


def _truncate(s: str, *, max_len: int) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max(0, max_len - 1)].rstrip() + "…"


def write_404_inventory(*, outputs_dir: Path, out_path: Path) -> None:
    failures = list(_iter_download_failures(outputs_dir))

    failures_404 = [
        f
        for f in failures
        if ("404" in (f.error or ""))
        or (f.error_type.lower() == "httperror" and "404" in (f.error or ""))
    ]

    # Group by pdf_name (stable key) and retain representative details.
    grouped: dict[str, list[DownloadFailure]] = defaultdict(list)
    for f in failures_404:
        if f.pdf_name:
            grouped[f.pdf_name].append(f)

    rows: list[list[str]] = []
    for pdf_name in sorted(grouped.keys()):
        items = grouped[pdf_name]
        # Prefer non-empty urls/pages
        first = next((i for i in items if i.pdf_url or i.report_page), items[0])
        sources = ", ".join(sorted({i.source_report for i in items}))
        rows.append(
            [
                pdf_name,
                first.error or "HTTP 404",
                first.report_page,
                first.pdf_url,
                sources,
            ]
        )

    now = datetime.now().strftime("%Y-%m-%d")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md = []
    md.append("# Inventory: KNBS download 404s\n")
    md.append(f"Date: {now}\n")
    md.append(
        "This is the current deduplicated list of KNBS PDF links that were discovered but returned HTTP 404 during download."
    )
    md.append("")
    md.append(f"Source reports: `{outputs_dir}/pdf_download_report_*.json`\n")
    md.append(f"Unique 404 PDFs: **{len(rows)}**\n")

    if rows:
        md.append(
            _as_md_table(
                rows,
                header=[
                    "pdf_name",
                    "error",
                    "report_page",
                    "pdf_url",
                    "seen_in_reports",
                ],
            )
        )
    else:
        md.append("No 404s found in the download reports.")

    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            items.append(obj)
    return items


def write_mupdf_warning_inventory(*, warnings_path: Path, out_path: Path) -> None:
    items = _load_jsonl(warnings_path) if warnings_path.exists() else []

    warnings = [i for i in items if str(i.get("error_type")) == "MuPDFWarning"]
    other_items = [
        i
        for i in items
        if i.get("error_type") and str(i.get("error_type")) != "MuPDFWarning"
    ]
    by_pdf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for w in warnings:
        pdf = str(w.get("pdf") or "")
        if pdf:
            by_pdf[pdf].append(w)

    top_warning_first_line = Counter()
    for w in warnings:
        text = str(w.get("warning") or "").strip()
        if not text:
            continue
        top_warning_first_line[text.splitlines()[0]] += 1

    rows: list[list[str]] = []
    for pdf in sorted(by_pdf.keys(), key=lambda p: Path(p).name.lower()):
        entries = by_pdf[pdf]
        page_nums = [e.get("page") for e in entries if isinstance(e.get("page"), int)]
        pages_with_warnings = len(set(page_nums)) if page_nums else 0
        pages_compact = _compress_page_ranges(page_nums)

        # Pick a representative warning first line.
        first_line_counter = Counter()
        for e in entries:
            text = str(e.get("warning") or "").strip()
            if text:
                first_line_counter[text.splitlines()[0]] += 1
        top_line = first_line_counter.most_common(1)[0][0] if first_line_counter else ""

        rows.append(
            [
                Path(pdf).name,
                str(len(entries)),
                str(pages_with_warnings),
                _truncate(pages_compact, max_len=60),
                _truncate(top_line, max_len=90),
            ]
        )

    keywords = ["shading", "colorspace", "color space", "icc", "pattern"]
    keyword_hits = {k: 0 for k in keywords}
    for w in warnings:
        text = str(w.get("warning") or "").lower()
        for k in keywords:
            if k in text:
                keyword_hits[k] += 1

    now = datetime.now().strftime("%Y-%m-%d")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md: list[str] = []
    md.append("# Inventory: MuPDF (PyMuPDF) warnings during PDF→text extraction\n")
    md.append(f"Date: {now}\n")
    md.append(
        "This inventory summarizes warnings captured from MuPDF (via PyMuPDF) during `page.get_text()` calls. "
        "These are *warnings* (not necessarily fatal errors) and often relate to font embedding/mapping."
    )
    md.append("")
    md.append(f"Source warnings file: `{warnings_path}`\n")
    md.append(f"Total warning items: **{len(warnings)}**\n")
    md.append(f"PDFs with ≥1 warning: **{len(rows)}**\n")
    md.append("Keyword hits in warnings (counts of items containing keyword):")
    for k, n in keyword_hits.items():
        md.append(f"- {k}: {n}")

    md.append("")
    md.append("## Top warning types (first line)")
    if top_warning_first_line:
        for s, n in top_warning_first_line.most_common(15):
            md.append(f"- {n}x {s}")
    else:
        md.append("- (none)")

    md.append("")
    md.append("## PDFs with warnings")
    if rows:
        md.append(
            _as_md_table(
                rows,
                header=[
                    "pdf",
                    "warning_items",
                    "pages_with_warnings",
                    "pages",
                    "most_common_warning",
                ],
            )
        )
    else:
        md.append("No MuPDF warnings found.")

    # Also summarize non-MuPDF issues (exceptions, fallback failures, etc.)
    md.append("")
    md.append("## Other extraction issues (non-MuPDFWarning)")
    if not other_items:
        md.append("No non-MuPDF issues found in the warnings JSONL.")
        out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        return

    other_by_type = Counter(str(i.get("error_type")) for i in other_items)
    md.append("### Counts by error_type")
    for t, n in other_by_type.most_common():
        md.append(f"- {n}x {t}")

    md.append("")
    md.append("### PDFs with non-MuPDF issues")
    other_by_pdf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i in other_items:
        pdf = str(i.get("pdf") or "")
        if pdf:
            other_by_pdf[pdf].append(i)

    other_rows: list[list[str]] = []
    for pdf in sorted(other_by_pdf.keys(), key=lambda p: Path(p).name.lower()):
        entries = other_by_pdf[pdf]
        types = Counter(
            str(e.get("error_type")) for e in entries if e.get("error_type")
        )
        top_type = types.most_common(1)[0][0] if types else ""
        page_nums = [e.get("page") for e in entries if isinstance(e.get("page"), int)]
        pages_compact = _compress_page_ranges(page_nums)
        sample_msg = ""
        # Prefer an explicit 'error' field if present.
        for e in entries:
            msg = str(e.get("error") or "").strip()
            if msg:
                sample_msg = msg
                break
        other_rows.append(
            [
                Path(pdf).name,
                str(len(entries)),
                _truncate(top_type, max_len=40),
                _truncate(pages_compact, max_len=60),
                _truncate(sample_msg.splitlines()[0] if sample_msg else "", max_len=90),
            ]
        )

    md.append(
        _as_md_table(
            other_rows,
            header=[
                "pdf",
                "issue_items",
                "top_error_type",
                "pages",
                "sample_message",
            ],
        )
    )

    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate markdown inventories for KNBS 404 download failures and MuPDF "
            "(PyMuPDF) warnings captured during PDF→text extraction."
        )
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory containing outputs/pdf_download_report_*.json etc.",
    )
    parser.add_argument(
        "--warnings-path",
        type=Path,
        default=Path("outputs/pdf_text_extraction_warnings.jsonl"),
        help=(
            "Path to the JSONL warnings file (e.g. a full-run timestamped file). "
            "No renaming/copying required."
        ),
    )
    parser.add_argument(
        "--out-404",
        type=Path,
        default=Path("docs/investigations/2026-02-09-knbs-404-download-inventory.md"),
        help="Output path for the 404 inventory markdown.",
    )
    parser.add_argument(
        "--out-warn",
        type=Path,
        default=Path("docs/investigations/2026-02-09-mupdf-warning-inventory.md"),
        help="Output path for the MuPDF warning inventory markdown.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    outputs_dir = args.outputs_dir
    if not outputs_dir.is_absolute():
        outputs_dir = repo_root / outputs_dir

    warnings_path = args.warnings_path
    if not warnings_path.is_absolute():
        warnings_path = repo_root / warnings_path

    out_404 = args.out_404
    if not out_404.is_absolute():
        out_404 = repo_root / out_404

    out_warn = args.out_warn
    if not out_warn.is_absolute():
        out_warn = repo_root / out_warn

    write_404_inventory(outputs_dir=outputs_dir, out_path=out_404)
    write_mupdf_warning_inventory(warnings_path=warnings_path, out_path=out_warn)

    print(f"Wrote: {out_404}")
    print(f"Wrote: {out_warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
