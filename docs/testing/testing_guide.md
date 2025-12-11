# Testing Guide for StatsChat-KE

This guide outlines essential testing strategies for new users working with a Python package that processes PDFs for chatbot applications. The package includes modules like `pdf_to_json.py` and `pdf_downloader.py`.
---

## Code Functionality Testing

**Purpose:** Ensure all functions and modules behave as expected.

**What to Test:**
- Core logic and expected outputs
- Edge cases and invalid inputs
- Integration between components

**Tools to Use:**
- `pytest`
- `unittest`
- Optional: `coverage` for test coverage analysis

---

### 1. Text Extraction Accuracy

**Purpose:** Check that extracted text matches the original content of the PDF.

**Test Strategy:**
- Compare extracted text against ground-truth data from sample PDFs.

**Why It Matters:**
- Ensures the extraction logic does not omit or distort content.

**Relevant Module:**
- `pdf_to_json.py`

---

### 2. Metadata Extraction Robustness

**Purpose:** Confirm that metadata fields are correctly parsed and handled.

**Test Strategy:**
- Check for presence and correctness of fields like title, author, and creation date.
- Use PDFs with complete, missing, or malformed metadata.

**Why It Matters:**
- Many PDFs have inconsistent metadata; the code should handle these gracefully.

**Relevant Modules:**
- `pdf_to_json.py`
- `pdf_downloader.py`

---

### 3. Error Handling for Corrupt or Unusual PDFs

**Purpose:** Ensure the system fails gracefully when encountering problematic files.

**Test Strategy:**
- Use intentionally corrupted or oddly formatted PDFs.
- Verify that the system logs errors and skips files without crashing.

**Why It Matters:**
- Prevents pipeline failures due to bad input files.

**Relevant Module:**
- `pdf_to_json.py`

---

### 4. Unicode and Encoding Issues

**Purpose:** Verify correct handling of non-ASCII characters.

**Test Strategy:**
- Use PDFs containing accented letters, symbols, and multilingual text.

**Why It Matters:**
- Supports internationalization and prevents garbled output.

**Relevant Module:**
- `pdf_to_json.py`

---

### 5. Page and Section Splitting

```
pytest tests/e2e/test_page_splitting.py -s
```

**Purpose:** Check that documents are segmented correctly.

**Test Strategy:**
- Confirm that splitting logic divides content by page as expected.
- Ensure no content is lost or duplicated.

**Why It Matters:**
- Accurate segmentation is critical for downstream semantic search and chatbot context.

**Relevant Module:**
- `pdf_to_json.py`

---

### 6. Performance and Scalability

**Purpose:** Assess system behavior with large documents.

**Test Strategy:**
- Run extraction on large PDFs.
- Measure runtime and memory usage.

**Why It Matters:**
- Ensures the system can handle real-world, high-volume documents efficiently.

**Relevant Module:**
- `pdf_to_json.py`

---

## Tips for New Users

- Begin testing with small, well-structured PDFs.
- Gradually introduce corrupted files.
- Monitor logs for unexpected behavior.
- Use `pytest` options like `--maxfail=1` and `--disable-warnings` for focused debugging.

---
