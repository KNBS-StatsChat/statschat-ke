"""Run tests for PDF text extraction and comparison with `pytest tests/e2e/test_pdf_text_extraction.py -s`"""

import pytest
import logging
from pathlib import Path
from datetime import datetime
from statschat import load_config
from pdf_text_extraction_test_functions import check_folders_text_extraction
import pdfplumber


# ----------------------------
# Logging Configuration
# ----------------------------

LOG_DIR = Path.cwd() / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

session_name = f"test_pdf_text_extraction_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
log_file = LOG_DIR / f"{session_name}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
    logger.info("🔧 Loading configuration...")
    return load_config(name="main")

@pytest.fixture
def data_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("pdf_downloads" if mode == "SETUP" else "latest_pdf_downloads")
    logger.info(f"📁 Using PDF directory: {path}")
    return path

@pytest.fixture
def json_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("json_conversions" if mode == "SETUP" else "latest_json_conversions")
    logger.info(f"📁 Using JSON directory: {path}")
    return path

# ----------------------------
# Tests
# ----------------------------

def test_check_folders_text_extraction(data_dir, json_dir):
    logger.info("📂 Starting PDF text extraction check")
    check_folders_text_extraction(data_dir, json_dir)
    logger.info("✅ PDF check completed. See log")
