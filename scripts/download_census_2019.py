"""One-off script to download 2019 Kenya Census PDFs.

The census 2019 report page was previously excluded from the scraper by a
hard-coded filter.  Now that the filter has been removed, this script
back-fills the missing PDFs without re-running the full scraper across
all 50 index pages.

Usage:
    python scripts/download_census_2019.py
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_DIR = Path.cwd() / "data"
DATA_DIR = BASE_DIR / "pdf_downloads"
URL_DICT_PATH = DATA_DIR / "url_dict.json"

CENSUS_PAGES = [
    "https://www.knbs.or.ke/reports/kenya-census-2019/",
    "https://www.knbs.or.ke/reports/kenya-census-2009/",
]

USER_AGENT = "StatsChat-KE/0.2 (+https://github.com/datasciencecampus/statschat-app)"
REQUEST_KWARGS = {
    "headers": {"User-Agent": USER_AGENT},
    "timeout": (10, 60),
}


def main() -> None:
    # Load existing url_dict
    if URL_DICT_PATH.exists():
        with open(URL_DICT_PATH) as f:
            url_dict: dict = json.load(f)
        print(f"Loaded url_dict.json with {len(url_dict)} entries")
    else:
        print("No url_dict.json found. Exiting.")
        sys.exit(1)

    existing_filenames = set(url_dict.keys())

    # Discover PDF links from census pages
    all_pdf_entries: dict[str, str] = {}  # pdf_url -> report_page
    for page_url in CENSUS_PAGES:
        print(f"\nFetching {page_url} ...")
        try:
            resp = requests.get(page_url, **REQUEST_KWARGS)
        except requests.RequestException as exc:
            print(f"  Failed to fetch: {exc}")
            continue
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")
        pdf_anchors = soup.find_all(
            "a", href=lambda h: h and h.lower().endswith(".pdf")
        )
        for a in pdf_anchors:
            pdf_url = a["href"]
            pdf_name = Path(urlparse(pdf_url).path).name
            if pdf_name not in existing_filenames:
                all_pdf_entries[pdf_url] = page_url
        print(
            f"  Found {len(pdf_anchors)} PDF links, {len(all_pdf_entries)} new so far"
        )

    if not all_pdf_entries:
        print("\nNo new PDFs to download.")
        return

    print(f"\nDownloading {len(all_pdf_entries)} new census PDFs...")

    downloaded = 0
    failures = []
    fmt = "[{elapsed}<{remaining}]{n_fmt}/{total_fmt}|{l_bar}{bar} {rate_fmt}"
    for pdf_url, report_page in tqdm(
        all_pdf_entries.items(),
        desc="Downloading",
        bar_format=fmt,
        colour="yellow",
        dynamic_ncols=True,
    ):
        pdf_name = Path(urlparse(pdf_url).path).name
        file_path = DATA_DIR / pdf_name

        try:
            resp = requests.get(pdf_url, **REQUEST_KWARGS)
        except requests.RequestException as exc:
            failures.append(f"  {pdf_name}: {exc}")
            continue

        if resp.status_code != 200:
            failures.append(f"  {pdf_name}: HTTP {resp.status_code}")
            continue

        content = resp.content or b""
        with open(file_path, "wb") as f:
            f.write(content)

        url_dict[pdf_name] = {"pdf_url": pdf_url, "report_page": report_page}
        downloaded += 1

        if not content.startswith(b"%PDF-"):
            failures.append(f"  {pdf_name}: content is not a valid PDF")

    # Save updated url_dict
    with open(URL_DICT_PATH, "w") as f:
        json.dump(url_dict, f, indent=2)

    print(
        f"\nDone. Downloaded {downloaded} PDFs. url_dict now has {len(url_dict)} entries."
    )
    if failures:
        print(f"\n{len(failures)} issues:")
        for msg in failures:
            print(msg)


if __name__ == "__main__":
    main()
