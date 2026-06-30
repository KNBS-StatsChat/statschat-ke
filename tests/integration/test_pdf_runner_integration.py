"""Integration tests for pdf_runner orchestration behavior.

These tests execute the pdf_runner entry point with mocked configuration and
subprocess calls to verify the correct script order for SETUP and UPDATE modes.
"""

import runpy
import subprocess
from pathlib import Path

import pytest


def _run_pdf_runner(monkeypatch, mode):
    calls = []

    def fake_run(args, check):
        calls.append(tuple(args))
        return subprocess.CompletedProcess(args, 0)

    import statschat

    monkeypatch.setattr(
        statschat,
        "load_config",
        lambda name="main": {"preprocess": {"mode": mode}, "app": {}},
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    runpy.run_module("statschat.pdf_runner", run_name="__main__")
    return calls


def test_pdf_runner_setup_calls_expected_scripts(monkeypatch):
    calls = _run_pdf_runner(monkeypatch, "SETUP")

    script_paths = [Path(args[1]) for args in calls]
    repo_root = Path(__file__).resolve().parents[2]
    expected_paths = [
        repo_root / "statschat" / "pdf_processing" / "pdf_downloader.py",
        repo_root / "statschat" / "pdf_processing" / "pdf_to_json.py",
        repo_root / "statschat" / "embedding" / "preprocess.py",
    ]
    assert script_paths == expected_paths

    script_names = [path.name for path in script_paths]
    assert script_paths == [
        repo_root / "statschat" / "pdf_processing" / "pdf_downloader.py",
        repo_root / "statschat" / "pdf_processing" / "pdf_to_json.py",
        repo_root / "statschat" / "embedding" / "preprocess.py",
    ]
    assert script_names == [
        "pdf_downloader.py",
        "pdf_to_json.py",
        "preprocess.py",
    ]


def test_pdf_runner_update_calls_expected_scripts(monkeypatch):
    calls = _run_pdf_runner(monkeypatch, "UPDATE")

    script_paths = [Path(args[1]) for args in calls]
    repo_root = Path(__file__).resolve().parents[2]
    expected_paths = [
        repo_root / "statschat" / "pdf_processing" / "pdf_downloader.py",
        repo_root / "statschat" / "pdf_processing" / "pdf_to_json.py",
        repo_root / "statschat" / "embedding" / "preprocess.py",
        repo_root / "statschat" / "pdf_processing" / "merge_database_files.py",
    ]
    assert script_paths == expected_paths

    script_names = [path.name for path in script_paths]
    assert script_names == [
        "pdf_downloader.py",
        "pdf_to_json.py",
        "preprocess.py",
        "merge_database_files.py",
    ]


def test_pdf_runner_surfaces_subprocess_failure(monkeypatch):
    def fake_run(_args, check):
        raise subprocess.CalledProcessError(1, ["python", "pdf_downloader.py"])

    import statschat

    monkeypatch.setattr(
        statschat,
        "load_config",
        lambda name="main": {"preprocess": {"mode": "SETUP"}, "app": {}},
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        runpy.run_module("statschat.pdf_runner", run_name="__main__")
