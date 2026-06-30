"""Integration tests for error paths in merge_database_files.

These tests execute the merge script in minimal/empty workspaces to ensure it
handles missing directories and missing/empty latest_* folders gracefully.
They assert that the script prints its expected informational messages, emits
no tracebacks, and does not create unintended outputs. A separate case covers
the behavior when the latest url_dict exists but the original is missing.
"""

import importlib
import sys

import pytest


def test_merge_database_files_handles_missing_dirs_and_url_dict(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)
    importlib.import_module(module_name)

    captured = capsys.readouterr().out
    assert "No new url_dict.json to merge" in captured
    assert "json_splits have been moved to" in captured

    captured_err = capsys.readouterr().err
    assert "Traceback" not in captured_err


def test_merge_database_files_handles_empty_latest_dirs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    base = tmp_path / "data"
    for dirname in (
        "pdf_downloads",
        "json_conversions",
        "json_split",
        "latest_pdf_downloads",
        "latest_json_conversions",
        "latest_json_split",
    ):
        (base / dirname).mkdir(parents=True, exist_ok=True)

    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)
    importlib.import_module(module_name)

    captured = capsys.readouterr().out
    assert "No new url_dict.json to merge" in captured
    assert "json_splits have been moved to" in captured

    captured_err = capsys.readouterr().err
    assert "Traceback" not in captured_err

    assert not list((base / "latest_pdf_downloads").glob("*.pdf"))
    assert not list((base / "latest_json_conversions").glob("*.json"))
    assert not list((base / "latest_json_split").glob("*.json"))

    assert not list((base / "pdf_downloads").glob("*.pdf"))
    assert not list((base / "json_conversions").glob("*.json"))
    assert not list((base / "json_split").glob("*.json"))


def test_merge_database_files_missing_original_url_dict(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    base = tmp_path / "data"
    (base / "pdf_downloads").mkdir(parents=True, exist_ok=True)
    (base / "latest_pdf_downloads").mkdir(parents=True, exist_ok=True)

    (base / "latest_pdf_downloads" / "url_dict.json").write_text(
        '{"new.pdf": {"pdf_url": "https://example.com/new.pdf"}}'
    )

    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    with pytest.raises(FileNotFoundError):
        importlib.import_module(module_name)
