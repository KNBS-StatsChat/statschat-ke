from __future__ import annotations

"""Summarize StatsChat PDF text extraction warnings/errors (JSONL).

Purpose
-------
During PDF→text extraction, StatsChat can persist exceptions and MuPDF warnings
to a JSONL file (default: outputs/pdf_text_extraction_warnings.jsonl). This
script prints a quick, human-readable summary to stdout:
- counts by error_type
- top MuPDF warning messages (first line)
- keyword hit counts (e.g., shading/colorspace/icc/pattern)
- top affected PDFs

This is a fast way to answer: “are we seeing shading/colorspace issues?” and
“which PDFs are the noisiest?”

How to run
----------
    /Users/gregdunlop/projects2/statschat-ke/.venv/bin/python \
        scripts/summarize_extraction_warnings.py

    /Users/gregdunlop/projects2/statschat-ke/.venv/bin/python \
        scripts/summarize_extraction_warnings.py \
        --top 20 \
        --keywords "shading,colorspace,icc,pattern"

Inputs/Outputs
--------------
- Input: outputs/pdf_text_extraction_warnings.jsonl (or --path)
- Output: printed summary (no files written)
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize StatsChat PDF text extraction warnings/errors written to "
            "outputs/pdf_text_extraction_warnings.jsonl."
        )
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("outputs/pdf_text_extraction_warnings.jsonl"),
        help="Path to the JSONL warnings file.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top items to display in each summary section.",
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="shading,colorspace,color space,icc,pattern",
        help=(
            "Comma-separated list of keywords to count in warning/error text. "
            "(Case-insensitive.)"
        ),
    )
    return parser.parse_args()


def _safe_json_loads(line: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(line)
    except Exception:
        return None

    if isinstance(obj, dict):
        return obj

    return None


def main() -> int:
    args = _parse_args()

    if not args.path.exists():
        print(f"Not found: {args.path}")
        return 2

    lines = args.path.read_text(encoding="utf-8").splitlines()
    items = [
        obj
        for obj in (_safe_json_loads(line_text) for line_text in lines)
        if obj is not None
    ]

    print(f"Path: {args.path}")
    print(f"Lines: {len(lines)}")
    print(f"Parsed: {len(items)}")

    by_type = Counter(str(i.get("error_type", "Unknown")) for i in items)
    print("\nBy error_type:")
    for error_type, n in by_type.most_common():
        print(f"  {n:>6}  {error_type}")

    mupdf_warnings = [i for i in items if i.get("error_type") == "MuPDFWarning"]
    if mupdf_warnings:
        first_lines: list[str] = []
        for w in mupdf_warnings:
            text = str(w.get("warning", "") or "").strip()
            if not text:
                continue
            first_lines.append(text.splitlines()[0])

        print("\nTop MuPDF warnings (first line):")
        for s, n in Counter(first_lines).most_common(args.top):
            print(f"  {n:>6}  {s[:200]}")

    # Keyword hits in either 'warning' or 'error'
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if keywords:
        haystacks = [
            (
                str(i.get("warning", "") or "") + "\n" + str(i.get("error", "") or "")
            ).lower()
            for i in items
        ]
        kw_counts = {k: 0 for k in keywords}
        for h in haystacks:
            for k in keywords:
                if k.lower() in h:
                    kw_counts[k] += 1

        print("\nKeyword hits (items containing keyword):")
        for k, n in sorted(kw_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {n:>6}  {k}")

    # Which PDFs are most affected?
    pdf_counts = Counter(str(i.get("pdf")) for i in items if i.get("pdf"))
    if pdf_counts:
        print("\nTop PDFs by warning/error count:")
        for pdf, n in pdf_counts.most_common(args.top):
            print(f"  {n:>6}  {Path(pdf).name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
