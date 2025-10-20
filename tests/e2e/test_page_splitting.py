""""Run tests for page splitting functionality with `pytest tests/e2e`"""

import pytest
from pathlib import Path
from statschat import load_config
from page_splitting_test_functions import get_pdf_page_counts, validate_page_splitting  # adjust import

@pytest.fixture
def config():
    return load_config(name="main")

@pytest.fixture
def data_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    return base.joinpath("pdf_downloads" if mode == "SETUP" else "latest_pdf_downloads")

@pytest.fixture
def json_dir(config):
    mode = config["preprocess"]["mode"].upper()
    base = Path.cwd().joinpath("data")
    return base.joinpath("json_conversions" if mode == "SETUP" else "latest_json_conversions")

def test_get_pdf_page_counts(data_dir):
    page_counts = get_pdf_page_counts(data_dir)
    assert isinstance(page_counts, dict)
    assert all(isinstance(v, int) for v in page_counts.values())

def test_validate_page_splitting(json_dir, data_dir):
    expected_counts = get_pdf_page_counts(data_dir)
    results = validate_page_splitting(json_dir, expected_counts)
    assert isinstance(results, list)
    for result in results:
        assert "json_file" in result
        assert "filename_match_found" in result
        assert "page_count_matches" in result
