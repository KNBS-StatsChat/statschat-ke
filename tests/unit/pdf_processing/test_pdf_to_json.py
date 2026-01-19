"""Unit tests for statschat.pdf_processing.pdf_to_json.

These tests focus on high-ROI, deterministic behaviors:
- date parsing/fallback rules
- keyword extraction
- JSON payload invariants and schema produced by build_json
"""

import importlib
import json
import sys
from datetime import datetime
from types import ModuleType

import pytest

fake_fitz = ModuleType("fitz")


def _fake_open(*args, **kwargs):
    raise RuntimeError("fake fitz.open called - should be monkeypatched in tests")


fake_fitz.open = _fake_open
sys.modules.setdefault("fitz", fake_fitz)

pdf_to_json = importlib.import_module("statschat.pdf_processing.pdf_to_json")


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


def test_extract_pdf_text_with_mocked_fitz(tmp_path, monkeypatch):
    # Create a fake PDF path
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_text("")

    class FakePage:
        def __init__(self, text):
            self._text = text

        def get_text(self):
            return self._text

    class FakeDoc:
        def __init__(self, pages):
            self._pages = pages

        def __len__(self):
            return len(self._pages)

        def __getitem__(self, idx):
            return self._pages[idx]

        def close(self):
            pass

    def fake_open(path):
        return FakeDoc([FakePage("Line1\nLine2"), FakePage("OnlyOneLine")])

    monkeypatch.setattr(
        pdf_to_json, "fitz", type("M", (), {"open": staticmethod(fake_open)})
    )

    pages = pdf_to_json.extract_pdf_text(pdf_path, "https://example.com/doc.pdf")
    assert isinstance(pages, list)
    assert pages[0]["page_number"] == 1
    assert pages[0]["page_text"] == "Line1Line2"
    assert pages[1]["page_text"] == "OnlyOneLine"


def test_get_name_and_meta_and_extract_pdf_metadata(monkeypatch, tmp_path):
    # Create a fake PDF file path
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("")

    class FakeDoc:
        def __init__(self, metadata):
            self.metadata = metadata

        def close(self):
            pass

    def fake_open(path):
        return FakeDoc({"creationDate": "D:20220101000000Z", "title": "My Title"})

    monkeypatch.setattr(
        pdf_to_json, "fitz", type("M", (), {"open": staticmethod(fake_open)})
    )

    name, meta = pdf_to_json.get_name_and_meta(pdf_path)
    assert name == "sample.pdf"
    assert "creationDate" in meta

    # extract_pdf_metadata currently wraps get_name_and_meta
    fname, pmeta = pdf_to_json.extract_pdf_metadata(pdf_path)
    assert fname == name
    assert pmeta == meta


def test_get_abstract_metadata_parses_html(monkeypatch):
    html = (
        "<html><body>About Report Report Economy May 2025 Overview This is an overview "
        'Share This Page <a href="https://example.com/file.pdf">pdf</a></body></html>'
    ).encode("utf-8")

    class FakeResp:
        def read(self):
            return html

    def fake_urlopen(req):
        return FakeResp()

    monkeypatch.setattr(pdf_to_json, "urlopen", fake_urlopen)

    meta = pdf_to_json.get_abstract_metadata("https://knbs.or.ke/reports/x")
    assert meta["date"] == "May 2025"
    assert "overview" in meta
    assert meta["pdf_abstract_url"] == "https://example.com/file.pdf"


def test_get_abstract_metadata_alt_layout_uses_main_report_year(monkeypatch):
    html = (
        "<html><body>Main Report Some content 2014 Visit the KNBS "
        '<a href="https://example.com/file.pdf">pdf</a></body></html>'
    ).encode("utf-8")

    class FakeResp:
        def read(self):
            return html

    def fake_urlopen(_req):
        return FakeResp()

    monkeypatch.setattr(pdf_to_json, "urlopen", fake_urlopen)

    meta = pdf_to_json.get_abstract_metadata("https://knbs.or.ke/reports/x")
    assert meta["date"] == "2014"
    assert meta["pdf_abstract_url"] == "https://example.com/file.pdf"


def test_get_abstract_metadata_missing_pdf_link(monkeypatch):
    html = (
        "<html><body>About Report Report Economy May 2025 Overview Text "
        "Share This Page</body></html>"
    ).encode("utf-8")

    class FakeResp:
        def read(self):
            return html

    def fake_urlopen(_req):
        return FakeResp()

    monkeypatch.setattr(pdf_to_json, "urlopen", fake_urlopen)

    meta = pdf_to_json.get_abstract_metadata("https://knbs.or.ke/reports/x")
    assert meta["pdf_abstract_url"] == "No PDF link found"


