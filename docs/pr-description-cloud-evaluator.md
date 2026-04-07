# PR: Accuracy evaluator — cloud mode, multi-reference capture, and run reporting

## Summary

Extends the accuracy evaluation system (`tests/accuracy/evaluate_accuracy.py`) to:
1. Work against both local and cloud StatsChat APIs
2. Capture all references returned by the API (not just the first)
3. Produce timestamped, human-readable run reports for comparing StatsChat outputs against sample Q&As

Full rationale and details: [ADR-003](docs/decisions/003-accuracy-evaluator-cloud-mode.md)

## Changes

### Timestamped run folders (new)
- Each evaluation creates `tests/accuracy/runs/{cloud|local}/{timestamp}/` containing:
  - `accuracy_results.csv` — full per-row metrics
  - `run_report.md` — human-readable comparison with full summary metrics table and per-question breakdown (golden vs predicted answers, expected vs returned docs, reasoning, context chunks)
  - `run_metadata.txt` — run configuration (provider, model, QA file, all thresholds including `answer_threshold`, `document_threshold`, `k_docs`, `k_contexts`) and summary stats
  - `summary_metrics.csv` — single-row CSV of all aggregate metrics (accuracy, EM, F1, semantic sim, Precision@k, Recall@k, MRR, nDCG, safe response rate) for easy cross-run comparison
  - `qa_data_issues.csv` — validation issues (if any)
- `runs/` is gitignored

### Debug/reasoning capture (new)
- API requests now use `debug=true` to capture StatsChat's reasoning process
- New fields in `EvaluationResult`: `reasoning`, `context_texts`, `reference_scores`, `reference_titles`, `highlighting`, `context_from`, `context_reference`, `relevant_publications`
- Cloud mode captures: LLM reasoning, key phrases, retrieved context chunks, retrieval scores
- Local mode captures: `context_from`, `context_reference`, publication titles

### Multi-reference capture
- `extract_reference_details()` now collects **all** references returned by the API, not just the first
- Reference fields renamed: `reference_url` → `reference_urls`, `reference_doc_id` → `reference_doc_ids`, `reference_page` → `reference_pages`
- Values are semicolon-joined strings (e.g. `doc-a;doc-b`)
- Evidence page matching updated to check all `(doc_id, page)` pairs — `True` if any match

### Cloud mode enablement
- Retrieval metrics (Precision@k, Recall@k, MRR, nDCG) now run for both `local` and `cloud` modes using the shared FAISS index directly
- Pre-flight API key validation: reads the provider from `statschat/config/main.toml`, checks the corresponding env var, and exits with a clear message if missing

### README restructure
- Split into Part 1 (Evaluation — primary workflow) and Part 2 (QA Generation — optional)
- Unified local/cloud run commands (same `--host` flag, only URL differs)
- Documented new run folder output structure

### Bug fix
- `normalize_doc_id()` no longer returns an empty string for malformed URLs — falls back to the original input

### Census 2019 PDF exclusion removed
- The PDF scraper had a hard-coded filter excluding all report pages under `/reports/kenya-census*`, preventing download of 2019 and 2009 census PDFs
- This caused two QA questions (Q030, Q053) to reference documents that didn't exist in `pdf_downloads/`
- Removed the exclusion filter from `pdf_downloader.py` and `confirm_missing_downloads.py`
- Updated the unit test from `test_report_link_filter_excludes_census` to `test_report_link_filter_includes_census`
- Back-filled 89 census PDFs (51 from 2019, 38 from 2009) via `scripts/download_census_2019.py`
- `url_dict.json` updated from 1088 to 1176 entries
- Full investigation: [docs/investigations/2026-04-01-census-2019-pdfs-excluded-from-scraper.md](docs/investigations/2026-04-01-census-2019-pdfs-excluded-from-scraper.md)

### QA spreadsheet filename corrections
- Stripped date-path prefixes (e.g. `2025/01/`, `2023/08/`) from `relevant_doc_ids` and `evidence_locations` columns in both `KNBS_Verified_QA_Examples_updated.xlsx` and `_v2.xlsx`
- Corrected two filenames to match actual files on disk (`*Basic-Report.pdf` → `*Basic-Report1.pdf`, `*Survey-Report.pdf` → `*Survey-Report_1.pdf`)
- Deleted example rows Q001/Q002 (made-up data no longer needed) from both files

## How to test

```bash
# Validate QA sheet only (no API call)
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --validate-only

# Run against cloud API
set -a && source .env && set +a
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001

# In a new terminal:
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --timeout 420

# Output appears in tests/accuracy/runs/cloud/{timestamp}/
```

## Files changed

| File | What |
|------|------|
| `tests/accuracy/evaluate_accuracy.py` | Multi-ref capture, debug/reasoning fields, timestamped run folders, run report + metadata generators, summary_metrics.csv, cloud retrieval metrics, API key check, bug fix |
| `tests/accuracy/README.md` | Restructured into eval/generation sections, cloud instructions, run folder documentation |
| `tests/accuracy/.gitignore` | Added `runs/` |
| `docs/decisions/003-accuracy-evaluator-cloud-mode.md` | ADR updated with run reporting and summary metrics changes |
| `docs/future-development/phase-4-evaluation.md` | Future evaluation improvements (cross-run comparison, CI, retrieval from API refs) |
| `docs/future-development/phase-3-generation-local.md` | Future local generation improvements (timeout, debug, GPU acceleration) |
| `docs/decisions/README.md` | ADR index |
| `statschat/pdf_processing/pdf_downloader.py` | Removed census exclusion filter |
| `statschat/pdf_processing/confirm_missing_downloads.py` | Removed census exclusion filter |
| `tests/unit/pdf_processing/test_pdf_downloader.py` | Test updated: census inclusion instead of exclusion |
| `scripts/download_census_2019.py` | One-off back-fill script for census PDFs |
| `docs/investigations/2026-04-01-census-2019-pdfs-excluded-from-scraper.md` | Investigation write-up |
| `tests/accuracy/KNBS_Verified_QA_Examples_updated.xlsx` | Filename fixes, Q001/Q002 removed |
| `tests/accuracy/KNBS_Verified_QA_Examples_updated_v2.xlsx` | Filename fixes, Q001/Q002 removed |
