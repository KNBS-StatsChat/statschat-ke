"""Integration test for PDF pipeline: downloader -> pdf_to_json -> merge_database_files."""

import json
import importlib
import sys
import types
from unittest.mock import MagicMock


def _silence_tqdm(monkeypatch):
    import statschat.pdf_processing.pdf_downloader as dl

    monkeypatch.setattr(dl, "tqdm", lambda it, **k: it)


def test_pdf_pipeline_update_end_to_end(tmp_path, monkeypatch):
    # Arrange workspace
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

    # Seed existing url_dict and file for UPDATE mode
    (pdf_downloads / "existing.pdf").write_bytes(b"%PDF-1.4 existing")
    (pdf_downloads / "url_dict.json").write_text(
        json.dumps(
            {
                "existing.pdf": {
                    "pdf_url": "https://www.knbs.or.ke/files/existing.pdf",
                    "report_page": "https://www.knbs.or.ke/reports/report-0/",
                }
            }
        )
    )

    # Mock config for downloader
    mock_config = {
        "preprocess": {"mode": "UPDATE"},
        "app": {"page_start": 1, "page_end": 1},
    }
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)

    # Mock network responses
    listing = '<a href="https://www.knbs.or.ke/reports/report-1/">Report 1</a>'
    report = '<a href="https://www.knbs.or.ke/files/sample.pdf">Download PDF</a>'
    pdf_bytes = b"%PDF-1.4 sample"

    def side_effect(url, *a, **k):
        resp = MagicMock()
        if str(url).endswith("/all-reports/page/1/"):
            resp.status_code = 200
            resp.content = listing.encode()
        elif str(url).endswith("/reports/report-1/"):
            resp.status_code = 200
            resp.content = report.encode()
        elif str(url).endswith("/files/sample.pdf"):
            resp.status_code = 200
            resp.content = pdf_bytes
        else:
            resp.status_code = 404
            resp.content = b""
        return resp

    monkeypatch.setattr(
        "statschat.pdf_processing.pdf_downloader.requests.get",
        MagicMock(side_effect=side_effect),
    )
    _silence_tqdm(monkeypatch)

    # Run downloader (UPDATE)
    from statschat.pdf_processing import pdf_downloader

    importlib.reload(pdf_downloader)
    pdf_downloader.main()

    # Stub pdf_to_json extractors to avoid heavy deps
    if "pdfplumber" not in sys.modules:
        sys.modules["pdfplumber"] = types.ModuleType("pdfplumber")
    if "fitz" not in sys.modules:
        sys.modules["fitz"] = types.ModuleType("fitz")

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

    pdf_to_json.process_pdfs("UPDATE", {})

    # Merge latest_* into base directories
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)
    importlib.import_module(module_name)

    # Assert: new files exist in base directories
    assert (pdf_downloads / "sample.pdf").exists()
    assert (json_conversions / "sample.json").exists()

    # Assert: counts are as expected (1 existing + 1 new)
    pdfs = list(pdf_downloads.glob("*.pdf"))
    jsons = list(json_conversions.glob("*.json"))
    assert len(pdfs) == 2
    assert len(jsons) == 1

    # Assert: url_dict merged and all files present
    merged = json.loads((pdf_downloads / "url_dict.json").read_text())
    assert "existing.pdf" in merged
    assert "sample.pdf" in merged
    for name in merged.keys():
        assert (pdf_downloads / name).exists()

    # Assert: latest_* directories are cleaned
    assert not list(latest_pdf_downloads.glob("*.pdf"))
    assert not list(latest_json_conversions.glob("*.json"))
