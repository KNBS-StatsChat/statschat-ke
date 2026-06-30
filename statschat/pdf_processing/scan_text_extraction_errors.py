"""Scan local PDFs for PyMuPDF (MuPDF) text-extraction errors.

This is a diagnostic tool for investigating issues like:
- "shading colorspace" errors
- page-level text extraction failures

It does NOT modify PDFs or create JSON conversions.

Usage:
    python -m statschat.pdf_processing.scan_text_extraction_errors \
      --dir data/pdf_downloads --max-pdfs 50 --max-pages 5

Environment:
- Set `STATSCHAT_PDFPLUMBER_FALLBACK=1` to attempt a pdfplumber fallback when
  PyMuPDF fails for a page.

Output:
- Writes a JSON report under outputs/.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz
import pdfplumber


def _scan_pdf(
    pdf_path: Path,
    *,
    max_pages: int,
    try_pdfplumber: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pdf": str(pdf_path),
        "pages_scanned": 0,
        "open_error": None,
        "page_errors": [],
        "fallback_success_pages": [],
    }

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        result["open_error"] = {"error": str(exc), "error_type": type(exc).__name__}
        return result

    plumber = None
    try:
        page_count = len(doc)
        pages_to_scan = min(page_count, max_pages)

        for i in range(pages_to_scan):
            page_num = i + 1
            try:
                _ = doc[i].get_text()
            except Exception as exc:
                err = {
                    "page": page_num,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }

                if try_pdfplumber:
                    try:
                        if plumber is None:
                            plumber = pdfplumber.open(pdf_path)
                        _ = plumber.pages[i].extract_text() or ""
                        result["fallback_success_pages"].append(page_num)
                    except Exception as fallback_exc:
                        err["fallback_error"] = {
                            "error": str(fallback_exc),
                            "error_type": type(fallback_exc).__name__,
                        }

                result["page_errors"].append(err)

            result["pages_scanned"] += 1

    finally:
        try:
            doc.close()
        except Exception:
            pass
        if plumber is not None:
            try:
                plumber.close()
            except Exception:
                pass

    return result


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        dest="pdf_dir",
        default="data/pdf_downloads",
        help="Directory containing PDFs to scan (default: data/pdf_downloads)",
    )
    parser.add_argument(
        "--max-pdfs",
        type=int,
        default=50,
        help="Maximum number of PDFs to scan (default: 50)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum pages per PDF to scan (default: 5)",
    )

    args = parser.parse_args(argv)

    pdf_dir = Path.cwd() / args.pdf_dir
    max_pdfs = max(1, args.max_pdfs)
    max_pages = max(1, args.max_pages)

    try_pdfplumber = os.environ.get("STATSCHAT_PDFPLUMBER_FALLBACK", "1") == "1"

    pdfs = sorted(pdf_dir.glob("*.pdf"), key=lambda p: p.name)[:max_pdfs]

    results = [
        _scan_pdf(p, max_pages=max_pages, try_pdfplumber=try_pdfplumber) for p in pdfs
    ]

    errors = [r for r in results if r.get("open_error") or r.get("page_errors")]

    payload: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pdf_dir": str(pdf_dir),
        "max_pdfs": max_pdfs,
        "max_pages": max_pages,
        "scanned": len(results),
        "with_errors": len(errors),
        "results": errors,
    }

    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = outputs_dir / f"text_extraction_scan_{ts}.json"
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"Scan complete. PDFs with errors: {len(errors)}. Report: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
