"""Unit tests for statschat.pdf_processing.pdf_to_json.

These tests focus on high-ROI, deterministic behaviors:
- date parsing/fallback rules
- keyword extraction
- JSON payload invariants and schema produced by build_json
"""

import json
from datetime import datetime

import pytest

from statschat.pdf_processing import pdf_to_json


def test_extract_pdf_creation_date_prefers_metadata():
    """Parses and uses the PDF metadata creation date when present."""
    metadata = {"creationDate": "D:20240115000000Z"}
    date, counter = pdf_to_json.extract_pdf_creation_date(
        metadata, "ignored.pdf", counter=0
    )
    assert date == "2024-01-15"
    assert counter == 0


def test_extract_pdf_creation_date_falls_back_to_filename_year():
    """Falls back to a year parsed from the filename when metadata is missing."""
    metadata = {}
    date, counter = pdf_to_json.extract_pdf_creation_date(
        metadata, "2018-Survey-Report.pdf", counter=2
    )
    assert date == "2018-01-01"
    assert counter == 2


def test_extract_pdf_creation_date_uses_today_when_no_hints():
    """Uses today's date when neither metadata nor filename hints are available."""
    metadata = {}

    class _FixedDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 14)

    # Avoid flakiness around midnight by freezing now()
    original_datetime = pdf_to_json.datetime
    pdf_to_json.datetime = _FixedDateTime
    try:
        date, counter = pdf_to_json.extract_pdf_creation_date(
            metadata, "no-date.pdf", counter=0
        )
    finally:
        pdf_to_json.datetime = original_datetime

    assert date == "2026-01-14"
    assert counter == 1


def test_convert_to_date_parses_month_year():
    assert pdf_to_json.convert_to_date("May 2025") == "2025-05-01"


def test_convert_to_date_parses_year_only():
    assert pdf_to_json.convert_to_date("2025") == "2025-01-01"


def test_convert_to_date_rejects_invalid():
    with pytest.raises(ValueError):
        pdf_to_json.convert_to_date("not a date")


def test_extract_url_keywords_from_filename_unique_and_ordered():
    assert pdf_to_json.extract_url_keywords_from_filename(
        "2018-Survey-Test-2018.pdf"
    ) == ["2018", "Survey", "Test"]


def test_extract_pdf_modification_date_falls_back_if_too_old():
    # ModDate more than 5 years earlier than creation should fall back.
    metadata = {"modDate": "D:20100101000000Z"}
    assert (
        pdf_to_json.extract_pdf_modification_date(metadata, "2019-01-01")
        == "2019-01-01"
    )


def test_extract_pdf_modification_date_returns_moddate_when_reasonable():
    metadata = {"modDate": "D:20200102000000Z"}
    assert (
        pdf_to_json.extract_pdf_modification_date(metadata, "2019-01-01")
        == "2020-01-02"
    )


def test_assemble_pdf_info_blanks_overview_when_title_only():
    info = pdf_to_json.assemble_pdf_info(
        file_name="2018-Test.pdf",
        pdf_metadata={},
        pdf_add_metadata={
            "overview": "2018 Test ",
            "publication_theme": "Theme",
            "publication_type": "Report",
        },
        pdf_url="https://example.com/2018-test.pdf",
        pdf_creation_date="2018-01-01",
        content=[{"page_number": 1, "page_url": "u#page=1", "page_text": "x"}],
        id_factory=lambda: "1234567",
    )

    assert info["id"] == "1234567"
    assert info["title"] == "2018 Test"
    assert info["overview"] == " "


def test_build_json_writes_expected_schema(tmp_path):
    json_dir = tmp_path / "out"

    def fake_metadata_extractor(_path):
        return "2018-Test.pdf", {"modDate": "D:20240102000000Z"}

    def fake_abstract_getter(_report_page: str) -> dict:
        return {
            "date": "May 2025",
            "overview": "Overview text",
            "publication_type": "Report",
            "publication_theme": "Economy",
            "pdf_abstract_url": "https://example.com/abstract",
        }

    def fake_text_extractor(_pdf_path, _pdf_url):
        return [
            {"page_number": 1, "page_url": "u#page=1", "page_text": "A"},
            {"page_number": 2, "page_url": "u#page=2", "page_text": "B"},
        ]

    out_path = pdf_to_json.build_json(
        pdf_file_path=tmp_path / "2018-Test.pdf",
        pdf_website_url="https://example.com/2018-test.pdf",
        report_page="https://knbs.or.ke/reports/whatever",
        JSON_DIR=json_dir,
        abstract_metadata_getter=fake_abstract_getter,
        metadata_extractor=fake_metadata_extractor,
        text_extractor=fake_text_extractor,
        id_factory=lambda: "9999999",
    )

    assert out_path.exists()
    payload = json.loads(out_path.read_text())

    # Core schema
    assert payload["id"] == "9999999"
    assert payload["title"] == "2018 Test"
    assert payload["release_date"] == "2025-05-01"
    assert payload["modification_date"] == "2024-01-02"
    assert payload["latest"] is True
    assert payload["url"] == "https://example.com/2018-test.pdf"
    assert payload["url_keywords"] == ["2018", "Test"]

    # Content contract
    assert isinstance(payload["content"], list)
    assert [p["page_number"] for p in payload["content"]] == [1, 2]
