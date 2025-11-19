# Merge Database Files Tests Documentation

**Last Updated**: November 17, 2025  

**Test Count**: 1 test  

**Coverage**: Validation of merging new PDF and JSON data into the main database structure  

---

## Overview
This test ensures that **newly downloaded PDFs and their JSON conversions** are correctly merged into the main data directories. It validates:  
- Movement of files from `latest_*` directories to main directories.  
- Merging of `url_dict.json` entries without overwriting existing data.  
- Cleanup of temporary directories after merging.  

**Recent Updates**:  
- ✅ Added logging for file moves and dictionary merges.  
- ✅ Integrated config-driven directory paths for flexibility.  
- ✅ Strengthened assertions for file existence and dictionary integrity.  

---

## Quick Start

### Prepare Test Data
```bash
python tests/utils/create_sample_data_and_folder_structure.py
```

### Run All Tests
```bash
pytest -s -v tests/unit/pdf_processing/test_merge_database_files.py
```

---

## Test Structure

### Test Organization
```
Core Merge Test (1)
└── test_merge_database_files    # Validates merging of PDFs, JSONs, and URL dictionaries
```

---

## Test Details

### `test_merge_database_files`
**Type**: Integration test  
**Purpose**:  
- Move PDFs and JSON files from `latest_*` directories to main directories.  
- Merge `url_dict.json` entries without losing existing data.  
- Verify cleanup of temporary directories.  

**Checks**:  
- ✅ All PDFs moved to `pdf_downloads`  
- ✅ All JSON conversions moved to `json_conversions`  
- ✅ All split JSON files moved to `json_split`  
- ✅ `url_dict.json` merged correctly  
- ✅ No files remain in `latest_*` directories  

**Example Log Output**:  
```
INFO - Moved PDF: report.pdf → pdf_downloads/report.pdf
INFO - Moved JSON: report.json → json_conversions/report.json
INFO - Moved split JSON: report_1.json → json_split/report_1.json
INFO - Merged URL dictionaries successfully
```

---

## Fixtures
- **setup_test_data**: Creates and validates directory structure for test data  
  - `DATA_DIR`: Main PDF directory  
  - `JSON_CONVERSION`: Main JSON conversions directory  
  - `JSON_SPLIT_DIR`: Main split JSON directory  
  - `LATEST_*`: Temporary directories for new data  

---

## Logging
- Logs stored in `log/test_merge_database_files_<timestamp>.log`  
**Contents**:  
- File moves  
- Dictionary merge operations  
- Cleanup verification  

---

## Dependencies
- `pytest`  
- Standard library: `pathlib`, `json`, `logging`, `datetime`  

Install:  
```bash
pip install pytest
```

---

## Common Issues & Solutions

### Missing Test Data
**Error**: `AssertionError: No files found in latest directories`  
**Solution**:  
- Run `create_sample_data_and_folder_structure.py` before tests  

### Dictionary Merge Failure
**Cause**: Incorrect handling of duplicate keys  
**Solution**:  
- Ensure merge logic uses `update()` without overwriting existing entries  

---

## Future Enhancements
- [ ] Add validation for file integrity after move  
- [ ] Include rollback mechanism for failed merges  
- [ ] Add performance benchmarks for large datasets  

---
