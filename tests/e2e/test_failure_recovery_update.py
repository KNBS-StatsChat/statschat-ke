"""End-to-end failure recovery for UPDATE downloads.

Simulates a failed PDF download during UPDATE and asserts the pipeline exits
cleanly without altering existing data or creating new artifacts.
"""

import json
import runpy
import subprocess
from pathlib import Path
from unittest.mock import MagicMock


def _run_update_with_status(tmp_path, monkeypatch, status_code):
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

    def side_effect(url, *a, **k):
        resp = MagicMock()
        if str(url).endswith("/all-reports/page/1/"):
            resp.status_code = 200
            resp.content = listing.encode()
        elif str(url).endswith("/reports/report-1/"):
            resp.status_code = 200
            resp.content = report.encode()
        elif str(url).endswith("/files/sample.pdf"):
            resp.status_code = status_code
            resp.content = b""
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

            pdf_downloader.main()
        elif script == "pdf_to_json.py":
            from statschat.pdf_processing import pdf_to_json

            pdf_to_json.process_pdfs("UPDATE", {})
        elif script == "preprocess.py":
            return subprocess.CompletedProcess(args, 0)
        elif script == "merge_database_files.py":
            runpy.run_module(
                "statschat.pdf_processing.merge_database_files", run_name="__main__"
            )
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runpy.run_module("statschat.pdf_runner", run_name="__main__")

    merged = json.loads((pdf_downloads / "url_dict.json").read_text())
    assert set(merged.keys()) == {"existing.pdf"}
    assert (pdf_downloads / "existing.pdf").exists()

    assert not list(latest_pdf_downloads.glob("*.pdf"))
    assert not list(latest_json_conversions.glob("*.json"))
    latest_dict_path = latest_pdf_downloads / "url_dict.json"
    if latest_dict_path.exists():
        assert json.loads(latest_dict_path.read_text()) == {}

    assert not list(json_conversions.glob("*.json"))


def test_update_download_failure_leaves_existing_data(tmp_path, monkeypatch, capsys):
    _run_update_with_status(tmp_path, monkeypatch, 404)

    captured = capsys.readouterr().out
    assert "Failed to download" in captured


def test_update_download_failure_forbidden(tmp_path, monkeypatch, capsys):
    _run_update_with_status(tmp_path, monkeypatch, 403)

    captured = capsys.readouterr().out
    assert "Failed to download" in captured


def test_update_download_failure_rate_limited(tmp_path, monkeypatch, capsys):
    _run_update_with_status(tmp_path, monkeypatch, 429)

    captured = capsys.readouterr().out
    assert "Failed to download" in captured
