# Bug Fix: UPDATE Mode Path Concatenation Issue

**Date:** 2026-01-07
**Status:** Fixed
**File:** `docs/bugfix-update-mode-path-concatenation.md`

## Problem Description
An issue was reported where running the pipeline in `UPDATE` mode successfully downloaded new PDFs and converted them to JSON, but StatsChat failed to reference these new documents when answering questions.

## Experiment & Reproduction
We devised a test to reproduce and verify the fix:

1.  **Baseline Test (Pre-Update):**
    We asked StatsChat: *"What are the leading economic indicators for November 2025?"*
    *   **Expectation:** Failure, as the document was not yet present.
    *   **Result:** StatsChat could not answer, referencing older January/April reports.

2.  **Update Attempt:**
    We ran `pdf_runner.py` in `UPDATE` mode to fetch the missing "Leading Economic Indicators – November 2025" report.
    *   **Observation:** The logs showed "No document chunks to embed. Skipping embedding step." despite finding 10 new PDFs.

3.  **Post-Update Test:**
    We asked the same question again.
    *   **Result:** StatsChat still could not answer, confirming the new data was not indexed.

## Root Cause Analysis
The issue was located in `statschat/embedding/preprocess.py` within the `PrepareVectorStore` class.

When initializing the directory paths for `UPDATE` mode, `os.path.join` was used incorrectly with a conditional prefix:

```python
# INVALID CODE
self.directory = os.path.join(
    data_dir, ("latest_" if mode == "UPDATE" else ""), directory
)
```

`os.path.join` inserts a separator (slash) between arguments. When `mode == "UPDATE"`, this produced:
`data/` + `latest_` + `/` + `json_conversions` -> **`data/latest_/json_conversions`**

This directory does not exist (the actual directory is `data/latest_json_conversions`), causing the script to find 0 files to embed.

## The Fix
We modified the code to concatenate the prefix string directly with the directory name, rather than passing them as separate arguments to `os.path.join`.

```python
# FIXED CODE
self.directory = os.path.join(
    data_dir, ("latest_" if mode == "UPDATE" else "") + directory
)
```

This now correctly produces: **`data/latest_json_conversions`**.

## Verification Results
After applying the fix, we re-ran the experiment:

1.  **Update Process:** The logs confirmed successful embedding:
    > `Starting embedding of document chunks, please wait...`
    > `Vector store saved to data/db_langchain_latest`

2.  **Verification Query:** We asked: *"What are the leading economic indicators for November 2025?"*
    *   **Result:** StatsChat successfully retrieved the new document (`Kenya Leading Economic Indicators November 2025`) and provided the correct reference.
