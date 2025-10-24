'''
This script tests scraping logic and behaviour of 'pdf_downloader.py' when in "SETUP" mode with "pytest tests/e2e/test_pdf_downloader_setup.py"
--------------------------------
1) Gets sample PDF with metadata using a public URL from py-pdf/sample-files GitHub repository. 

2) Checks metadata status of PDF

3) Each expected metadata field is logged as FOUND or MISSING.

4) PDF saved to tests/test_data/pdf_downloads/ to mirror production logic.

5) Mirrors behavior of pdf_downloader.py and keeps test environment consistent

6) Creates a url_dict.json file in tests/test_data/pdf_downloads with the correct structure - but with dummy report_url

7) Doesn't take into account "get_abstract_metadata" function if PDF metadata in missing
--------------------------------
'''
import requests
import logging
import pytest
from pathlib import Path
from datetime import datetime
import PyPDF2
from statschat import load_config
import json

# ----------------------------
# Logging Configuration
# ----------------------------

LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

session_name = f"test_pdf_downloader_setup_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
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
# Test Function
# ----------------------------

def test_setup_mode(data_dir):
    """
    Downloads a sample PDF and logs which metadata fields are present or missing.
    """
    # May need to adapt if wanting to work with PDFs on KNBS website as gets missing metadata from another page
    logger.info("Starting test: SETUP mode")
    
    pdf_url = "https://github.com/py-pdf/sample-files/raw/main/001-trivial/minimal-document.pdf" # maybe change to KNBS PDF
    pdf_name = "minimal-document.pdf"
    report_url = "https://github.com/reports/minimal-document.pdf" # "https://www.knbs.or.ke/reports/sample-report-page/" # doesn't exist for this sample PDF or for KNBS PDF
    
  # 'report_url' variable:
  # 1) Helps document the expected structure of a real url_dict entry.
  # 2) Mirrors production logic, which includes report_page.

    pdf_path = data_dir / pdf_name

    response = requests.get(pdf_url)
    assert response.status_code == 200, f"Failed to download PDF: {pdf_url}"

    with open(pdf_path, "wb") as f:
        f.write(response.content)

    logger.info(f"Downloaded PDF to {pdf_path}")

    reader = PyPDF2.PdfReader(pdf_path)
    meta = reader.metadata

    # Specific to KNBS PDFs
    expected_fields = [
        "title", "author", "producer",
        "creation_date", "modification_date"
    ]

    # Create url_dict entry
    url_dict = {
        pdf_name: {
            "pdf_url": pdf_url,
            "report_page": report_url
        }
    }

    # Save to url_dict.json in the same folder
    url_dict_path = data_dir / "url_dict.json"
    with open(url_dict_path, "w", encoding="utf-8") as f:
        json.dump(url_dict, f, indent=4)

    logger.info(f"Saved url_dict.json to {url_dict_path}")
    
    logger.info(f"Metadata check for SETUP mode: {pdf_name}")
    for field in expected_fields:
        value = getattr(meta, field, None)
        status = "MISSING" if not value else "FOUND"
        logger.info(f"{field}: {status}")
