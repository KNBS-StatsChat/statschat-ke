"""Integration test for UPDATE flow with mixed old/new PDFs.

This test simulates the UPDATE pipeline using a temp workspace and mocked
PDF parsing. It verifies that:
1) Only new PDFs in latest_* are converted to JSON.
2) Merge moves latest_* artifacts into base directories.
3) latest_* directories are cleaned after merge.
4) url_dict.json is merged to include both old and new entries.
"""

import importlib
import json
import sys


def test_update_flow_processes_only_new(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    latest_pdf_downloads = base / "latest_pdf_downloads"
    json_conversions = base / "json_conversions"
    latest_json_conversions = base / "latest_json_conversions"

    for p in (
        pdf_downloads,
        latest_pdf_downloads,
        json_conversions,
        latest_json_conversions,
    ):
        p.mkdir(parents=True, exist_ok=True)

    # Seed old and new PDFs
    (pdf_downloads / "old.pdf").write_bytes(b"%PDF-1.4 old")
    (latest_pdf_downloads / "old.pdf").write_bytes(b"%PDF-1.4 old")
    (latest_pdf_downloads / "new.pdf").write_bytes(b"%PDF-1.4 new")

    (pdf_downloads / "url_dict.json").write_text(
        json.dumps(
            {
                "old.pdf": {
                    "pdf_url": "https://example.com/old.pdf",
                    "report_page": "https://example.com/old",
                }
            }
        )
    )
    (latest_pdf_downloads / "url_dict.json").write_text(
        json.dumps(
            {
                "old.pdf": {
                    "pdf_url": "https://example.com/old.pdf",
                    "report_page": "https://example.com/old",
                },
                "new.pdf": {
                    "pdf_url": "https://example.com/new.pdf",
                    "report_page": "https://example.com/new",
                },
            }
        )
    )

    # Mock pdf_to_json internals to avoid heavy deps
    from statschat.pdf_processing import pdf_to_json

    monkeypatch.setattr(
        pdf_to_json,
        "extract_pdf_metadata",
        lambda path: (path.name, {"modDate": "D:20240102000000Z"}),
    )
    monkeypatch.setattr(
        pdf_to_json,
        "extract_pdf_text",
        lambda _path, _url: [
            {"page_number": 1, "page_url": "u#page=1", "page_text": "content"}
        ],
    )
    monkeypatch.setattr(
        pdf_to_json,
        "get_abstract_metadata",
        lambda _url: {
            "date": "May 2025",
            "overview": "Overview",
            "publication_type": "Report",
            "publication_theme": "Theme",
            "pdf_abstract_url": "https://example.com/abstract",
        },
    )

    # Act: process UPDATE and merge
    pdf_to_json.process_pdfs("UPDATE", {})

    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)
    importlib.import_module(module_name)

    # Assert: only new JSON created and merged
    assert (json_conversions / "new.json").exists()
    assert not (json_conversions / "old.json").exists()

    # Assert: latest dirs are cleaned
    assert not list(latest_pdf_downloads.glob("*.pdf"))
    assert not list(latest_json_conversions.glob("*.json"))

    # Assert: url_dict merged contains both
    merged = json.loads((pdf_downloads / "url_dict.json").read_text())
    assert set(merged.keys()) == {"old.pdf", "new.pdf"}
