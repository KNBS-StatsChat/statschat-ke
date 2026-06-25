# Linting Changelog

## 2025-12-15: Initial Pre-commit Fixes

Applied "safe" automated fixes to resolve `flake8` errors blocking the build.

### Fixed
- **Unused Imports (`F401`)**
    - `statschat/generative/cloud_llm.py`: Removed `pathlib.Path`
    - `tests/unit/embedding/test_json_splitter.py`: Removed `pytest`, `pathlib.Path`
    - `tests/unit/embedding/test_latest_matching.py`: Removed `pytest`, `pathlib.Path`
- **Unused Variables (`F841`)**
    - `statschat/pdf_processing/pdf_downloader.py`: Removed unused `page_start` variable.
- **String Formatting (`F541`)**
    - `statschat/generative/local_llm.py`: Converted f-string without placeholders to normal string.
- **Boolean Comparisons (`E712`)**
    - `tests/unit/pdf_processing/test_page_splitting.py`: Changed `== True/False` comparisons to idiomatic python (`if cond:` / `if not cond:`).

### Deferred
- See `docs/LINTING_TODO.md` for deferred complexity and line-length issues.
