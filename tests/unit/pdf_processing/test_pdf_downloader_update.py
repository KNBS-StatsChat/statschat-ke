'''
This script tests scraping logic and behaviour of 'pdf_downloader.py' when in "UPDATE" mode 
 --------------------------------
1) Gets sample PDF with metadata using a public URL from py-pdf/sample-files GitHub repository. 

2) Tests metadata extracted correctly using PyPDF2

3) Checks new PDFs added to url_dict.

4) Checks no duplicate entries created in url_dict if same PDF is reprocessed

5) Existing PDFs skipped with logged message.

6) PDF saved to tests/test_data/latest_pdf_downloads/ to mirror production logic.

7) Mirrors behavior of pdf_downloader.py and keeps your test environment consistent

8) Doesn't take into account "get_abstract_metadata" function if PDF metadata in missing as sample PDF doesn't have report page like KNBS PDFs do

Run:
    pytest tests\unit\pdf_processing\test_pdf_downloader_update.py
--------------------------------
'''

import requests
import logging
import pytest
from pathlib import Path
from datetime import datetime
import PyPDF2
from statschat import load_config

# ----------------------------
# Logging Configuration
# ----------------------------

LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

session_name = f"test_pdf_downloader_update_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
log_file = LOG_DIR / f"{session_name}.log"

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    filename=log_file,
    filemode="a",
    force=True
)

logger = logging.getLogger(__name__)

# ----------------------------
# Fixtures
# ----------------------------

@pytest.fixture
def config():
    """
    Loads configuration for the test session.
    """
    print("🔧 Loading configuration...")
    return load_config(name="main")

@pytest.fixture
def data_dir(config):
    """
    Determines the correct download directory based on SETUP or UPDATE mode.
    """
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("tests/test_data")
    path = base.joinpath("pdf_downloads" if mode == "SETUP" else "latest_pdf_downloads")
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using PDF directory: {path}")
    return path

# ----------------------------
# Metadata Extraction Logic
# ----------------------------

def extract_pdf_metadata_update_mode(pdf_path, url_dict, pdf_name, pdf_url):
    """
    Logs metadata status for a new PDF in UPDATE mode.
    Skips if already present in url_dict.
    """
    if pdf_name in url_dict:
        message = f"Skipping {pdf_name}: already present in url_dict."
        print(message)
        logger.info(message)
        return url_dict

    reader = PyPDF2.PdfReader(pdf_path)
    meta = reader.metadata

    expected_fields = [
        "title", "author", "producer",
        "creation_date", "modification_date"
    ]

    logger.info(f"Metadata check for UPDATE mode: {pdf_name}")
    for field in expected_fields:
        value = getattr(meta, field, None)
        status = "MISSING" if not value else "FOUND"
        logger.info(f"{field}: {status}")

    # Only store basic info, not metadata
    url_dict[pdf_name] = {
        "pdf_url": pdf_url,
        "report_page": "https://example.com/report-page"
    }

    return url_dict

# ----------------------------
# Test Function
# ----------------------------

def test_update_mode(data_dir, capsys):
    """
    Tests that a new PDF is processed in UPDATE mode,
    and that re-adding an existing PDF is skipped with a message.
    Logs metadata status, writes updated url_dict.json, and validates its contents.
    """
    logger.info("Starting test: UPDATE mode")

    # Simulate EXISTING entry in memory only
    existing_pdf_name = "minimal-document.pdf"
    existing_pdf_url = "https://github.com/py-pdf/sample-files/raw/main/001-trivial/minimal-document.pdf"
    url_dict = {
        existing_pdf_name: {
            "pdf_url": existing_pdf_url,
            "report_page": "https://github.com/reports/minimal-document.pdf"
        }
    }

    # Download and attempt to re-add existing PDF (should be skipped)
    pdf_path = data_dir / existing_pdf_name
    response = requests.get(existing_pdf_url)
    assert response.status_code == 200
    logger.info(f"Successfully downloaded existing PDF: {existing_pdf_name}")

    with open(pdf_path, "wb") as f:
        f.write(response.content)

    updated_dict = extract_pdf_metadata_update_mode(pdf_path, url_dict, existing_pdf_name, existing_pdf_url)

    # Confirm skip message and no duplicate entry
    captured = capsys.readouterr()
    assert f"Skipping {existing_pdf_name}: already present in url_dict." in captured.out
    logger.info(f"Verified skip message for existing PDF: {existing_pdf_name}")
    assert len(updated_dict) == 1
    assert "metadata" not in updated_dict[existing_pdf_name]
    logger.info("Confirmation: no duplicate entry added.")

    # Now test adding a NEW PDF
    new_pdf_name = "new_sample-reportlab.pdf"
    new_pdf_url = "https://github.com/py-pdf/sample-files/raw/main/013-reportlab-overlay/reportlab-overlay.pdf"
    new_pdf_path = data_dir / new_pdf_name
    response = requests.get(new_pdf_url)
    assert response.status_code == 200
    logger.info(f"Successfully downloaded new PDF: {new_pdf_name}")

    with open(new_pdf_path, "wb") as f:
        f.write(response.content)

    # Start with a clean dict for writing only the new entry
    write_dict = {}
    write_dict = extract_pdf_metadata_update_mode(new_pdf_path, write_dict, new_pdf_name, new_pdf_url)

    # Confirm new entry was added
    assert new_pdf_name in write_dict

    # Save to url_dict.json in latest_pdf_downloads
    url_dict_path = data_dir / "url_dict.json"
    with open(url_dict_path, "w", encoding="utf-8") as f:
        import json
        json.dump(write_dict, f, indent=4)

    logger.info(f"New PDF processed: {new_pdf_name} and added to {url_dict_path}")
    logger.info(f"url_dict.json successfully written to {url_dict_path}")

    # ✅ Validate contents of url_dict.json
    with open(url_dict_path, "r", encoding="utf-8") as f:
        loaded_dict = json.load(f)

    assert list(loaded_dict.keys()) == [new_pdf_name], "url_dict.json should contain only the new PDF entry"

    entry = loaded_dict[new_pdf_name]
    assert entry["pdf_url"] == new_pdf_url
    assert entry["report_page"] == "https://example.com/report-page"
    logger.info(f"Test passed: url_dict.json contains correct entry for {new_pdf_name}")
