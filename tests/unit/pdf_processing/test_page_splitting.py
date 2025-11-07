"""Run tests for page splitting functionality when converting PDF to JSON with `pytest tests/unit/pdf_processing/test_page_splitting.py -s -W always`"""

# %%
import pytest
from pathlib import Path
import logging
from datetime import datetime
from statschat import load_config
from .page_splitting_test_functions import get_pdf_page_counts, validate_page_splitting
import warnings

# %%
# ----------------------------
# Logging Configuration
# ----------------------------

# Create log directory if it doesn't exist
LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# %%

# Define session-based log filename
session_name = f"test_page_splitting_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
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

@pytest.fixture
def data_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("pdf_downloads" if mode == "SETUP" else "latest_pdf_downloads")
    logger.info(f"Using PDF directory: {path}")
    return path

@pytest.fixture
def json_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    path = base.joinpath("json_conversions" if mode == "SETUP" else "latest_json_conversions")
    logger.info(f"Using JSON directory: {path}")
    return path

# ----------------------------
# Tests
# ----------------------------

def test_get_pdf_page_counts(data_dir):
    logger.info("Running test_get_pdf_page_counts")
    page_counts = get_pdf_page_counts(data_dir)
    logger.info(f"Found {len(page_counts)} PDFs with page counts")
    assert isinstance(page_counts, dict)
    assert all(isinstance(v, int) for v in page_counts.values())

def test_validate_page_splitting(json_dir, data_dir):
    logger.info("Running test_validate_page_splitting")
    expected_counts = get_pdf_page_counts(data_dir)
    results = validate_page_splitting(json_dir, expected_counts)
    logger.info(f"Validated {len(results)} JSON files")

    for result in results:
        logger.info(
            f"{result['json_file']}: match_found={result.get('filename_match_found')}, "
            f"page_match={result.get('page_count_matches')}"
        )
        assert "json_file" in result
        assert "filename_match_found" in result
        assert "page_count_matches" in result

        if not result.get("page_count_matches"):
            warnings.warn(
                f"page count mismatch for {result['json_file']}",
                UserWarning
            )

