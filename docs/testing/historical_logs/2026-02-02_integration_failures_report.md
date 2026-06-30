# Integration Test Failure Report (2026-02-02)

## Summary
Running `pytest tests/integration/` produced 12 failures. The failures were traced to two root causes: missing AnyIO backend dependency for trio and stale default callables in `build_json()` preventing monkeypatched extractors from being used.

## Environment
- OS: macOS
- Python: 3.11.14 (virtualenv)
- Pytest: 8.4.2
- AnyIO: 4.11.0

## Observed Failures
1) **AnyIO backend errors**
- Failures in: `tests/integration/test_api_health.py` (all parametrized `[trio]` cases)
- Error: `ModuleNotFoundError: No module named 'trio'`
- Root cause: AnyIO attempts to use the `trio` backend for `@pytest.mark.anyio` tests when no backend override is provided. `trio` is not installed in the test environment.

2) **PDF processing errors**
- Failures in:
  - `tests/integration/test_pdf_pipeline_e2e.py::test_pdf_pipeline_update_end_to_end`
  - `tests/integration/test_pdf_update_flow_integration.py::test_update_flow_processes_only_new`
- Error: `pymupdf.FileDataError: Failed to open file ...` (invalid fake PDFs)
- Root cause: `build_json()` in `statschat/pdf_processing/pdf_to_json.py` captured default extractor functions at definition time. Tests monkeypatched `extract_pdf_metadata` / `extract_pdf_text`, but the patched functions were not used, causing PyMuPDF to parse the fake PDFs.

## Fixes Applied
1) **Force AnyIO to use asyncio**
- Added a session-scoped fixture to avoid the optional trio dependency.
- File: `tests/conftest.py`
- Fixture:
  - `anyio_backend()` returns `"asyncio"`.

2) **Make `build_json()` honor monkeypatching**
- Changed defaults to `None` and assigned callables inside the function body.
- File: `statschat/pdf_processing/pdf_to_json.py`
- This ensures patched functions are used during tests.

## Result
- After the changes, `pytest tests/integration/` passed:
  - 28 passed
  - 5 warnings (PyMuPDF SWIG deprecation warnings)

## Notes
- Warnings are from PyMuPDF SWIG types and do not affect test outcomes.
- No changes required to runtime logic beyond enabling test overrides.

## Recommended Follow-ups
- Consider documenting the AnyIO backend fixture in testing guides if needed.
- Optionally add `trio` as a test extra if you want to run tests against multiple AnyIO backends.
