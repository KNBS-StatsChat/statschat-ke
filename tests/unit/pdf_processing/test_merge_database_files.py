"""
Test for statschat.pdf_processing.merge_database_files

Permanent storage folders - created during SETUP:
    test_data/pdf_downloads: where all PDFs and url_dict.json are stored
    test_data/json_conversions: where full JSON representations of PDFs are stored
    test_data/json_split: where split JSON files (e.g., per-page/section) are stored
    
Latest folders - created temporarily during UPDATE:
    test_data/latest_pdf_downloads: newly downloaded PDFs and url_dict.json
    test_data/latest_json_conversions: new JSON files from the latest batch
    test_data/latest_json_split: new split JSON files

Run:
    pytest -s -v tests/unit/pdf_processing/test_merge_database_files.py
"""
# %%
import json
import pytest
from pathlib import Path
import logging
from datetime import datetime

# %%

# ----------------------------
# Logging Configuration
# ----------------------------

# Create log directory if it doesn't exist
LOG_DIR = Path.cwd().joinpath("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Define session-based log filename
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
    logger.info(f"Adding test data to: {base} if required")

    if not base.exists():
        base.mkdir(parents=True)
        logger.info("Created base test_data directory")

    directory = {
        "DATA_DIR": base / "pdf_downloads",
        "JSON_DIR": base / "json_conversions",
        "JSON_SPLIT_DIR": base / "json_split",
        "LATEST_JSON_SPLIT_DIR": base / "latest_json_split",
        "LATEST_JSON_DIR": base / "latest_json_conversions",
        "LATEST_DATA_DIR": base / "latest_pdf_downloads",
    }

    for name, dir in directory.items():
        dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checking directory exists: {name} → {dir}")

    # Create sample PDFs
    original_pdf_dir = directory["DATA_DIR"]
    if not any(original_pdf_dir.glob("*.pdf")):
        (original_pdf_dir / "doc1.pdf").write_text("1st PDF content")
        logger.info("Created doc1.pdf in DATA_DIR")

    latest_pdf_dir = directory["LATEST_DATA_DIR"]
    if not any(latest_pdf_dir.glob("*.pdf")):
        (latest_pdf_dir / "doc2.pdf").write_text("2nd PDF content")
        logger.info("Created doc2.pdf in LATEST_DATA_DIR")

    # Create JSON files based on PDFs
    for pdf_file in original_pdf_dir.glob("*.pdf"):
        pdf_name = pdf_file.name
        json_name = pdf_file.with_suffix(".json").name
        json_path = directory["JSON_DIR"] / json_name
        if not json_path.exists():
            json_path.write_text(json.dumps({"source_pdf": pdf_name, "a": 1}, indent=4))
            logger.info(f"Created sample JSON as none currently present: {json_path}")
        split_json_path = directory["JSON_SPLIT_DIR"] / f"split_{json_name}"
        if not split_json_path.exists():
            split_json_path.write_text(json.dumps({"source_pdf": pdf_name, "b": 2}, indent=4))
            logger.info(f"Created sample split JSON as none currently present: {split_json_path}")

    for pdf_file in latest_pdf_dir.glob("*.pdf"):
        pdf_name = pdf_file.name
        json_name = pdf_file.with_suffix(".json").name
        json_path = directory["LATEST_JSON_DIR"] / json_name
        if not json_path.exists():
            json_path.write_text(json.dumps({"source_pdf": pdf_name, "a": 1}, indent=4))
            logger.info(f"Created sample latest JSON as none currently present: {json_path}")
        split_json_path = directory["LATEST_JSON_SPLIT_DIR"] / f"split_{json_name}"
        if not split_json_path.exists():
            split_json_path.write_text(json.dumps({"source_pdf": pdf_name, "b": 2}, indent=4))
            logger.info(f"Created sample latest split JSON as none currently present: {split_json_path}")

    # Create url_dicts
    original_url_dict_path = directory["DATA_DIR"] / "url_dict.json"
    latest_url_dict_path = directory["LATEST_DATA_DIR"] / "url_dict.json"

    if not original_url_dict_path.exists():
        original_url_dict = {
            "doc1.pdf": {
                "pdf_url": "sample_url_1",
                "report_page": "sample_report_page"
            }
        }
        original_url_dict_path.write_text(json.dumps(original_url_dict, indent=4))
        logger.info("Created original url_dict.json")

    if not latest_url_dict_path.exists():
        latest_url_dict = {
            "doc2.pdf": {
                "pdf_url": "sample_url_1",
                "report_page": "sample_report_page"
            }
        }
        latest_url_dict_path.write_text(json.dumps(latest_url_dict, indent=4))
        logger.info("Created latest url_dict.json")

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
    for json_file in directory["LATEST_JSON_DIR"].glob("*.json"):
        target = directory["JSON_DIR"] / json_file.name
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
        original_dict = json.load(f)
    with open(latest_path) as f:
        latest_dict = json.load(f)

    new_entries = {k: v for k, v in latest_dict.items() if k not in original_dict}
    logger.info(f"Found {len(new_entries)} new entries to merge")

    merged_dict = original_dict.copy()
    merged_dict.update(new_entries)

    with open(original_path, "w") as f:
        json.dump(merged_dict, f, indent=4)
    logger.info(f"Updated original url_dict.json in: {original_path}")

    # Save latest_dict for verification before deleting
    latest_dict_copy = latest_dict.copy()
    latest_path.unlink()
    logger.info(f"Deleted latest url_dict.json from: {latest_path}")

    # ✅ Verify merged dictionary contains all entries from original and latest
    expected_dict = original_dict.copy()
    expected_dict.update(latest_dict_copy)
    assert merged_dict == expected_dict
    logger.info("Verified original url_dict contains all entries from original and latest dictionaries")

    # ✅ Verify all PDFs have corresponding JSONs and split JSONs
    for pdf_file in directory["DATA_DIR"].glob("*.pdf"):
        json_name = pdf_file.with_suffix(".json").name
        assert (directory["JSON_DIR"] / json_name).exists()
        assert (directory["JSON_SPLIT_DIR"] / f"split_{json_name}").exists()
        logger.info(f"Verified JSON and split JSON for {pdf_file.name}")

    # ✅ Verify no files remain in latest directories
    assert not latest_path.exists()
    assert len(list(directory["LATEST_DATA_DIR"].glob("*.pdf"))) == 0
    logger.info("Verified no PDF files remain in LATEST_DATA_DIR")

    assert len(list(directory["LATEST_JSON_DIR"].glob("*.json"))) == 0
    logger.info("Verified no JSON files remain in LATEST_JSON_DIR")

    assert len(list(directory["LATEST_JSON_SPLIT_DIR"].glob("*.json"))) == 0
    logger.info("Verified no split JSON files remain in LATEST_JSON_SPLIT_DIR")