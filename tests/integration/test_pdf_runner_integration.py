"""Integration tests for pdf_runner orchestration behavior.

These tests execute the pdf_runner entry point with mocked configuration and
subprocess calls to verify the correct script order for SETUP and UPDATE modes.
"""

import runpy
import subprocess
from pathlib import Path


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

    script_paths = [Path(args[1]).name for args in calls]
    assert script_paths == [
        "pdf_downloader.py",
        "pdf_to_json.py",
        "preprocess.py",
    ]


def test_pdf_runner_update_calls_expected_scripts(monkeypatch):
    calls = _run_pdf_runner(monkeypatch, "UPDATE")

    script_paths = [Path(args[1]).name for args in calls]
    assert script_paths == [
        "pdf_downloader.py",
        "pdf_to_json.py",
        "preprocess.py",
        "merge_database_files.py",
    ]
