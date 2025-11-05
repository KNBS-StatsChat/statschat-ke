# Page Splitting Tests Documentation

## Overview

The page splitting tests validate that PDF to JSON conversion maintains page integrity throughout the data ingestion pipeline.

---

## Test Files

### `test_page_splitting.py`

**Purpose**: Integration tests for PDF page counting and JSON validation

**Location**: `tests/unit/pdf_processing/test_page_splitting.py`

**Run with**: 
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v
```

#### Tests

##### `test_get_pdf_page_counts`
Validates that page counts are correctly extracted from PDF files.

**Checks**:
- ✅ Returns a dictionary of filename → page count
- ✅ At least one PDF is found
- ✅ All page counts are positive integers
- ✅ No errors during PDF reading

**Example Output**:
```
Found 50 PDFs with page counts
  2025-Economic-Survey.pdf: 245 pages
  2024-Statistical-Abstract.pdf: 312 pages
  ...
```

##### `test_validate_page_splitting`
Validates that JSON conversions maintain correct page counts from source PDFs.

**Checks**:
- ✅ At least one JSON file is found
- ✅ Each JSON file matches a source PDF (by filename)
- ✅ Page count in JSON matches page count in PDF
- ✅ All required JSON fields are present

**Validation Logic**:
1. Extract last page number from JSON `content` array
2. Match JSON filename to corresponding PDF
3. Compare last page number with PDF page count
4. Report any mismatches

**Example Failure**:
```
Page splitting validation failures:
  - 2025-Economic-Survey.json: Page count mismatch (JSON: 244, PDF: 245)
  - Unknown-Report.json: No matching PDF found
```

---

### `page_splitting_test_functions.py`

**Purpose**: Reusable helper functions for page splitting validation

**Location**: `tests/unit/pdf_processing/page_splitting_test_functions.py`

#### Functions

##### `get_pdf_page_counts(directory: Path) -> dict`

Scans a directory for PDF files and returns their page counts.

**Parameters**:
- `directory`: Path to directory containing PDF files

**Returns**:
- Dictionary: `{filename: page_count}`

**Example**:
```python
page_counts = get_pdf_page_counts(Path("data/pdf_downloads"))
# {'report1.pdf': 100, 'report2.pdf': 250}
```

**Error Handling**: Catches and logs individual PDF reading errors, continues processing remaining files.

---

##### `validate_page_splitting(json_folder: Path, expected_page_counts: dict) -> list`

Validates JSON conversion files against expected PDF page counts.

**Parameters**:
- `json_folder`: Path to directory containing JSON conversion files
- `expected_page_counts`: Dictionary from `get_pdf_page_counts()`

**Returns**:
- List of validation result dictionaries, each containing:
  - `json_file`: Name of the JSON file
  - `pdf_filename_in_json`: Filename extracted from JSON 'url' field
  - `matched_expected_filename`: The PDF filename that matched
  - `filename_match_found`: Boolean - was a matching PDF found?
  - `last_page_number_from_json_content`: Last page in JSON content array
  - `expected_page_count_from_pdf`: Expected page count from PDF
  - `page_count_matches`: Boolean - do the page counts match?
  - `error`: (Optional) Error message if processing failed

**Example**:
```python
results = validate_page_splitting(
    Path("data/json_conversions"),
    expected_page_counts
)

# Result structure:
[
    {
        'json_file': '2025-Economic-Survey.json',
        'pdf_filename_in_json': '2025-Economic-Survey.pdf',
        'matched_expected_filename': '2025-Economic-Survey.pdf',
        'filename_match_found': True,
        'last_page_number_from_json_content': 245,
        'expected_page_count_from_pdf': 245,
        'page_count_matches': True
    }
]
```

**Filename Matching Logic**:
- Extracts filename from JSON `url` field (last segment)
- Compares against expected PDF filenames (minus `.pdf` extension)
- Uses substring matching to handle URL encoding differences

---

## Test Fixtures

### `config`
Loads the main configuration file.

**Source**: `statschat.load_config(name="main")`

### `data_dir`
Path to PDF files directory, determined by config mode.

**Setup Mode**: `data/pdf_downloads`  
**Update Mode**: `data/latest_pdf_downloads`

### `json_dir`
Path to JSON conversion files directory, determined by config mode.

**Setup Mode**: `data/json_conversions`  
**Update Mode**: `data/latest_json_conversions`

---

## Logging

Tests generate detailed logs in `log/test_page_splitting_YYYY_MM_DD_HH-MM.log`

**Log Contents**:
- Configuration loading
- Directory paths being used
- Number of PDFs/JSONs found
- Individual validation results
- Success/failure summary

---

## Configuration Modes

Tests respect the `preprocess.mode` setting in `config/main.toml`:

- **SETUP**: Tests original data in `pdf_downloads/` and `json_conversions/`
- **UPDATE**: Tests latest data in `latest_pdf_downloads/` and `latest_json_conversions/`

---

## Dependencies

**Required Packages**:
- `pytest` - Test framework
- `pypdf` - PDF page counting (formerly PyPDF2)
- Standard library: `pathlib`, `json`, `logging`

---

## Common Issues

### No PDFs found
**Error**: `AssertionError: No PDFs found in data/pdf_downloads`

**Cause**: Directory is empty or doesn't exist

**Solution**: 
1. Check config mode setting
2. Verify PDFs have been downloaded
3. Check directory path is correct

### No matching PDF found
**Error**: `filename_match_found: False`

**Cause**: JSON filename doesn't match any PDF filename

**Possible reasons**:
- PDF was deleted after JSON creation
- Filename mismatch in URL
- Wrong directory being checked

### Page count mismatch
**Error**: `page_count_matches: False`

**Cause**: Last page in JSON doesn't match PDF page count

**Possible reasons**:
- PDF conversion failed partway through
- PDF was modified after JSON creation
- Conversion process has a bug (off-by-one, etc.)

---

## Running Tests

### Run all page splitting tests
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v
```

### Run with detailed output
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v -s
```

### Run specific test
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py::test_get_pdf_page_counts -v
```

### Run with coverage
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py --cov=statschat.pdf_processing --cov-report=html
```

---

## Future Enhancements

Planned improvements (Phase 2+):
- [ ] Edge case tests (empty directories, malformed JSON)
- [ ] Test fixtures for isolated testing
- [ ] Parameterized tests for different scenarios
- [ ] Mock-based unit tests
- [ ] Performance benchmarks
