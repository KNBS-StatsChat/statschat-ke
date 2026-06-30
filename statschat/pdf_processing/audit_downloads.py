"""Audit downloaded PDFs against url_dict.json.

This is a lightweight, offline integrity check to help confirm "missing downloads":
- PDFs referenced in url_dict.json but missing on disk
- PDFs present on disk but missing from url_dict.json
- zero-byte PDFs
- files that don't look like PDFs (magic header check)

It does not perform any network requests.

Usage:
    python -m statschat.pdf_processing.audit_downloads

Notes:
- In UPDATE mode, new PDFs land in data/latest_pdf_downloads before being merged.
- This script audits both data/pdf_downloads and data/latest_pdf_downloads when present.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from statschat import load_config


@dataclass(frozen=True)
class AuditFinding:
    filename: str
    reason: str
    path: str | None = None
    url: str | None = None
    report_page: str | None = None


def _is_pdf_magic(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            head = f.read(5)
        return head == b"%PDF-"
    except OSError:
        return False


def _load_url_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def audit_directory(pdf_dir: Path) -> dict[str, Any]:
    """Audit a single directory containing PDFs and a url_dict.json."""

    findings: list[AuditFinding] = []

    url_dict_path = pdf_dir / "url_dict.json"
    url_dict = _load_url_dict(url_dict_path)

    dict_files = {k for k in url_dict.keys() if k.lower().endswith(".pdf")}
    disk_files = {p.name for p in pdf_dir.glob("*.pdf")}

    missing_on_disk = sorted(dict_files - disk_files)
    extra_on_disk = sorted(disk_files - dict_files)

    for filename in missing_on_disk:
        meta = (
            url_dict.get(filename, {})
            if isinstance(url_dict.get(filename), dict)
            else {}
        )
        findings.append(
            AuditFinding(
                filename=filename,
                reason="missing_on_disk",
                path=str(pdf_dir / filename),
                url=meta.get("pdf_url"),
                report_page=meta.get("report_page"),
            )
        )

    for filename in extra_on_disk:
        findings.append(
            AuditFinding(
                filename=filename,
                reason="extra_on_disk",
                path=str(pdf_dir / filename),
            )
        )

    for pdf_path in sorted(pdf_dir.glob("*.pdf"), key=lambda p: p.name):
        try:
            size = pdf_path.stat().st_size
        except OSError:
            size = -1

        if size == 0:
            findings.append(
                AuditFinding(
                    filename=pdf_path.name,
                    reason="zero_byte",
                    path=str(pdf_path),
                )
            )
        elif size > 0 and not _is_pdf_magic(pdf_path):
            findings.append(
                AuditFinding(
                    filename=pdf_path.name,
                    reason="non_pdf_magic",
                    path=str(pdf_path),
                )
            )

    return {
        "pdf_dir": str(pdf_dir),
        "url_dict_path": str(url_dict_path),
        "url_dict_entries": len(dict_files),
        "pdf_files_on_disk": len(disk_files),
        "findings": [asdict(f) for f in findings],
    }


def main() -> Path:
    config = load_config(name="main")
    mode = str(config["preprocess"]["mode"]).upper()

    base_dir = Path.cwd() / "data"
    primary_dir = base_dir / "pdf_downloads"
    latest_dir = base_dir / "latest_pdf_downloads"

    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "directories": [],
    }

    if primary_dir.exists():
        results["directories"].append(audit_directory(primary_dir))
    if latest_dir.exists():
        results["directories"].append(audit_directory(latest_dir))

    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = outputs_dir / f"download_audit_{mode.lower()}_{ts}.json"
    out_path.write_text(json.dumps(results, indent=2))

    # Console summary
    total_findings = sum(len(d.get("findings", [])) for d in results["directories"])
    print(f"Audit complete. Findings: {total_findings}. Report: {out_path}")

    return out_path


if __name__ == "__main__":
    main()
