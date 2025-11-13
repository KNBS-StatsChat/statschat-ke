"""
Test splitting of JSON conversions done by statschat\embedding\preprocess.py

- Compares number of pages in each JSON conversion file against the number of split files created
- Makes sure no pages are lost during the splitting process

Run:
    pytest tests/unit/embedding/test_json_splitting.py
"""

import pytest
from pathlib import Path
import logging
import json
from datetime import datetime
from statschat import load_config

# ----------------------------
# Logging Configuration
# ----------------------------

# Create log directory if it doesn't exist
LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Define session-based log filename
session_name = f"test_json_splitting_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
log_file = LOG_DIR / f"{session_name}.log"

# Configure logging
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
    print("🔧 Loading configuration...")
    return load_config(name="main")

# DATA DIR
@pytest.fixture
def data_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("pdf_downloads" if mode == "SETUP" else "latest_pdf_downloads")
    logger.info(f"Using PDF directory: {path}")
    return path

# JSON CONVERSION DIR
@pytest.fixture
def json_conversions_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("json_conversions" if mode == "SETUP" else "latest_json_conversions")
    logger.info(f"Using JSON directory: {path}")
    return path

# JSON SPLIT DIR
@pytest.fixture
def json_split_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("json_split" if mode == "SETUP" else "latest_json_split")
    logger.info(f"Using JSON splits directory: {path}")
    return path

# ----------------------------
# Tests
# ----------------------------

def test_json_splits_match(json_conversions_dir, json_split_dir):
    """
    Ensure that the number of pages in each json_conversions file
    matches the number of split files in json_splits.
    Aggregates mismatches and reports them all at once.
    """
    conversion_files = list(json_conversions_dir.glob("*.json"))
    assert conversion_files, "No conversion files found!"

    mismatches = []

    for converted_file in conversion_files:
        with converted_file.open("r", encoding="utf-8") as f:
            conv_data = json.load(f)

        # Count pages in conversion file
        pages_in_conversion = len(conv_data.get("content", []))

        # Identify matching split files by ID prefix
        doc_id = str(conv_data.get("id"))
        split_files = list(json_split_dir.glob(f"{doc_id}_*.json"))
        pages_in_splits = len(split_files)

        logger.info(
            f"Checking {converted_file.name}: CONVERTED PAGES={pages_in_conversion}, JSON SPLITS={pages_in_splits}"
        )

        if pages_in_conversion != pages_in_splits:
            msg = (
                f"Mismatch for {converted_file.name}: conversion file has {pages_in_conversion} pages, "
                f"but only found {pages_in_splits} split files."
            )
            logger.warning(msg)
            mismatches.append(msg)

    # Final assertion after checking all files
    if mismatches:
        all_mismatches = "\n".join(mismatches)
        pytest.fail(f"PAGE SPLIT MISMATCHES FOUND\n{all_mismatches}")