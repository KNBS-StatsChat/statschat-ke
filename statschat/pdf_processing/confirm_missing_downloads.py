"""Confirm potential missing downloads by comparing KNBS discovery vs local url_dict.

This script re-scrapes KNBS report listing pages (no PDF downloads) and compares
what it discovers to what's currently recorded in:
- data/pdf_downloads/url_dict.json
- data/latest_pdf_downloads/url_dict.json (if present)

It produces a report in outputs/ with:
- discovered PDF links (filenames and URLs)
- filenames discovered but not present in local url_dict.json ("missing")
- filename collisions (same filename, multiple URLs)
- report pages with multiple PDF links

Usage:
    python -m statschat.pdf_processing.confirm_missing_downloads

Notes:
- Uses main config values: app.page_start/app.page_end
- Respects the census exclusion used by the downloader
"""

from __future__ import annotations

import concurrent.futures
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from statschat import load_config


@dataclass(frozen=True)
class DiscoveredPdf:
    filename: str
    pdf_url: str
    report_page: str


def _load_url_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _discover_pdfs(*, page_start: int, page_end: int) -> list[DiscoveredPdf]:
    base_url = "https://www.knbs.or.ke/all-reports/page/"

    user_agent = (
        "StatsChat-KE/0.2 (+https://github.com/datasciencecampus/statschat-app)"
    )
    request_kwargs = {
        "headers": {"User-Agent": user_agent},
        "timeout": (10, 20),
    }

    discovered: list[DiscoveredPdf] = []

    report_urls: list[str] = []
    for page in range(page_start, page_end + 1):
        url = f"{base_url}{page}/"
        try:
            resp = requests.get(url, **request_kwargs)
        except requests.RequestException:
            break
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.content, "html.parser")

        page_report_links = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if re.search(r"/reports/[^/]+/?$", a["href"])
        ]
        page_report_links = list(dict.fromkeys(page_report_links))
        if not page_report_links:
            break

        report_urls.extend(page_report_links)

    # De-dupe across all pages while preserving order.
    report_urls = list(dict.fromkeys(report_urls))

    def _fetch_report(report_url: str) -> list[DiscoveredPdf]:
        try:
            r = requests.get(report_url, **request_kwargs)
        except requests.RequestException:
            return []
        if r.status_code != 200:
            return []

        rs = BeautifulSoup(r.content, "html.parser")
        pdf_anchors = rs.find_all(
            "a", href=lambda href: href and str(href).lower().endswith(".pdf")
        )
        out: list[DiscoveredPdf] = []
        for a in pdf_anchors:
            pdf_url = a["href"]
            filename = Path(urlparse(pdf_url).path).name
            out.append(
                DiscoveredPdf(
                    filename=filename, pdf_url=pdf_url, report_page=report_url
                )
            )
        return out

    # Fetch report pages in parallel to avoid long, "stuck" runs for large ranges.
    # Keep concurrency modest to be kind to KNBS.
    max_workers = 8
    processed = 0
    total = len(report_urls)
    if total:
        print(f"Discovering PDFs from {total} report pages...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_fetch_report, u) for u in report_urls]
        for fut in concurrent.futures.as_completed(futures):
            try:
                discovered.extend(fut.result())
            except Exception:
                pass
            processed += 1
            if processed % 25 == 0 or processed == total:
                print(f"  processed {processed}/{total} report pages")

    return discovered


def main() -> Path:
    cfg = load_config(name="main")
    page_start = int(cfg["app"]["page_start"])
    page_end = int(cfg["app"]["page_end"])

    discovered = _discover_pdfs(page_start=page_start, page_end=page_end)

    base = Path.cwd() / "data"
    primary_dir = base / "pdf_downloads"
    latest_dir = base / "latest_pdf_downloads"

    primary_dict = _load_url_dict(primary_dir / "url_dict.json")
    latest_dict = _load_url_dict(latest_dir / "url_dict.json")

    local_filenames = set(primary_dict.keys()) | set(latest_dict.keys())

    discovered_by_filename: dict[str, list[dict[str, str]]] = {}
    per_report: dict[str, set[str]] = {}

    for d in discovered:
        discovered_by_filename.setdefault(d.filename, []).append(
            {"pdf_url": d.pdf_url, "report_page": d.report_page}
        )
        per_report.setdefault(d.report_page, set()).add(d.pdf_url)

    discovered_filenames = set(discovered_by_filename.keys())

    missing_in_local = sorted(discovered_filenames - local_filenames)
    collisions = {
        fn: items
        for fn, items in discovered_by_filename.items()
        if len({i["pdf_url"] for i in items}) > 1
    }
    multi_pdf_reports = {
        report: sorted(urls) for report, urls in per_report.items() if len(urls) > 1
    }

    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = outputs_dir / f"missing_downloads_report_{ts}.json"

    payload: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "page_start": page_start,
        "page_end": page_end,
        "discovered_count": len(discovered),
        "discovered_unique_filenames": len(discovered_filenames),
        "local_url_dict_count": len(local_filenames),
        "missing_in_local": missing_in_local,
        "collisions": collisions,
        "multi_pdf_reports": multi_pdf_reports,
    }

    out_path.write_text(json.dumps(payload, indent=2))
    print(
        "Missing-downloads check complete. "
        f"Discovered unique PDFs: {payload['discovered_unique_filenames']}. "
        f"Missing in local: {len(missing_in_local)}. "
        f"Report: {out_path}"
    )

    return out_path


if __name__ == "__main__":
    main()
