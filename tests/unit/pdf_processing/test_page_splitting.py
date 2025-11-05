"""
Unit tests for PDF page splitting functionality.

Tests ensure that PDF to JSON conversion maintains page integrity by:
- Correctly counting pages in PDF files
- Validating that JSON conversions contain the expected number of pages
- Matching JSON files to their source PDFs

Run with: pytest tests/unit/pdf_processing/test_page_splitting.py -s
"""
import pytest
from pathlib import Path
import logging
from datetime import datetime
from statschat import load_config
from .page_splitting_test_functions import get_pdf_page_counts, validate_page_splitting
# ----------------------------
# Logging Configuration
# ----------------------------

# Create log directory if it doesn't exist
LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

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
    """
    Test that PDF page counts are correctly extracted from all PDF files.
    
    Validates:
    - Returns a dictionary
    - All page counts are positive integers
    - At least some PDFs were found (non-empty result)
    """
    logger.info("Running test_get_pdf_page_counts")
    page_counts = get_pdf_page_counts(data_dir)
    
    logger.info(f"Found {len(page_counts)} PDFs with page counts")
    
    # Basic structure validation
    assert isinstance(page_counts, dict), "Result should be a dictionary"
    
    # Validate we found some PDFs
    assert len(page_counts) > 0, f"No PDFs found in {data_dir}"
    
    # Validate all page counts are positive integers
    for pdf_name, count in page_counts.items():
        assert isinstance(count, int), f"{pdf_name}: page count should be an integer"
        assert count > 0, f"{pdf_name}: page count should be positive, got {count}"
        logger.info(f"  {pdf_name}: {count} pages")


def test_validate_page_splitting(json_dir, data_dir):
    """
    Test that JSON conversions maintain correct page counts from source PDFs.
    
    Validates:
    - All JSON files have required fields
    - Filenames match between PDFs and JSON files
    - Page counts match between PDFs and JSON files
    - All validations pass (no mismatches)
    """
    logger.info("Running test_validate_page_splitting")
    expected_counts = get_pdf_page_counts(data_dir)
    results = validate_page_splitting(json_dir, expected_counts)
    
    logger.info(f"Validated {len(results)} JSON files")
    
    # Validate we found some results
    assert len(results) > 0, f"No JSON files found in {json_dir}"
    
    # Track validation failures for detailed reporting
    failures = []
    
    for result in results:
        # Check for error field (indicates processing failure)
        if "error" in result:
            failures.append(f"{result['json_file']}: {result['error']}")
            logger.error(f"Error processing {result['json_file']}: {result['error']}")
            continue
        
        # Validate required fields exist
        assert "json_file" in result, "Result missing 'json_file' field"
        assert "filename_match_found" in result, f"{result['json_file']}: missing 'filename_match_found'"
        assert "page_count_matches" in result, f"{result['json_file']}: missing 'page_count_matches'"
        
        json_file = result['json_file']
        filename_match = result.get('filename_match_found')
        page_match = result.get('page_count_matches')
        
        logger.info(
            f"{json_file}: "
            f"filename_match={filename_match}, "
            f"page_match={page_match}, "
            f"last_page={result.get('last_page_number_from_json_content')}, "
            f"expected={result.get('expected_page_count_from_pdf')}"
        )
        
        # Track failures for detailed error messages
        if not filename_match:
            failures.append(
                f"{json_file}: No matching PDF found "
                f"(extracted name: {result.get('pdf_filename_in_json')})"
            )
        
        if not page_match:
            failures.append(
                f"{json_file}: Page count mismatch "
                f"(JSON: {result.get('last_page_number_from_json_content')}, "
                f"PDF: {result.get('expected_page_count_from_pdf')})"
            )
    
    # Report all failures together for easier debugging
    if failures:
        failure_msg = "\n".join([f"  - {f}" for f in failures])
        pytest.fail(f"Page splitting validation failures:\n{failure_msg}")
    
    logger.info("✅ All page splitting validations passed")
