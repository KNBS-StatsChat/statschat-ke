# Investigation: Missing downloads + MuPDF (PyMuPDF) shading/colorspace extraction errors

Date: 2026-02-04

Issue: **#84 Confirm missing downloads and investigate MuPDF shading colorspace errors**

## Executive summary

Two separate-but-related problems were investigated:

1) **“Missing downloads”**: KNBS hosts PDFs that StatsChat did not download.
2) **MuPDF/PyMuPDF extraction errors**: Some PDFs may raise page-level extraction errors (e.g., shading/colorspace) during text extraction.

### Outcome

- **Root cause for missing downloads identified and fixed**: the downloader previously recorded **only the first PDF link** found on each KNBS report page. Many KNBS report pages contain **multiple PDF attachments** (main report, highlights, abridged version, presentations, etc.). Those additional PDFs were never discovered, so they were never downloaded.
- **UPDATE run performed with the fix** and the previously “missing” set was largely recovered. The remaining “missing” item (in the small crawl window used at the end) corresponds to an **HTTP 404**.
- **MuPDF shading/colorspace errors were not reproduced** during the initial sample scan, but we added:
  - page-level exception handling,
  - optional fallback extraction using `pdfplumber`,
  - optional on-disk error logging,
  - a standalone scanner tool to find and report problematic PDFs.

## Background: what “missing downloads” means

The pipeline maintains a local index of downloaded PDFs via:

- `data/pdf_downloads/url_dict.json` (SETUP baseline)
- `data/latest_pdf_downloads/url_dict.json` (UPDATE staging)

When we say **“missing downloads”**, we mean:

- KNBS publishes a PDF and links it from a report page,
- but the pipeline never recorded that PDF URL in `url_dict.json`,
- so it never downloaded the file.

This is different from “files went missing on disk”.

## Terminology: “local integrity” (clarified)

In this investigation, **local integrity** means:

> “Does our local `url_dict.json` agree with what is actually present on disk?”

Concretely:

- Every `*.pdf` listed in `url_dict.json` exists on disk.
- There are no extra `*.pdf` files on disk that are not listed in `url_dict.json`.
- Files are non-empty and look like PDFs at a basic level (magic header `%PDF-`).

This is **an offline consistency check**. It does *not* prove we have everything KNBS publishes.

## What we did

### 1) Add an offline audit tool for local consistency

Added a tool to audit `url_dict.json` vs the PDFs on disk:

- Missing-on-disk
- Extra-on-disk
- Zero-byte PDFs
- Non-PDF-magic files

File added:
- `statschat/pdf_processing/audit_downloads.py`

Example run:

```bash
python -m statschat.pdf_processing.audit_downloads
```

Result on real data:
- No local inconsistencies found.
- Report: `outputs/download_audit_update_20260203_221757.json`

### 2) Confirm “missing downloads” by re-scraping KNBS (no downloads)

Added a script that re-scrapes KNBS report pages (listing pages -> report pages -> PDF anchors) and compares discovered filenames to local `url_dict.json` entries.

File added:
- `statschat/pdf_processing/confirm_missing_downloads.py`

Example run:

```bash
python -m statschat.pdf_processing.confirm_missing_downloads
```

Key evidence (wide crawl window):
- Report: `outputs/missing_downloads_report_20260203_224610.json`
- Crawl window: pages 1–41
- Discovered unique filenames: **1091**
- Local url_dict count: **946**
- Missing in local: **145**

This showed the missingness was primarily a **discovery/indexing** issue, not a disk-loss issue.

### 3) Fix downloader discovery: collect *all* PDFs per report page

The downloader used to do a single `find(...)` for `.pdf` links on each report page, which effectively kept only one PDF per report page.

Fix:
- change to `find_all(...)` and record **every** PDF anchor on the report page.

Other hardening added at the same time:
- request timeouts + User-Agent
- catch request exceptions
- record structured failures (HTTP errors, exceptions, and non-PDF content saved)
- optional sampling (`app.max_pdfs`) for quick debug runs

File changed:
- `statschat/pdf_processing/pdf_downloader.py`

New output:
- download failures report (when failures occur): `outputs/pdf_download_report_<mode>_<timestamp>.json`

### 4) Make PDF-to-JSON conversion resilient to extraction failures

Where MuPDF shading/colorspace errors typically surface: `page.get_text()`.

Changes:
- Catch exceptions per page and continue building JSON with empty text for that page.
- Optionally attempt `pdfplumber` fallback extraction for the failing page.
- Optionally persist extraction warnings/errors to `outputs/pdf_text_extraction_warnings.jsonl`.
- Wrap conversion per PDF to record failures without aborting the entire batch.

File changed:
- `statschat/pdf_processing/pdf_to_json.py`

Environment toggles:
- `STATSCHAT_PDFPLUMBER_FALLBACK` (default `1`): enable/disable fallback.
- `STATSCHAT_WRITE_EXTRACTION_WARNINGS=1`: write JSONL warnings.

### 5) Add an extraction error scanner to help find “shading/colorspace” PDFs

Added a standalone scanner that attempts `get_text()` for N pages of N PDFs and reports page errors.

