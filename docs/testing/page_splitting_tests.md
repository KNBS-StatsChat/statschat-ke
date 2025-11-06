# Page Splitting Tests Documentation

**Last Updated**: November 6, 2025  
**Test Count**: 6 tests  
**Coverage**: Essential (integration tests + critical error handling)

## Overview

The page splitting tests validate that PDF to JSON conversion maintains page integrity throughout the data ingestion pipeline. These tests ensure that:
- PDF page counts are accurately extracted
- JSON conversions contain the correct number of pages
- Files are correctly matched between PDFs and their JSON representations
- Critical error conditions (corruption, mismatches) are detected


**Recent Updates**:
- ✅ Phase 1: Migrated from PyPDF2 to pypdf, strengthened assertions
- ✅ Phase 2: Streamlined to 6 essential tests (removed over-engineered edge cases)

---

## Quick Start

### Run All Tests
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v
```

### Run Specific Test Categories
```bash
# Integration tests only (uses real data)
pytest tests/unit/pdf_processing/test_page_splitting.py -k "test_get_pdf_page_counts or test_validate_page_splitting" -v

# Error handling tests only
pytest tests/unit/pdf_processing/test_page_splitting.py -k "malformed or mismatch or correct_match" -v

# Edge case tests only
pytest tests/unit/pdf_processing/test_page_splitting.py -k "empty" -v
```

**Expected Result**: `6 passed in ~2.5s`

---

## Test Structure

### Test Organization (6 essential tests)

```
Core Integration Tests (2)     - Use real production data
├── test_get_pdf_page_counts
└── test_validate_page_splitting

Edge Case & Error Handling (4) - Use tmp_path isolation
├── test_get_pdf_page_counts_empty_directory
├── test_validate_page_splitting_malformed_json
├── test_validate_page_splitting_page_count_mismatch
└── test_validate_page_splitting_correct_match
```

**Rationale**: Tests focus on real-world scenarios. The controlled data pipeline ensures JSON fields are always present, so tests for missing fields are unnecessary. Integration tests catch filename/page count issues with real data.

---

## Test Files

### `test_page_splitting.py`

**Purpose**: Comprehensive test suite for PDF page counting and JSON validation

**Location**: `tests/unit/pdf_processing/test_page_splitting.py`

---

## Integration Tests (Production Data)

### `test_get_pdf_page_counts`
**Type**: Integration test  
**Data**: Uses real PDFs from configured directory

Validates that page counts are correctly extracted from PDF files.

**Checks**:
- ✅ Returns a dictionary of filename → page count
- ✅ At least one PDF is found (fails if directory empty)
- ✅ All page counts are positive integers
- ✅ No errors during PDF reading
- ✅ Detailed logging of each PDF's page count

**Example Output**:
```
Found 50 PDFs with page counts
  2025-Economic-Survey.pdf: 245 pages
  2024-Statistical-Abstract.pdf: 312 pages
  Kenya-Consumer-Price-Indices-April-2025.pdf: 15 pages
```

**Assertions**:
```python
assert isinstance(page_counts, dict), "Result should be a dictionary"
assert len(page_counts) > 0, f"No PDFs found in {data_dir}"
for pdf_name, count in page_counts.items():
    assert isinstance(count, int), f"{pdf_name}: page count should be an integer"
    assert count > 0, f"{pdf_name}: page count should be positive, got {count}"
```

---

### `test_validate_page_splitting`
**Type**: Integration test  
**Data**: Uses real PDFs and JSONs from configured directories

Validates that JSON conversions maintain correct page counts from source PDFs.

**Checks**:
- ✅ At least one JSON file is found
- ✅ Each JSON file matches a source PDF (by filename)
- ✅ Page count in JSON matches page count in PDF
- ✅ All required JSON fields are present
- ✅ Comprehensive failure reporting (all failures shown together)

**Validation Logic**:
1. Extract last page number from JSON `content` array
2. Match JSON filename to corresponding PDF
3. Compare last page number with PDF page count
4. Track all failures and report together

**Example Success**:
```
Validated 50 JSON files
2025-Economic-Survey.json: filename_match=True, page_match=True, last_page=245, expected=245
✅ All page splitting validations passed
```

**Example Failure**:
```
Page splitting validation failures:
  - 2025-Economic-Survey.json: Page count mismatch (JSON: 244, PDF: 245)
  - Unknown-Report.json: No matching PDF found (extracted name: unknown-name.pdf)
