# `test_pdf_to_json.py` — Unit Test Notes

This document explains what `tests/unit/pdf_processing/test_pdf_to_json.py` tests and why the current scope is a good fit for **StatsChat-KE**.

## Context: What We’re Protecting
The PDF processing pipeline produces JSON artifacts that downstream steps depend on:

- **Embedding** relies on stable schema and page text fields.
- **Retrieval correctness** depends on page numbering integrity and consistent URLs.
- **Update flows** depend on predictable metadata rules when KNBS pages or PDFs vary.

Because full ingestion is expensive and stateful (large `data/` folder, live network calls), these unit tests focus on deterministic behaviors and the JSON “contract”.

## Design Principles Used

### 1) Unit tests are deterministic and fast
These tests avoid:
- real network calls
- real PDF parsing
- relying on the user’s `data/` directory

Where the production code uses the current date, the tests freeze the clock to avoid midnight/CI flakiness.

### 2) Contract testing for `build_json`
Instead of trying to open real PDFs, the suite uses dependency injection (via `build_json` keyword-only parameters) to supply:
- a fake abstract metadata getter
- a fake metadata extractor
- a fake text extractor
- a deterministic ID generator

This validates the output JSON schema and invariants while keeping the test truly unit-level.

### 3) High-ROI behavioral coverage
We prioritize behaviors that can break ingestion/retrieval silently:
- date parsing and fallbacks
- keyword extraction
- modification date sanity checking
- schema fields that downstream components expect

## What Each Test Does (and Why)

### `test_extract_pdf_creation_date_prefers_metadata`
**What it checks**:
- A PDF metadata creation date like `D:20240115000000Z` is parsed into `YYYY-MM-DD`.

**Why it matters**:
- When metadata exists, it should be the most reliable source. Bad parsing here shifts dates across the corpus.

---

### `test_extract_pdf_creation_date_falls_back_to_filename_year`
**What it checks**:
- If metadata is missing, the function extracts a year from filenames like `2018-Survey-Report.pdf`.

**Why it matters**:
- Many PDFs in the corpus may have incomplete metadata; filename heuristics are a practical fallback.

---

### `test_extract_pdf_creation_date_uses_today_when_no_hints`
**What it checks**:
- If neither metadata nor filename year exists, the function uses today’s date and increments a counter.

**Why it matters**:
- This is the “last resort” path. It must be deterministic in tests, so the suite freezes `now()`.

---

### `test_convert_to_date_parses_month_year`
**What it checks**:
- Converts KNBS-style values like `"May 2025"` into `2025-05-01`.

**Why it matters**:
- KNBS pages often expose publication dates as month + year; this ensures consistent release dates.

---

### `test_convert_to_date_parses_year_only`
**What it checks**:
- Converts year-only strings like `"2025"` into `2025-01-01`.

**Why it matters**:
- Some KNBS pages may only provide the year.

---

### `test_convert_to_date_rejects_invalid`
**What it checks**:
- Invalid date formats raise `ValueError`.

**Why it matters**:
- Ensures bad input is not silently converted into incorrect dates.

---

### `test_extract_url_keywords_from_filename_unique_and_ordered`
**What it checks**:
- Extracts unique, hyphen-delimited tokens from a filename while preserving order.

**Why it matters**:
- `url_keywords` is used for query routing/retrieval relevance; it should be stable and not include duplicates.

---

### `test_extract_pdf_modification_date_falls_back_if_too_old`
**What it checks**:
- If the modification date is implausibly old (>~5 years earlier than the creation date), fall back to creation date.

**Why it matters**:
- Some PDFs contain broken `ModDate` values that can pollute metadata.

---

### `test_extract_pdf_modification_date_returns_moddate_when_reasonable`
**What it checks**:
- When the mod date is plausible, it’s returned.

**Why it matters**:
- Preserves legitimate modification dates for “last updated” type reasoning.

---

### `test_assemble_pdf_info_blanks_overview_when_title_only`
**What it checks**:
- Preserves a legacy invariant: if overview is just `title + " "`, it’s replaced with a blank placeholder.

**Why it matters**:
- Prevents “overview” from being redundant/noisy when KNBS pages repeat the title.

---

### `test_build_json_writes_expected_schema`
**What it checks**:
- `build_json` writes a JSON file with the expected fields and content structure.
- Uses injected fakes to avoid network/PDF parsing and to make the output deterministic.

**Why it matters**:
- This is the core contract test: it protects the shape of JSON artifacts the embedding/retrieval pipeline depends on.

## Why This Suite Is Sufficient (for this project)
This suite is sufficient because it covers the highest-risk behaviors that can silently break ingestion correctness while staying:
- **fast** (runs in a fraction of a second)
- **deterministic** (no network, no real PDFs, no reliance on local `data/`)
- **contract-focused** (validates the JSON output schema/invariants)

It intentionally does not attempt to validate PyMuPDF’s parsing correctness or KNBS website stability. Those belong in:
- integration tests (if we add a small, controlled fixture PDF)
- periodic manual/E2E runs on a dedicated environment

## Suggested Folder Name for This Style of Documentation
For a growing set of “why this test file exists” docs, a good pattern is:
- `docs/testing/guides/test_suite_notes/`

It’s explicit, fits your existing `docs/testing/guides/` structure, and scales cleanly as you add one doc per important test module.
