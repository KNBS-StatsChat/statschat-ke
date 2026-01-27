"""End-to-end tests for the UPDATE pipeline entrypoint.

These tests run the pdf_runner entrypoint with mocked network/PDF parsing and a
lightweight embedding step to verify end-to-end artifacts are produced and
merged correctly. They also cover the no-new-PDFs path to ensure the pipeline
exits cleanly without creating new outputs.
"""

import json
import runpy
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_full_update_run_creates_and_merges_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.cwd", lambda *a, **k: tmp_path)

    call_order = []

    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    latest_pdf_downloads = base / "latest_pdf_downloads"
    json_conversions = base / "json_conversions"
    latest_json_conversions = base / "latest_json_conversions"
    json_split = base / "json_split"
    latest_json_split = base / "latest_json_split"
    db_root = base / "db_langchain"
    db_latest = base / "db_langchain_latest"

    for p in (
        pdf_downloads,
        latest_pdf_downloads,
        json_conversions,
        latest_json_conversions,
        json_split,
        latest_json_split,
        db_root,
        db_latest,
    ):
        p.mkdir(parents=True, exist_ok=True)

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

    mock_config = {
        "preprocess": {"mode": "UPDATE"},
        "app": {"page_start": 1, "page_end": 1},
    }
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)

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
    monkeypatch.setattr(
        "statschat.pdf_processing.pdf_downloader.tqdm", lambda it, **k: it
    )

    def fake_preprocess():
        call_order.append("preprocess")
        for source in latest_json_conversions.glob("*.json"):
            data = json.loads(source.read_text())
            split = {"page_text": "chunk", "latest": data["latest"], "id": data["id"]}
            (latest_json_split / f"{data['id']}_0.json").write_text(json.dumps(split))

        (db_root / "index.faiss").write_bytes(b"base")
        (db_root / "index.pkl").write_bytes(b"base")
        (db_latest / "index.faiss").write_bytes(b"latest")
        (db_latest / "index.pkl").write_bytes(b"latest")

        for fp in db_latest.glob("*"):
            fp.unlink()

    def fake_run(args, check):
        script = Path(args[1]).name
        if script == "pdf_downloader.py":
            call_order.append("download")
            from statschat.pdf_processing import pdf_downloader

            pdf_downloader.main()
        elif script == "pdf_to_json.py":
            call_order.append("pdf_to_json")
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
        elif script == "preprocess.py":
            fake_preprocess()
        elif script == "merge_database_files.py":
            call_order.append("merge")
            module_name = "statschat.pdf_processing.merge_database_files"
            runpy.run_module(module_name, run_name="__main__")
        else:
            raise AssertionError(f"Unexpected script: {script}")

        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runpy.run_module("statschat.pdf_runner", run_name="__main__")

    assert (pdf_downloads / "sample.pdf").exists()
    assert (json_conversions / "sample.json").exists()
    merged = json.loads((pdf_downloads / "url_dict.json").read_text())
    assert set(merged.keys()) == {"existing.pdf", "sample.pdf"}
    assert (
        merged["sample.pdf"]["report_page"]
        == "https://www.knbs.or.ke/reports/report-1/"
    )

    assert not list(latest_pdf_downloads.glob("*.pdf"))
    assert not list(latest_json_conversions.glob("*.json"))
    assert not list(latest_json_split.glob("*.json"))

    assert list(json_split.glob("*.json"))
    assert (db_root / "index.faiss").exists()
    assert (db_root / "index.pkl").exists()
    assert not list(db_latest.glob("*"))

    assert call_order.index("preprocess") < call_order.index("merge")


def test_full_update_run_with_no_new_pdfs_exits_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.cwd", lambda *a, **k: tmp_path)

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

    mock_config = {
        "preprocess": {"mode": "UPDATE"},
        "app": {"page_start": 1, "page_end": 1},
    }
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)

    listing = '<a href="https://www.knbs.or.ke/reports/report-1/">Report 1</a>'
    report = '<a href="https://www.knbs.or.ke/files/existing.pdf">Download PDF</a>'

    def side_effect(url, *a, **k):
        resp = MagicMock()
        if str(url).endswith("/all-reports/page/1/"):
            resp.status_code = 200
            resp.content = listing.encode()
        elif str(url).endswith("/reports/report-1/"):
            resp.status_code = 200
            resp.content = report.encode()
        elif str(url).endswith("/files/existing.pdf"):
            resp.status_code = 200
            resp.content = b"%PDF-1.4 existing"
        else:
            resp.status_code = 404
            resp.content = b""
        return resp

    monkeypatch.setattr(
        "statschat.pdf_processing.pdf_downloader.requests.get",
        MagicMock(side_effect=side_effect),
    )
    monkeypatch.setattr(
        "statschat.pdf_processing.pdf_downloader.tqdm", lambda it, **k: it
    )

    def fake_run(args, check):
        script = Path(args[1]).name
        if script == "pdf_downloader.py":
            from statschat.pdf_processing import pdf_downloader

            with pytest.raises(SystemExit):
                pdf_downloader.main()
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runpy.run_module("statschat.pdf_runner", run_name="__main__")

    assert not list(latest_pdf_downloads.glob("*.pdf"))
    assert not list(latest_json_conversions.glob("*.json"))
