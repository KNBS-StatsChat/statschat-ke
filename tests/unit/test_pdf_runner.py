"""Unit tests for pdf_runner entrypoint and subprocess orchestration.

These tests validate that the pipeline runner:
- Invokes child scripts via subprocess with the expected arguments.
- Executes the correct script sequence for SETUP and UPDATE modes.
- Raises on invalid modes and propagates subprocess failures.
"""

import runpy
import subprocess
import sys
from types import SimpleNamespace

import statschat
import pytest


def test_run_script_success(monkeypatch, capsys):
    calls = []

    def fake_run(args, check=True, **kwargs):
        calls.append((args, check, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Import the run_script function by running the module and accessing it
    module = runpy.run_path("statschat/pdf_runner.py")
    run_script = module["run_script"]

    run_script("some_script.py")

    captured = capsys.readouterr()
    assert "Running script: some_script.py" in captured.out
    assert len(calls) == 1
    # First arg should be the sys.executable and script path
    assert calls[0][0][0] == sys.executable
    assert str(calls[0][0][1]) == "some_script.py"


def test_run_script_raises_on_failure(monkeypatch):
    def raising_run(args, check=True, **kwargs):
        raise subprocess.CalledProcessError(returncode=2, cmd=args)

    monkeypatch.setattr(subprocess, "run", raising_run)
    module = runpy.run_path("statschat/pdf_runner.py")
    run_script = module["run_script"]

    with pytest.raises(subprocess.CalledProcessError):
        run_script("bad.py")


def _patch_load_config(monkeypatch, mode_value: str):
    # Patch statschat.load_config to return a predictable mode
    def fake_load_config(name="main"):
        return {"preprocess": {"mode": mode_value}}

    monkeypatch.setattr(statschat, "load_config", fake_load_config)


def test_main_pipeline_setup_executes_three_scripts(monkeypatch):
    calls = []

    def fake_run(args, check=True, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    _patch_load_config(monkeypatch, "SETUP")

    # Execute the script as __main__
    runpy.run_path("statschat/pdf_runner.py", run_name="__main__")

    # Expect three script runs: downloader, pdf_to_json, preprocess
    assert len(calls) == 3
    called_files = [str(c[1]) for c in calls]
    assert called_files[0].endswith("pdf_downloader.py")
    assert called_files[1].endswith("pdf_to_json.py")
    assert called_files[2].endswith("preprocess.py")


def test_main_pipeline_update_executes_merge(monkeypatch):
    calls = []

    def fake_run(args, check=True, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    _patch_load_config(monkeypatch, "UPDATE")

    runpy.run_path("statschat/pdf_runner.py", run_name="__main__")

    # Expect four script runs including merge_database_files.py
    assert len(calls) == 4
    called_files = [str(c[1]) for c in calls]
    assert called_files[0].endswith("pdf_downloader.py")
    assert called_files[1].endswith("pdf_to_json.py")
    assert called_files[2].endswith("preprocess.py")
    assert called_files[3].endswith("merge_database_files.py")


def test_main_pipeline_invalid_mode_raises(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0)
    )
    _patch_load_config(monkeypatch, "BADMODE")

    with pytest.raises(ValueError):
        runpy.run_path("statschat/pdf_runner.py", run_name="__main__")
