# PDF Processing Tests

These tests protect the ingestion side of the system: downloading PDFs, extracting metadata/text, and producing JSON artifacts that downstream embedding/retrieval depends on.

## Where the Tests Live

- `tests/unit/pdf_processing/test_pdf_downloader.py`
- `tests/unit/pdf_processing/test_pdf_to_json.py`
- `tests/unit/pdf_processing/test_page_splitting.py`
- `tests/unit/pdf_processing/test_merge_database_files.py`

Related deep-dive:
- `docs/testing/guides/page_splitting_tests.md`

## What These Tests Protect

- **Downloader correctness**: URL discovery, url_dict schema, update-mode behavior, and failure modes (404s, corrupt/empty PDFs)
- **Metadata extraction**: creation date parsing and fallback behavior
- **Page integrity**: JSON page numbering aligns with PDF page counts (critical for retrieval correctness)
- **Database file merging**: latest_* artifacts are moved/merged correctly and safely

## Maintainership Notes

### Isolation and Determinism

Many of these tests simulate filesystem layouts and network behavior.
Maintain the “unit” characteristics by:
- using `tmp_path` for directories
- mocking network calls (`requests.get`) rather than hitting KNBS endpoints
- keeping assumptions about `data/` minimal (prefer fixtures under `tests/test_data/`)

### Page Splitting

The page splitting suite has a dedicated guide because it mixes correctness checks and practical failure reporting.
If you adjust how PDFs are read (library changes) or how JSON is produced, update both:
- `tests/unit/pdf_processing/test_page_splitting.py`
- `docs/testing/guides/page_splitting_tests.md`

## How to Run

```bash
# All pdf_processing tests
pytest tests/unit/pdf_processing/ -v

# Commonly-run subsets
pytest tests/unit/pdf_processing/test_pdf_to_json.py -v
pytest tests/unit/pdf_processing/test_pdf_downloader.py -v
pytest tests/unit/pdf_processing/test_page_splitting.py -v
```

## When to Update These Tests

Update/add pdf_processing tests when:
- url_dict.json schema changes
- downloader logic changes (pagination, link selection, file naming)
- metadata extraction rules change
- JSON output schema changes (fields or page numbering)
- merge behavior changes for latest_* directories