```

---

## Edge Case Tests (Isolation with tmp_path)

### `test_get_pdf_page_counts_empty_directory`
**Purpose**: Validate handling of empty PDF directories  
**Expected**: Returns empty dict without errors

```python
page_counts = get_pdf_page_counts(empty_dir)
assert len(page_counts) == 0
```

### `test_get_pdf_page_counts_nonexistent_directory`
**Purpose**: Validate handling of non-existent directories  
**Expected**: Returns empty dict gracefully (Path.glob handles this)

### `test_validate_page_splitting_empty_json_directory`
**Purpose**: Validate handling of empty JSON directories  
**Expected**: Returns empty list without errors

### `test_validate_page_splitting_empty_expected_counts`
**Purpose**: Validate behavior when no PDFs were found  
**Expected**: Processes JSONs but reports no matches

**Test Data**:
```json
{"url": "http://example.com/test.pdf", "content": [{"page_number": 1}]}
```

**Expected Result**: `filename_match_found: False`

---

## Error Handling Tests

### `test_validate_page_splitting_malformed_json`
**Purpose**: Test graceful handling of invalid JSON syntax

**Test Data**: `{"url": "test.pdf", "content": [invalid json}`

**Validates**:
- ✅ Catches JSON parsing errors
- ✅ Includes error message in results
- ✅ Continues processing (doesn't crash)

**Expected Result**:
```python
assert "error" in results[0]
# error: "Expecting property name enclosed in double quotes..."
```

---

### `test_validate_page_splitting_page_count_mismatch`
**Purpose**: Verify detection of page count discrepancies

**Scenario**: JSON has 3 pages, PDF expects 5 pages

**Test Data**:
```json
{
    "url": "http://example.com/test.pdf",
    "content": [
        {"page_number": 1},
        {"page_number": 2},
        {"page_number": 3}
    ]
}
```

**Validates**:
- ✅ Filename matches correctly
- ✅ Page count mismatch is detected
- ✅ Detailed mismatch information is reported

**Expected Result**:
```python
assert results[0]['filename_match_found'] == True
assert results[0]['last_page_number_from_json_content'] == 3
assert results[0]['expected_page_count_from_pdf'] == 5
assert results[0]['page_count_matches'] == False
```

---

### `test_validate_page_splitting_filename_no_match`
**Purpose**: Verify detection when JSON doesn't match any PDF

**Scenario**: JSON filename "completely-different-name.pdf" vs PDFs "test.pdf", "other.pdf"

**Validates**:
- ✅ `filename_match_found` is False
- ✅ `matched_expected_filename` is None
- ✅ Processes without errors

---

### `test_validate_page_splitting_correct_match`
**Purpose**: Positive control - verify correct matches work

**Scenario**: JSON with 3 pages matches PDF with 3 pages

**Validates**:
- ✅ Filename matches
- ✅ Page count matches
- ✅ All fields populated correctly
- ✅ **This is the "everything works" baseline**

**Expected Result**:
```python
assert results[0]['filename_match_found'] == True
assert results[0]['page_count_matches'] == True
```

---

## Helper Functions

### `page_splitting_test_functions.py`

**Purpose**: Reusable helper functions for page splitting validation

**Location**: `tests/unit/pdf_processing/page_splitting_test_functions.py`

---

#### `get_pdf_page_counts(directory: Path) -> dict`

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

**Implementation**:
```python
from pypdf import PdfReader

pdf_page_counts = {}
for pdf_file in directory.glob("*.pdf"):
    with open(pdf_file, "rb") as f:
        reader = PdfReader(f)
        pdf_page_counts[pdf_file.name] = len(reader.pages)
```

**Error Handling**: Catches and logs individual PDF reading errors, continues processing remaining files.

---

#### `validate_page_splitting(json_folder: Path, expected_page_counts: dict) -> list`

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

**Error Handling**:
- Catches JSON parsing errors
- Handles missing 'url' or 'content' fields
- Returns error in result dict rather than crashing

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

### `tmp_path`
**Built-in pytest fixture**  
Provides temporary directory that's automatically cleaned up.

**Used by**: All edge case, error handling, negative, and parameterized tests

**Benefits**:
- Complete test isolation
- No dependency on production data
- Automatic cleanup
- Parallel test execution safe

---

## Logging

Tests generate detailed logs in `log/test_page_splitting_YYYY_MM_DD_HH-MM.log`

**Log Contents**:
- Configuration loading
- Directory paths being used
- Number of PDFs/JSONs found
- Individual validation results
- Success/failure summary

**Log Levels**:
- `INFO`: Normal operations, test progress
- `ERROR`: Processing failures, validation errors

**Example Log**:
```
2025-11-06 10:30:15 - test_page_splitting - INFO - Running test_get_pdf_page_counts
2025-11-06 10:30:17 - test_page_splitting - INFO - Found 50 PDFs with page counts
2025-11-06 10:30:17 - test_page_splitting - INFO -   2025-Economic-Survey.pdf: 245 pages
2025-11-06 10:30:20 - test_page_splitting - INFO - Running test_validate_page_splitting
2025-11-06 10:30:22 - test_page_splitting - INFO - Validated 50 JSON files
2025-11-06 10:30:22 - test_page_splitting - INFO - ✅ All page splitting validations passed
```

---

## Configuration Modes

Tests respect the `preprocess.mode` setting in `config/main.toml`:

- **SETUP**: Tests original data in `pdf_downloads/` and `json_conversions/`
- **UPDATE**: Tests latest data in `latest_pdf_downloads/` and `latest_json_conversions/`

---

## Dependencies

**Required Packages**:
- `pytest` - Test framework
- `pypdf` (5.1.0+) - PDF page counting (replaced deprecated PyPDF2)
- Standard library: `pathlib`, `json`, `logging`

**Installation**:
```bash
pip install pypdf pytest
```

---

## Common Issues & Solutions

### No PDFs found
**Error**: `AssertionError: No PDFs found in data/pdf_downloads`

**Cause**: Directory is empty or doesn't exist

**Solution**: 
1. Check config mode setting in `config/main.toml`
2. Verify PDFs have been downloaded
3. Check directory path is correct
4. Run: `ls data/pdf_downloads/*.pdf`

---

### No matching PDF found
**Warning**: `filename_match_found: False`

**Cause**: JSON filename doesn't match any PDF filename

**Possible reasons**:
- PDF was deleted after JSON creation
- Filename mismatch in URL
- Wrong directory being checked
- URL contains unexpected path structure

**Debug**:
```python
# Check what filename was extracted from JSON
print(result['pdf_filename_in_json'])

# Check what PDFs are expected
print(expected_page_counts.keys())
```

---

### Page count mismatch
**Error**: `page_count_matches: False`

**Cause**: Last page in JSON doesn't match PDF page count

**Possible reasons**:
- PDF conversion failed partway through
- PDF was modified after JSON creation
- Conversion process has a bug (off-by-one, etc.)
- Empty pages at end of PDF

**Debug**:
```python
# Check the discrepancy
print(f"JSON last page: {result['last_page_number_from_json_content']}")
print(f"PDF page count: {result['expected_page_count_from_pdf']}")

# Manually check the PDF
from pypdf import PdfReader
with open(pdf_path, 'rb') as f:
    reader = PdfReader(f)
    print(f"Actual pages: {len(reader.pages)}")
```

---

### Malformed JSON errors
**Error**: `error: "Expecting property name..."`

**Cause**: Invalid JSON syntax in conversion file

**Solution**:
1. Check the JSON file for syntax errors
2. Re-run PDF to JSON conversion
3. Check for encoding issues

---

## Running Tests

### Run all page splitting tests
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v
```

**Expected**: `6 passed in ~2.5s`

---

### Run with detailed output
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v -s
```

Shows print statements and detailed logging.

---

### Run specific test
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py::test_get_pdf_page_counts -v
```

---

### Run by category
```bash
# Integration tests only (uses real data)
pytest tests/unit/pdf_processing/test_page_splitting.py::test_get_pdf_page_counts tests/unit/pdf_processing/test_page_splitting.py::test_validate_page_splitting -v

# Error handling only
pytest tests/unit/pdf_processing/test_page_splitting.py -k "empty or nonexistent or malformed or corrupt" -v
```

---

### Run with coverage
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py \
    --cov=statschat.pdf_processing.pdf_to_json \
    --cov=tests.unit.pdf_processing.page_splitting_test_functions \
    --cov-report=html
```

View report: `open htmlcov/index.html`

---

### Run with timing
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py -v --durations=10
```

Shows the slowest tests.

---

## Test Performance

### Execution Time Breakdown
```
Total: ~2.5s (6 tests)

Integration tests (2):  ~2.48s  (uses real PDFs/JSONs)
Error handling (4):     ~0.02s  (isolated, uses tmp_path)
```

### Performance Tips
- Integration tests are slow (read real files)
- Isolated tests are fast (<0.02s combined)
- Run isolated tests during development
- Run integration tests before commits

---

## Test Development Guide

### Adding a New Test

1. **Choose test type**:
   - Integration: Uses real data, tests end-to-end
   - Isolated: Uses `tmp_path`, tests specific scenario

2. **Add test function**:
```python
def test_my_new_scenario(tmp_path):
    """
    Purpose: Brief description
    
    Validates:
    - ✅ First check
    - ✅ Second check
    """
    # Setup
    test_dir = tmp_path / "test_case"
    test_dir.mkdir()
    
    # Create test data
    test_json = test_dir / "test.json"
    test_json.write_text('{"url": "...", "content": [...]}')
    
    # Run function
    results = validate_page_splitting(test_dir, expected_counts)
    
    # Assert
    assert results[0]['field'] == expected_value, "Clear error message"
```
---

### Adding New Tests

1. **Identify the scenario** to test

2. **Choose test type**:
   - **Integration**: Uses real data, slow but comprehensive
   - **Error handling**: Uses tmp_path, fast and isolated

3. **Add to appropriate section** in test file

4. **Run and verify**:
```bash
pytest tests/unit/pdf_processing/test_page_splitting.py::test_my_new_scenario -v
```

---

## Migration History

### Phase 1 (November 5, 2025)
- ✅ Migrated from deprecated PyPDF2 to pypdf
- ✅ Removed module-level config loading
- ✅ Cleaned up Jupyter notebook artifacts
- ✅ Strengthened assertions with detailed validation
- ✅ Added comprehensive docstrings

### Phase 2 Expansion (November 5, 2025)
- ✅ Added 4 edge case tests
- ✅ Added 5 error handling tests
- ✅ Added 3 negative test cases
- ✅ Added 10 parameterized test instances
- ✅ Expanded coverage: 2 → 23 tests (+1,050%)

### Phase 2 Streamlining (November 6, 2025)
- ✅ Removed 17 redundant tests based on user feedback
- ✅ Kept only essential tests: 2 integration + 4 error handling
- ✅ Rationale: User's pipeline controls JSON creation, so missing field scenarios don't occur in practice
- ✅ Final count: 23 → 6 tests (focused on real-world issues)

---

## Related Documentation

- **Phase 1 Changes**: `docs/testing/phase1_page_splitting_improvements.md`
- **Phase 2 Changes**: `docs/testing/phase2_enhanced_coverage.md` (historical - documents 23 test version)
- **Source Code**: `statschat/pdf_processing/pdf_to_json.py`
- **Test Helpers**: `tests/unit/pdf_processing/page_splitting_test_functions.py`

---

## Future Enhancements

### Potential Additions (Only If Needed)
- [ ] Performance tests (if processing time becomes an issue)
- [ ] Special character/Unicode tests (if conversion errors occur)
- [ ] Coverage reporting integration

### Current Philosophy
- Keep tests simple and focused
- Test real-world scenarios, not edge cases that can't happen
- Integration tests catch actual issues
- Avoid over-engineering the test suite

---

**Last Updated**: November 6, 2025  
**Status**: ✅ Streamlined to 6 essential tests
