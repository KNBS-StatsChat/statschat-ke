"""
Lightweight regression test for merge_database_files side effects.

Ensures files in latest_* directories are moved and url_dict merged safely.
"""

import json
import importlib
import sys

import pytest


def test_merge_database_files_moves_and_merges(tmp_path, monkeypatch):
    """Moves latest_* artifacts into main dirs and merges pdf_downloads/url_dict."""
    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    json_conversions = base / "json_conversions"
    json_split = base / "json_split"
    latest_pdf = base / "latest_pdf_downloads"
    latest_json = base / "latest_json_conversions"
    latest_split = base / "latest_json_split"

    # Create required directories
    for path in (
        pdf_downloads,
        json_conversions,
        json_split,
        latest_pdf,
        latest_json,
        latest_split,
    ):
        path.mkdir(parents=True, exist_ok=True)

    # Seed original url_dict and a file
    (pdf_downloads / "url_dict.json").write_text(
        json.dumps({"old.pdf": {"pdf_url": "old", "report_page": "old_page"}})
    )
    (pdf_downloads / "old.pdf").write_bytes(b"old")

    # Seed latest artifacts
    (latest_pdf / "new.pdf").write_bytes(b"new")
    (latest_pdf / "url_dict.json").write_text(
        json.dumps({"new.pdf": {"pdf_url": "new", "report_page": "new_page"}})
    )
    (latest_json / "new.json").write_text("{}")
    (latest_split / "new_split.json").write_text("{}")

    # Ensure module uses tmp_path as cwd
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    importlib.import_module(module_name)

    # Files should be moved to main directories
    assert (pdf_downloads / "new.pdf").exists()
    assert (json_conversions / "new.json").exists()
    assert (json_split / "new_split.json").exists()

    # Latest directories should be emptied of moved files
    assert not (latest_pdf / "new.pdf").exists()
    assert not (latest_json / "new.json").exists()
    assert not (latest_split / "new_split.json").exists()

    # url_dict should be merged and latest url_dict removed
    merged = json.loads((pdf_downloads / "url_dict.json").read_text())
    assert set(merged.keys()) == {"old.pdf", "new.pdf"}
    assert not (latest_pdf / "url_dict.json").exists()


def test_merge_database_files_no_latest_dirs(tmp_path, monkeypatch):
    """Should not error when latest_* dirs are missing."""
    base = tmp_path / "data"
    (base / "pdf_downloads").mkdir(parents=True)
    (base / "json_conversions").mkdir(parents=True)
    (base / "json_split").mkdir(parents=True)

    (base / "pdf_downloads" / "url_dict.json").write_text("{}")

    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    importlib.import_module(module_name)

    assert (base / "pdf_downloads" / "url_dict.json").exists()


def test_merge_database_files_empty_latest_dirs(tmp_path, monkeypatch):
    """Should not error when latest_* dirs exist but are empty."""
    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    json_conversions = base / "json_conversions"
    json_split = base / "json_split"
    latest_pdf = base / "latest_pdf_downloads"
    latest_json = base / "latest_json_conversions"
    latest_split = base / "latest_json_split"

    for path in (
        pdf_downloads,
        json_conversions,
        json_split,
        latest_pdf,
        latest_json,
        latest_split,
    ):
        path.mkdir(parents=True, exist_ok=True)

    (pdf_downloads / "url_dict.json").write_text("{}")

    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    importlib.import_module(module_name)

    assert (pdf_downloads / "url_dict.json").exists()
    assert not list(latest_pdf.glob("*.pdf"))
    assert not list(latest_json.glob("*.json"))
    assert not list(latest_split.glob("*.json"))


def test_merge_database_files_overwrites_on_collision(tmp_path, monkeypatch):
    """Latest files with same name should overwrite existing ones."""
    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    json_conversions = base / "json_conversions"
    json_split = base / "json_split"
    latest_pdf = base / "latest_pdf_downloads"
    latest_json = base / "latest_json_conversions"
    latest_split = base / "latest_json_split"

    for path in (
        pdf_downloads,
        json_conversions,
        json_split,
        latest_pdf,
        latest_json,
        latest_split,
    ):
        path.mkdir(parents=True, exist_ok=True)

    (pdf_downloads / "url_dict.json").write_text("{}")

    (pdf_downloads / "same.pdf").write_bytes(b"old")
    (latest_pdf / "same.pdf").write_bytes(b"new")

    (json_conversions / "same.json").write_text("old")
    (latest_json / "same.json").write_text("new")

    (json_split / "same_split.json").write_text("old")
    (latest_split / "same_split.json").write_text("new")

    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    importlib.import_module(module_name)

    assert (pdf_downloads / "same.pdf").read_bytes() == b"new"
    assert (json_conversions / "same.json").read_text() == "new"
    assert (json_split / "same_split.json").read_text() == "new"


def test_merge_database_files_invalid_latest_url_dict_raises(tmp_path, monkeypatch):
    """Invalid latest url_dict.json should raise a JSON decode error."""
    base = tmp_path / "data"
    pdf_downloads = base / "pdf_downloads"
    latest_pdf = base / "latest_pdf_downloads"

    pdf_downloads.mkdir(parents=True)
    latest_pdf.mkdir(parents=True)

    (pdf_downloads / "url_dict.json").write_text("{}")
    (latest_pdf / "url_dict.json").write_text("not-json")

    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    module_name = "statschat.pdf_processing.merge_database_files"
    sys.modules.pop(module_name, None)

    with pytest.raises(json.JSONDecodeError):
        importlib.import_module(module_name)
