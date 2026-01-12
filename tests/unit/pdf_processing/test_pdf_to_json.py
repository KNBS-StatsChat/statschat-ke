"""
Unit tests for pdf_to_json utility helpers.

Focus on creation/modification date extraction fallbacks.
"""

from datetime import datetime
from statschat.pdf_processing.pdf_to_json import extract_pdf_creation_date


def test_extract_pdf_creation_date_prefers_metadata():
    metadata = {"creationDate": "D:20240115000000Z"}
    date, counter = extract_pdf_creation_date(metadata, "ignored.pdf", counter=0)
    assert date == "2024-01-15"
    assert counter == 0


def test_extract_pdf_creation_date_falls_back_to_filename_year():
    metadata = {}
    date, counter = extract_pdf_creation_date(
        metadata, "2018-Survey-Report.pdf", counter=2
    )
    assert date == "2018-01-01"
    assert counter == 2


def test_extract_pdf_creation_date_uses_today_when_no_hints():
    metadata = {}
    date, counter = extract_pdf_creation_date(metadata, "no-date.pdf", counter=0)
    assert date == datetime.now().strftime("%Y-%m-%d")
    assert counter == 1
