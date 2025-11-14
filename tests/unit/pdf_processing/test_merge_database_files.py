"""
Test for statschat/pdf_processing/merge_database_files.py

Use test data storage folders - created from `create_sample_data.py`:
    test_data/pdf_downloads: where all PDFs and url_dict.json are stored
    test_data/json_conversions: where full JSON representations of PDFs are stored
    test_data/json_split: where split JSON files (e.g., per-page/section) are stored
    
    test_data/latest_pdf_downloads: newly downloaded PDFs and url_dict.json
    test_data/latest_json_conversions: new JSON files from the latest batch
    test_data/latest_json_split: new split JSON files
    
Run:
    1) python tests/utils/create_sample_data_and_folder_structure.py
    
    2) pytest -s -v tests/unit/pdf_processing/test_merge_database_files.py
"""
import json
import pytest
from pathlib import Path
import logging
from datetime import datetime

# ----------------------------
# Logging Configuration
# ----------------------------
LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

session_name = f"test_merge_database_files_{datetime.now().strftime('%Y_%m_%d_%H-%M')}"
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
def setup_test_data():
    base = Path("tests/test_data").resolve()
    directory = {
        "DATA_DIR": base / "pdf_downloads",
        "JSON_CONVERSION": base / "json_conversions",
        "JSON_SPLIT_DIR": base / "json_split",
        "LATEST_JSON_SPLIT_DIR": base / "latest_json_split",
        "LATEST_JSON_CONVERSION": base / "latest_json_conversions",
        "LATEST_DATA_DIR": base / "latest_pdf_downloads",
    }
    # Ensures folders exist (files are created by create_sample_data_and_folder_structure.py)
    for name, dir in directory.items():
        dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checked directory exists: {name} → {dir}")
    return directory

# ----------------------------
# Tests
# ----------------------------
def test_merge_database_files(setup_test_data):
    directory = setup_test_data
    logger.info("Starting test for merge_database_files.py")

    # Move PDFs
    for pdf_file in directory["LATEST_DATA_DIR"].glob("*.pdf"):
        target = directory["DATA_DIR"] / pdf_file.name
        pdf_file.rename(target)
        logger.info(f"Moved PDF: {pdf_file.name} → {target}")

    # Move JSON conversions
    for json_file in directory["LATEST_JSON_CONVERSION"].glob("*.json"):
        target = directory["JSON_CONVERSION"] / json_file.name
        json_file.rename(target)
        logger.info(f"Moved JSON: {json_file.name} → {target}")

    # Move split JSONs
    for json_split_file in directory["LATEST_JSON_SPLIT_DIR"].glob("*.json"):
        target = directory["JSON_SPLIT_DIR"] / json_split_file.name
        json_split_file.rename(target)
        logger.info(f"Moved split JSON: {json_split_file.name} → {target}")

    # Merge URL dicts
    original_path = directory["DATA_DIR"] / "url_dict.json"
    latest_path = directory["LATEST_DATA_DIR"] / "url_dict.json"

    with open(original_path) as f:
        original_url_dict = json.load(f)
    with open(latest_path) as f:
        latest_url_dict = json.load(f)

    new_entries = {key: value for key, value in latest_url_dict.items() if key not in original_url_dict}
    merged_dict = original_url_dict.copy()
    merged_dict.update(new_entries)

    with open(original_path, "w") as f:
        json.dump(merged_dict, f, indent=4)

    latest_dict_copy = latest_url_dict.copy()
    latest_path.unlink()

    # Verify merged dictionary contains all entries
    expected_dict = original_url_dict.copy()
    expected_dict.update(latest_dict_copy)
    assert merged_dict == expected_dict

    # Verify all PDFs have corresponding JSON conversions
    for pdf_file in directory["DATA_DIR"].glob("*.pdf"):
        json_name = pdf_file.with_suffix(".json").name
        assert (directory["JSON_CONVERSION"] / json_name).exists()

    # Verify no files remain in latest directories
    assert not latest_path.exists()
    assert len(list(directory["LATEST_DATA_DIR"].glob("*.pdf"))) == 0
    assert len(list(directory["LATEST_JSON_CONVERSION"].glob("*.json"))) == 0
    assert len(list(directory["LATEST_JSON_SPLIT_DIR"].glob("*.json"))) == 0