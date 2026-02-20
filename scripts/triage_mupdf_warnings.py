from __future__ import annotations

"""Triage MuPDF (PyMuPDF) warnings from StatsChat PDF→text extraction.

Purpose
-------
StatsChat captures MuPDF warnings (via PyMuPDF) during `page.get_text()` and
writes them as JSONL items (one per page) when extraction warnings are enabled.
Most warnings are non-fatal (often font embedding/mapping), but a small subset
can correlate with missing/garbled/mispositioned text.

This script helps you decide whether any warnings likely need manual inspection
by:
- grouping warnings by PDF,
- sampling a few pages that emitted warnings,
- flagging samples where extracted text looks suspiciously empty.

Inputs
------
- Warnings JSONL: outputs/pdf_text_extraction_warnings.jsonl
    (written when STATSCHAT_WRITE_EXTRACTION_WARNINGS=1 during conversion)
- Local PDFs: searched under one or more --pdf-root directories.

Outputs
-------
- Markdown report (default): outputs/mupdf_warning_triage_report.md

How to run
----------
Use the project virtualenv Python (so PyMuPDF/fitz is available):

    /Users/gregdunlop/projects2/statschat-ke/.venv/bin/python \
        scripts/triage_mupdf_warnings.py \
        --top 15 \
        --sample-pages 3 \
        --pdf-root data/pdf_downloads \
        --pdf-root data/latest_pdf_downloads

Notes
-----
- The `--min-chars` / `--min-alnum` thresholds are heuristics; a page can be
    legitimately short (e.g., a cover page).
- This script samples pages using `page.get_text("text")` (not the full
    StatsChat conversion pipeline) to provide a quick sanity check.
"""

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class WarningItem:
    pdf_name: str
    pdf_path_logged: str
    page: Optional[int]
    warning_text: str


@dataclass(frozen=True)
class PageSample:
    page: int
    extracted_chars: int
    extracted_alnum: int
    suspicious: bool
    preview: str