def test_process_pdfs_setup_creates_json(tmp_path, monkeypatch):
    # Make tmp_path act as cwd for the module
    monkeypatch.setattr(pdf_to_json.Path, "cwd", staticmethod(lambda: tmp_path))

    # Create data/pdf_downloads and a sample pdf + url_dict.json
    pdf_dir = tmp_path / "data" / "pdf_downloads"
    json_dir = tmp_path / "data" / "json_conversions"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "sample.pdf").write_text("")

    url_dict = {
        "sample.pdf": {
            "pdf_url": "https://example.com/sample.pdf",
            "report_page": "https://example.com/report",
        }
    }
    (pdf_dir / "url_dict.json").write_text(json.dumps(url_dict))

    # Replace build_json with a fake that writes a file
    def fake_build_json(pdf_path, pdf_url, report_page, JSON_DIR, **kwargs):
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        out = JSON_DIR / f"{pdf_path.stem}.json"
        out.write_text("{}")
        return out

    monkeypatch.setattr(pdf_to_json, "build_json", fake_build_json)

    pdf_to_json.process_pdfs("SETUP", {})

    assert (json_dir / "sample.json").exists()


def test_process_pdfs_update_only_new(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_to_json.Path, "cwd", staticmethod(lambda: tmp_path))

    old_dir = tmp_path / "data" / "pdf_downloads"
    latest_dir = tmp_path / "data" / "latest_pdf_downloads"
    old_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)

    (old_dir / "old.pdf").write_text("")
    (latest_dir / "old.pdf").write_text("")
    (latest_dir / "new.pdf").write_text("")

    url_dict = {
        "old.pdf": {"pdf_url": "https://example.com/old.pdf", "report_page": "r"},
        "new.pdf": {"pdf_url": "https://example.com/new.pdf", "report_page": "r"},
    }
    (latest_dir / "url_dict.json").write_text(json.dumps(url_dict))
    (old_dir / "url_dict.json").write_text(
        json.dumps({"old.pdf": {"pdf_url": "x", "report_page": "r"}})
    )

    out_dir = tmp_path / "data" / "latest_json_conversions"

    calls = []

    def fake_build_json(pdf_path, _pdf_url, _report_page, JSON_DIR, **kwargs):
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        calls.append(pdf_path.name)
        out = JSON_DIR / f"{pdf_path.stem}.json"
        out.write_text("{}")
        return out

    monkeypatch.setattr(pdf_to_json, "build_json", fake_build_json)

    pdf_to_json.process_pdfs("UPDATE", {})

    assert calls == ["new.pdf"]
    assert (out_dir / "new.json").exists()
    assert not (out_dir / "old.json").exists()


def test_process_pdfs_update_no_new_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_to_json.Path, "cwd", staticmethod(lambda: tmp_path))

    old_dir = tmp_path / "data" / "pdf_downloads"
    latest_dir = tmp_path / "data" / "latest_pdf_downloads"
    old_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)

    (old_dir / "same.pdf").write_text("")
    (latest_dir / "same.pdf").write_text("")

    (latest_dir / "url_dict.json").write_text(
        json.dumps({"same.pdf": {"pdf_url": "x", "report_page": "r"}})
    )
    (old_dir / "url_dict.json").write_text(
        json.dumps({"same.pdf": {"pdf_url": "x", "report_page": "r"}})
    )

    calls = []

    def fake_build_json(*args, **kwargs):
        calls.append("called")

    monkeypatch.setattr(pdf_to_json, "build_json", fake_build_json)

    pdf_to_json.process_pdfs("UPDATE", {})

    assert calls == []


def test_process_pdfs_update_missing_url_dict_skips(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_to_json.Path, "cwd", staticmethod(lambda: tmp_path))

    old_dir = tmp_path / "data" / "pdf_downloads"
    latest_dir = tmp_path / "data" / "latest_pdf_downloads"
    old_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)

    (old_dir / "old.pdf").write_text("")
    (latest_dir / "new.pdf").write_text("")

    # No latest url_dict.json present
    (old_dir / "url_dict.json").write_text(
        json.dumps({"old.pdf": {"pdf_url": "x", "report_page": "r"}})
    )

    calls = []

    def fake_build_json(*args, **kwargs):
        calls.append("called")

    monkeypatch.setattr(pdf_to_json, "build_json", fake_build_json)

    pdf_to_json.process_pdfs("UPDATE", {})

    assert calls == []
