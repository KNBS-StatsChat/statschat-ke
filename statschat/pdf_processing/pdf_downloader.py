# %%
import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import json
from tqdm import tqdm
import statschat
import re
from datetime import datetime
from requests.exceptions import RequestException


def main():

    # %% Configuration

    # Load configuration
    config = statschat.load_config(name="main")
    PDF_FILES = config["preprocess"]["mode"].upper()

    # Set directories
    BASE_DIR = Path.cwd().joinpath("data")
    DATA_DIR = BASE_DIR.joinpath(
        "pdf_downloads" if PDF_FILES == "SETUP" else "latest_pdf_downloads"
    )
    OUTPUT_URL_DIR = BASE_DIR.joinpath(
        "pdf_downloads" if PDF_FILES == "SETUP" else "latest_pdf_downloads"
    )
    ORIGINAL_URL_DICT_PATH = BASE_DIR.joinpath("pdf_downloads/url_dict.json")

    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_URL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"STARTING DATABASE {PDF_FILES}. PLEASE WAIT...")

    user_agent = (
        "StatsChat-KE/0.2 (+https://github.com/datasciencecampus/statschat-app)"
    )
    request_kwargs = {
        "headers": {"User-Agent": user_agent},
        # (connect timeout, read timeout)
        "timeout": (10, 20),
    }

    # Set path for new url_dict.json (where new entries are saved)
    url_dict_path = OUTPUT_URL_DIR / "url_dict.json"

    # Initialize URL dictionary
    if PDF_FILES == "SETUP":
        url_dict = {}  # Start fresh, do not load anything

    elif PDF_FILES == "UPDATE":
        if ORIGINAL_URL_DICT_PATH.exists():
            with open(ORIGINAL_URL_DICT_PATH, "r") as json_file:
                original_url_dict = json.load(json_file)
                print(f"Loaded existing url_dict.json from {ORIGINAL_URL_DICT_PATH}")
        else:
            print(
                "No existing url_dict.json found in pdf_downloads. Exiting update mode."
            )
            sys.exit(1)  # Nothing to update if there's no record

        url_dict = {}  # This will store only new entries

    page = config["app"]["page_start"]
    page_end = config["app"]["page_end"]

    max_pdfs = config.get("app", {}).get("max_pdfs")

    max_pages = 100 if PDF_FILES == "SETUP" else page_end  # Limit to 5 for updates

    # %% Scrape intermediate report pages and extract PDF links
    all_pdf_entries = {}  # {"pdf_url": "report_page", ...}
    visited_report_pages = set()

    # Set base URL for KNBS reports
    base_url = "https://www.knbs.or.ke/all-reports/page/"

    print("IN PROGRESS.")
    while page <= page_end:
        # Trigger page limit for UPDATE mode
        if max_pages and page > max_pages:
            print(f"Reached page limit ({max_pages}) for UPDATE mode. Stopping search.")
            break

        # Visit each page and extract report links
        url = f"{base_url}{page}/"
        response = requests.get(url, **request_kwargs)

        if response.status_code != 200:
            print(f"Failed to access {url}. Stopping search.")
            break

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all links that match the /reports/ pattern
        report_links = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if re.search(r"/reports/[^/]+/?$", a["href"])
        ]

        report_links = list(dict.fromkeys(report_links))
        # remove duplicate reports
        if not report_links:
            print(f"Reached page limit ({page}). Stopping search.")
            break

        # print(report_links)

        print(f"Found {len(report_links)} report pages on page {page}")

        # Step 2: Visit each report page and extract PDF links
        for report_url in report_links:
            if report_url in visited_report_pages:
                continue  # Skip already visited report pages

            visited_report_pages.add(report_url)
            try:
                report_response = requests.get(report_url, **request_kwargs)
            except RequestException as exc:
                print(f"Failed to access report page: {report_url} ({exc})")
                continue

            if report_response.status_code != 200:
                print(f"Failed to access report page: {report_url}")
                continue

            report_soup = BeautifulSoup(report_response.content, "html.parser")

            pdf_anchors = report_soup.find_all(
                "a", href=lambda href: href and href.lower().endswith(".pdf")
            )

            # If pdf links found - retain all of them (some report pages host multiple PDFs)
            for a in pdf_anchors:
                pdf_link = a["href"]
                all_pdf_entries[pdf_link] = report_url

                # If we're only sampling a few PDFs, stop scraping early.
                if isinstance(max_pdfs, int) and max_pdfs > 0:
                    if len(all_pdf_entries) >= max_pdfs:
                        break

            if (
                isinstance(max_pdfs, int)
                and max_pdfs > 0
                and len(all_pdf_entries) >= max_pdfs
            ):
                break

        if (
            isinstance(max_pdfs, int)
            and max_pdfs > 0
            and len(all_pdf_entries) >= max_pdfs
        ):
            print(
                f"Found {len(all_pdf_entries)} PDFs; stopping early due to max_pdfs={max_pdfs}"
            )
            break

        page += 1

    print(f"Total PDFs found: {len(all_pdf_entries)}")

    # %% If in UPDATE mode, filter only new PDFs
    if PDF_FILES == "UPDATE":
        existing_urls = set(
            entry["pdf_url"]
            for entry in original_url_dict.values()
            if isinstance(entry, dict) and "pdf_url" in entry.keys()
        )

        # Filter `all_pdf_entries` to include only new entries
        new_entries = {
            pdf_url: report_page
            for pdf_url, report_page in all_pdf_entries.items()
            if pdf_url not in existing_urls
        }

        if not new_entries:
            print("No new PDFs found. Exiting update process.")
            sys.exit(0)

        print(f"Found {len(new_entries)} new PDFs to download.")
        all_pdf_entries = new_entries  # Replace with filtered dictionary

    # Optional: cap total downloads for quicker sampling/debugging
    if isinstance(max_pdfs, int) and max_pdfs > 0 and len(all_pdf_entries) > max_pdfs:
        # Deterministic selection by URL
        all_pdf_entries = dict(list(sorted(all_pdf_entries.items()))[:max_pdfs])
        print(f"Capped downloads to max_pdfs={max_pdfs}")

    # %% Download PDFs and Update URL Dictionary
    format = (
        "[{elapsed}<{remaining}]{n_fmt}/{total_fmt}|{l_bar}{bar} {rate_fmt}{postfix}"
    )
    failures: list[dict] = []
    for pdf, report_page in tqdm(
        all_pdf_entries.items(),
        desc="DOWNLOADING PDF FILES:",
        bar_format=format,
        colour="yellow",
        total=len(all_pdf_entries),
        dynamic_ncols=True,
    ):
        pdf_url = pdf
        report_url = report_page
        parsed_url = urlparse(pdf_url)
        pdf_name = Path(parsed_url.path).name

        file_path = DATA_DIR / pdf_name

        # Download PDF
        try:
            response = requests.get(pdf_url, **request_kwargs)
        except RequestException as exc:
            failures.append(
                {
                    "pdf_name": pdf_name,
                    "pdf_url": pdf_url,
                    "report_page": report_url,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
            print(f"Failed to download: {pdf_url} ({exc})")
            continue

        if response.status_code == 200:
            content = response.content or b""
            with open(file_path, "wb") as file:
                file.write(content)

            # Store both pdf_url and report page
            url_dict[pdf_name] = {"pdf_url": pdf_url, "report_page": report_url}

            # Flag non-PDF responses that were saved (useful for later auditing)
            if not content.startswith(b"%PDF-"):
                failures.append(
                    {
                        "pdf_name": pdf_name,
                        "pdf_url": pdf_url,
                        "report_page": report_url,
                        "error": "Downloaded content does not start with %PDF-",
                        "error_type": "NonPdfResponse",
                    }
                )
        else:
            failures.append(
                {
                    "pdf_name": pdf_name,
                    "pdf_url": pdf_url,
                    "report_page": report_url,
                    "error": f"HTTP {response.status_code}",
                    "error_type": "HttpError",
                }
            )
            print(f"Failed to download: {pdf_url}")

    # %% Save New URL Dictionary to JSON (Only new entries)
    with open(url_dict_path, "w") as json_file:
        json.dump(url_dict, json_file, indent=4)
        print(f"Saved new url_dict.json to {url_dict_path}")

    if failures:
        outputs_dir = Path.cwd() / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = outputs_dir / f"pdf_download_report_{PDF_FILES.lower()}_{ts}.json"
        report_path.write_text(
            json.dumps(
                {
                    "mode": PDF_FILES,
                    "attempted": len(all_pdf_entries),
                    "saved": len(url_dict),
                    "failures": failures,
                },
                indent=2,
            )
        )
        print(f"Wrote download report to {report_path}")

    if PDF_FILES == "UPDATE":
        print("Finished downloading new PDF files.")

    if PDF_FILES == "SETUP":
        print("Finished downloading all PDF files.")


if __name__ == "__main__":
    main()