CONCERNING_WARNING_KEYWORDS = (
    "actualtext",
    "no position",
    "invalid marked content",
    "clip nesting",
    "could not find any cmaps",
    "unknown font format",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not path.exists():
        return items

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            items.append(obj)
    return items


def _iter_mupdf_warnings(items: Iterable[dict[str, Any]]) -> Iterable[WarningItem]:
    for item in items:
        if str(item.get("error_type")) != "MuPDFWarning":
            continue

        pdf_path_logged = str(item.get("pdf") or "")
        pdf_name = (
            Path(pdf_path_logged).name
            if pdf_path_logged
            else str(item.get("pdf") or "")
        )
        page = item.get("page")
        page_int = page if isinstance(page, int) else None
        warning_text = str(item.get("warning") or "").strip()

        if not pdf_name:
            continue

        yield WarningItem(
            pdf_name=pdf_name,
            pdf_path_logged=pdf_path_logged,
            page=page_int,
            warning_text=warning_text,
        )


def _first_line(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _is_concerning_warning(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in CONCERNING_WARNING_KEYWORDS)


def _find_pdf_path(
    pdf_name: str, search_roots: list[Path], cache: dict[str, Optional[Path]]
) -> Optional[Path]:
    if pdf_name in cache:
        return cache[pdf_name]

    for root in search_roots:
        if not root.exists():
            continue

        # Fast path: direct child
        direct = root / pdf_name
        if direct.exists():
            cache[pdf_name] = direct
            return direct

        # Common layout: nested downloads
        matches = list(root.rglob(pdf_name))
        if matches:
            # Prefer shortest path (usually the canonical downloads dir)
            best = sorted(matches, key=lambda p: (len(p.parts), str(p)))[0]
            cache[pdf_name] = best
            return best

    cache[pdf_name] = None
    return None


def _sample_pages_from_pdf(
    pdf_path: Path,
    pages: list[int],
    *,
    sample_pages: int,
    min_chars: int,
    min_alnum: int,
) -> tuple[list[PageSample], Optional[str]]:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover
        return [], f"PyMuPDF not available: {exc}"

    samples: list[PageSample] = []

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return [], f"Failed to open PDF: {exc}"

    try:
        wanted = sorted({p for p in pages if isinstance(p, int) and p > 0})
        wanted = wanted[:sample_pages]

        for page_num in wanted:
            try:
                page = doc[page_num - 1]
                extracted = page.get_text("text") or ""
            except Exception:
                extracted = ""

            extracted_stripped = extracted.strip()
            extracted_chars = len(extracted_stripped)
            extracted_alnum = sum(1 for c in extracted_stripped if c.isalnum())
            suspicious = (extracted_chars < min_chars) or (extracted_alnum < min_alnum)
            preview = extracted_stripped.replace("\n", " ")
            preview = preview[:160] + ("…" if len(preview) > 160 else "")

            samples.append(
                PageSample(
                    page=page_num,
                    extracted_chars=extracted_chars,
                    extracted_alnum=extracted_alnum,
                    suspicious=suspicious,
                    preview=preview,
                )
            )

        return samples, None
    finally:
        doc.close()


def _write_markdown_report(
    *,
    out_path: Path,
    warnings_path: Path,
    total_warning_items: int,
    pdf_summaries: list[dict[str, Any]],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# MuPDF warning triage report\n")
    lines.append(f"Warnings source: `{warnings_path}`\n")
    lines.append(f"Total warning items: **{total_warning_items}**\n")
    lines.append(f"PDFs included in report: **{len(pdf_summaries)}**\n")
    lines.append(
        "This report samples pages that emitted MuPDF warnings and flags pages where extracted text looks suspiciously empty.\n"
    )

    lines.append("## Summary table")
    lines.append(
        "| pdf | warning_items | pages_with_warnings | concerning_items | pdf_found | suspicious_samples | most_common_warning |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")

    for s in pdf_summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(s["pdf"]),
                    str(s["warning_items"]),
                    str(s["pages_with_warnings"]),
                    str(s["concerning_items"]),
                    "yes" if s["pdf_found"] else "no",
                    str(s["suspicious_samples"]),
                    str(s["most_common_warning"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.append("\n## Details")
    for s in pdf_summaries:
        lines.append(f"\n### {s['pdf']}")
        if not s["pdf_found"]:
            lines.append(
                "- PDF not found locally under the provided `--pdf-root` search paths."
            )
            continue

        if s.get("open_error"):
            lines.append(f"- Could not open/sample PDF: {s['open_error']}")
            continue

        samples: list[PageSample] = s.get("samples", [])
        if not samples:
            lines.append("- No page samples available.")
            continue

        lines.append("| page | chars | alnum | suspicious | preview |")
        lines.append("| --- | --- | --- | --- | --- |")
        for p in samples:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(p.page),
                        str(p.extracted_chars),
                        str(p.extracted_alnum),
                        "yes" if p.suspicious else "no",
                        (p.preview or "(empty)").replace("|", "\\|"),
                    ]
                )
                + " |"
            )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Triage MuPDF (PyMuPDF) warnings by sampling flagged pages and checking "
            "whether extracted text looks suspiciously empty."
        )
    )
    parser.add_argument(
        "--warnings",
        type=Path,
        default=Path("outputs/pdf_text_extraction_warnings.jsonl"),
        help="Path to pdf_text_extraction_warnings.jsonl",
    )
    parser.add_argument(
        "--pdf-root",
        type=Path,
        action="append",
        default=[Path("data")],
        help=(
            "Directory to search for PDFs (can be repeated). Default: data/. "
            "Example: --pdf-root data/pdf_downloads"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/mupdf_warning_triage_report.md"),
        help="Output markdown report path",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Number of PDFs (by warning count) to include in report",
    )
    parser.add_argument(
        "--sample-pages",
        type=int,
        default=3,
        help="How many warning pages to sample per PDF",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=30,
        help="Flag sample as suspicious if extracted text has fewer non-whitespace chars",
    )
    parser.add_argument(
        "--min-alnum",
        type=int,
        default=10,
        help="Flag sample as suspicious if extracted text has fewer alphanumeric characters",
    )

    args = parser.parse_args()

    warnings_path: Path = args.warnings
    search_roots: list[Path] = list(args.pdf_root)

    raw_items = _load_jsonl(warnings_path)
    warnings = list(_iter_mupdf_warnings(raw_items))

    by_pdf: dict[str, list[WarningItem]] = defaultdict(list)
    for w in warnings:
        by_pdf[w.pdf_name].append(w)

    # Build per-PDF stats and select top-N by count.
    pdf_stats: list[tuple[str, int]] = sorted(
        [(pdf, len(items)) for pdf, items in by_pdf.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    selected = [pdf for pdf, _ in pdf_stats[: max(0, args.top)]]

    pdf_path_cache: dict[str, Optional[Path]] = {}

    summaries: list[dict[str, Any]] = []
    for pdf in selected:
        items = by_pdf[pdf]
        pages = [w.page for w in items if isinstance(w.page, int)]
        pages_with_warnings = len({p for p in pages if isinstance(p, int)})

        most_common = Counter(
            _first_line(w.warning_text) for w in items if w.warning_text
        ).most_common(1)
        most_common_warning = most_common[0][0] if most_common else ""

        concerning_items = sum(
            1 for w in items if _is_concerning_warning(w.warning_text)
        )

        pdf_path = _find_pdf_path(pdf, search_roots, pdf_path_cache)
        pdf_found = pdf_path is not None

        samples: list[PageSample] = []
        open_error: Optional[str] = None
        suspicious_samples = 0

        if pdf_path is not None:
            samples, open_error = _sample_pages_from_pdf(
                pdf_path,
                [p for p in pages if isinstance(p, int)],
                sample_pages=args.sample_pages,
                min_chars=args.min_chars,
                min_alnum=args.min_alnum,
            )
            suspicious_samples = sum(1 for s in samples if s.suspicious)

        summaries.append(
            {
                "pdf": pdf,
                "warning_items": len(items),
                "pages_with_warnings": pages_with_warnings,
                "concerning_items": concerning_items,
                "pdf_found": pdf_found,
                "most_common_warning": most_common_warning,
                "open_error": open_error,
                "samples": samples,
                "suspicious_samples": suspicious_samples,
            }
        )

    _write_markdown_report(
        out_path=args.out,
        warnings_path=warnings_path,
        total_warning_items=len(warnings),
        pdf_summaries=summaries,
    )

    print(f"Wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
