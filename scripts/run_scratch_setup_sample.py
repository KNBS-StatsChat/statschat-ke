"""Run a small SETUP-mode sample in an isolated scratch directory.

This is intended for debugging missing downloads + PyMuPDF extraction issues
without touching your real `data/` directory.

It:
- downloads a capped number of PDFs (via app.max_pdfs)
- converts them to JSON
- runs an offline audit against url_dict.json vs files on disk

Run:
    python scripts/run_scratch_setup_sample.py

Outputs:
- prints the scratch directory path
- writes reports under <scratch>/outputs/
"""

from __future__ import annotations

import os
import pathlib
import tempfile
from pathlib import Path

import statschat
from statschat.pdf_processing import audit_downloads, pdf_downloader, pdf_to_json


def main() -> Path:
    scratch = Path(tempfile.mkdtemp(prefix="statschat_scratch_"))

    # Force all scripts that use Path.cwd() to write into the scratch directory.
    pathlib.Path.cwd = lambda: scratch

    cfg = {
        "preprocess": {"mode": "SETUP"},
        "app": {"page_start": 1, "page_end": 1, "max_pdfs": 5},
    }

    # Patch config loader.
    statschat.load_config = lambda *a, **k: cfg
    pdf_to_json.load_config = lambda *a, **k: cfg
    audit_downloads.load_config = lambda *a, **k: cfg

    os.environ["STATSCHAT_WRITE_EXTRACTION_WARNINGS"] = "1"

    print(f"Scratch dir: {scratch}")

    print("\n--- Running downloader (SETUP, max_pdfs=5) ---")
    pdf_downloader.main()

    print("\n--- Running pdf_to_json (SETUP) ---")
    pdf_to_json.process_pdfs("SETUP", cfg)

    print("\n--- Auditing downloads (offline) ---")
    audit_path = audit_downloads.main()

    print(f"\nAudit report: {audit_path}")
    print("Outputs:")
    for p in sorted((scratch / "outputs").glob("*")):
        print("-", p.name)

    return scratch


if __name__ == "__main__":
    main()