File added:
- `statschat/pdf_processing/scan_text_extraction_errors.py`

Example run:

```bash
python -m statschat.pdf_processing.scan_text_extraction_errors \
  --dir data/pdf_downloads --max-pdfs 200 --max-pages 10
```

Result from initial scan sample:
- Report: `outputs/text_extraction_scan_20260203_233736.json`
- Scanned: 60 PDFs, 8 pages each
- PDFs with errors: 0

This means we didn’t reproduce the shading/colorspace error in that sample, but the tooling is now present to find it when it occurs.

## Running UPDATE mode: results

After applying the downloader fix, UPDATE mode was run to download newly discoverable PDFs.

Download attempt summary:
- Report: `outputs/pdf_download_report_update_20260204_001344.json`
- Attempted: **145**
- Saved: **142**
- Failures: **3**, all HTTP 404

A follow-up KNBS-vs-local comparison (narrow crawl window) shows missing has collapsed:
- Report: `outputs/missing_downloads_report_20260204_094052.json`
- Crawl window: pages 1–5
- Missing in local: **1**
- That missing item is one of the 404s from the download report.

### What “KNBS link rot (404)” means

In this context, **link rot** means:

- The KNBS report page (the HTML page under `https://www.knbs.or.ke/reports/...`) contains a link to a PDF, but
- when we request that PDF URL, the KNBS server responds with **HTTP 404 Not Found**.

So, the PDF is “missing” from our local dataset **because it is not downloadable from the URL KNBS currently publishes**.
This is different from a scraper bug:

- **Scraper bug**: we failed to discover or download a valid link.
- **Link rot (404)**: we discovered the link correctly, but the server says the file does not exist at that location.

Is this something KNBS needs to fix?

- **Possibly, yes**, if the 404 is persistent: it usually means the PDF was removed, renamed, moved, or the link on the report page is outdated.
- **Sometimes it’s transient** (temporary hosting issues), but repeated 404s across runs are strong evidence of an outdated/broken link.

What we should do on our side:

- Treat repeated 404s as **known dead links** so we don’t retry forever.
- Keep recording them in the download report so we can audit what we’re missing and, if needed, send KNBS the exact broken URLs/report pages.

### Important note on crawl window

The confirm script uses `app.page_start/app.page_end`.

- The original evidence of “145 missing” used a window of **page_end=41**.
- Later verification used **page_end=5** (narrower).

So the “missing count = 1” result is definitive **for pages 1–5**, and it strongly supports that the fix works; to fully validate “missing is near-zero” for pages 1–41 again, re-run the confirm script with `page_end=41`.

## Test changes

Unit and e2e tests were updated to match the new behavior:

- Downloader now handles timeouts by recording failures and still writing `url_dict.json` + a report (rather than raising).
- Valid PDF bytes in tests now come from creating a real PDF via PyMuPDF for stability across versions.
- Test isolation was improved by removing a global fake `fitz` module injection.

Files changed/added:
- `tests/unit/pdf_processing/test_pdf_downloader.py`
- `tests/unit/pdf_processing/test_pdf_to_json.py`
- `tests/unit/pdf_processing/test_audit_downloads.py`

## Recommendations / next steps

### A) Validate completeness across the intended crawl range

- Set `app.page_end` back to the intended value (e.g., 41) and re-run:

```bash
python -m statschat.pdf_processing.confirm_missing_downloads
```

Expectations:
- Missing should be close to 0, excluding any KNBS link rot (404s).

### B) Track KNBS link rot explicitly

The downloader now records HTTP 404 failures. Consider treating repeated 404s as “known dead links” to avoid repeated retries, and/or record them in a dedicated file for reporting.

### C) If MuPDF shading/colorspace errors appear later

When errors occur:

1) Enable warning persistence:

```bash
export STATSCHAT_WRITE_EXTRACTION_WARNINGS=1
```

2) Run the scanner over a larger set:

```bash
python -m statschat.pdf_processing.scan_text_extraction_errors --dir data/pdf_downloads --max-pdfs 500 --max-pages 10
```

3) Use the JSONL warnings + scan report to identify PDFs/pages and attach them to the GitHub issue for targeted remediation.

## Files introduced/modified (index)

New:
- `statschat/pdf_processing/audit_downloads.py`
- `statschat/pdf_processing/confirm_missing_downloads.py`
- `statschat/pdf_processing/scan_text_extraction_errors.py`
- `scripts/run_scratch_setup_sample.py`
- `tests/unit/pdf_processing/test_audit_downloads.py`

Modified:
- `statschat/pdf_processing/pdf_downloader.py`
- `statschat/pdf_processing/pdf_to_json.py`
- `tests/unit/pdf_processing/test_pdf_downloader.py`
- `tests/unit/pdf_processing/test_pdf_to_json.py`

Reports produced during this investigation:
- `outputs/download_audit_update_20260203_221757.json`
- `outputs/missing_downloads_report_20260203_224610.json`
- `outputs/pdf_download_report_update_20260204_001344.json`
- `outputs/missing_downloads_report_20260204_094052.json`
- `outputs/text_extraction_scan_20260203_233736.json`
