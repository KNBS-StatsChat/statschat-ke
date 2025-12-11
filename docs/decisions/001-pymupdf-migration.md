# ADR-001: Migration from pypdf to PyMuPDF (fitz) for PDF Processing

**Status:** Accepted  
**Date:** 2024-12-02  
**Branch:** `production_fitz`

## Context

The statschat-ke application processes PDF documents from the Kenya National Bureau of Statistics (KNBS) website, converting them to JSON format for embedding and retrieval. The original implementation used `pypdf` for all PDF operations.

### Problem Statement

We needed to:
1. Improve PDF text extraction quality, especially for statistical documents with complex tables
2. Increase processing speed for large batch operations
3. Establish a dual-library testing strategy to validate PDF-to-JSON conversion accuracy

## Decision

**Primary (Production):** PyMuPDF (`fitz`)  
**Secondary (Testing/Validation):** `pypdf` and `pdfplumber`

### Why PyMuPDF?

| Criteria | pypdf | PyMuPDF | pdfplumber |
|----------|-------|---------|------------|
| **Speed** | Slower | Fast | Medium |
| **Text extraction quality** | Basic | Superior | Good (table-focused) |
| **Complex layout handling** | Limited | Excellent | Good |
| **Table extraction** | Poor | Good | Excellent |
| **Memory efficiency** | Good | Excellent | Good |
| **Active maintenance** | Yes | Yes | Yes |

PyMuPDF provides the best balance of speed and extraction quality for our statistical document use case.

### Testing Strategy

Using multiple libraries for validation:
- **PyMuPDF (fitz):** Primary production extraction
- **pypdf:** Cross-validation for text extraction
- **pdfplumber:** Specialized validation for tabular content

This allows detection of extraction issues by comparing outputs across libraries.

---

## Changes Made

Prior to 2025-12-02 we used pypdf for pdf conversion in the production mode. On 2025-12-02 we switched to use PyMuPDF. Here are the changes required for that transition. 

### Key Differences Between pypdf and PyMuPDF

Beyond just renaming imports, these libraries have fundamentally different APIs that require code changes:

| Aspect | pypdf | PyMuPDF | Impact |
|--------|-------|---------|--------|
| **Document object** | `PdfReader` class | `fitz.Document` (via `fitz.open()`) | Different instantiation pattern |
| **Metadata structure** | Object with attributes (e.g., `metadata.modification_date`) | Dictionary with string keys (e.g., `metadata.get("modDate")`) | Must change from attribute access to dict access |
| **Metadata key format** | Slash prefix, PascalCase (e.g., `/CreationDate`) | No slash, camelCase (e.g., `creationDate`) | Must update all metadata key references |
| **Text extraction method** | `page.extract_text()` | `page.get_text()` | Simple method rename |
| **Page access** | `reader.pages[i]` returns page object | `doc[i]` returns page object | Slightly different syntax |
| **Page count** | `len(reader.pages)` | `len(doc)` or `doc.page_count` | Direct length on document |
| **Resource management** | Context manager / auto-cleanup | Manual `doc.close()` required | Must add explicit cleanup |

### Why These Differences Exist

- **pypdf** is a pure-Python library that models PDF structure closely, using slash-prefixed keys that match the raw PDF specification
- **PyMuPDF** wraps the MuPDF C library, exposing a more Pythonic dict-based API with cleaner key names
- The metadata attribute vs dictionary difference is the most impactful change, requiring refactoring of date extraction logic

### Files Modified

#### Production Code

**`statschat/pdf_processing/pdf_to_json.py`**

| Function | Change |
|----------|--------|
| Import | `from pypdf import PdfReader` → `import fitz` |
| `get_name_and_meta()` | `PdfReader().metadata` → `fitz.open().metadata` |
| `extract_pdf_text()` | `page.extract_text()` → `page.get_text()` |
| `extract_pdf_creation_date()` | Updated metadata key: `/CreationDate` → `creationDate` |
| `extract_pdf_modification_date()` | `metadata.modification_date` → `metadata.get("modDate")` |

#### Test Code

**`tests/unit/pdf_processing/page_splitting_test_functions.py`**
- Replaced `pypdf.PdfReader` with `fitz.open()` for page counting

**`tests/unit/pdf_processing/pdf_text_extraction_test_functions.py`**
- Renamed method parameter `"pypdf2"` → `"pypdf"` for consistency
- Multi-library extraction support retained (`fitz`, `pypdf`, `pdfplumber`)

### API Mapping Reference

| Operation | pypdf | PyMuPDF |
|-----------|-------|---------|
| Import | `from pypdf import PdfReader` | `import fitz` |
| Open PDF | `PdfReader(path)` | `fitz.open(path)` |
| Metadata access | `reader.metadata` (object) | `doc.metadata` (dict) |
| Creation date key | `/CreationDate` | `creationDate` |
| Modification date | `metadata.modification_date` | `metadata.get("modDate")` |
| Text extraction | `page.extract_text()` | `page.get_text()` |
| Page count | `len(reader.pages)` | `len(doc)` |
| Resource cleanup | Context manager | `doc.close()` |

### Metadata Date Format

Both libraries use the PDF date format `D:YYYYMMDDHHmmSS`, but access patterns differ:

```python
# pypdf (old)
creation_date = metadata.get("/CreationDate")  # Slash prefix
mod_date = metadata.modification_date  # Attribute access

# PyMuPDF (new)
creation_date = metadata.get("creationDate")  # camelCase, no slash
mod_date = metadata.get("modDate")  # Dict access only
```

## Consequences

### Positive

- **Faster processing:** PyMuPDF is significantly faster for batch operations
- **Better extraction:** Improved handling of complex layouts common in KNBS statistical reports
- **Validation capability:** Dual-library testing can detect extraction errors
- **Future-proof:** PyMuPDF has excellent maintenance and documentation

### Negative

- **Learning curve:** Team needs familiarity with PyMuPDF API differences
- **Metadata handling:** More manual parsing required for dates (dict vs object)

### Risks

- **Extraction differences:** PyMuPDF may extract text differently than pypdf for some documents
- **Mitigation:** Use pdfplumber as a third validation source; maintain comparison tests

## Validation

Run tests to validate the migration:

```bash
# Page splitting tests
pytest tests/unit/pdf_processing/test_page_splitting.py -s

# Text extraction comparison tests  
pytest tests/unit/pdf_processing/test_pdf_text_extraction.py -s
```

## Dependencies

All required libraries are already in `pyproject.toml`:

```toml
dependencies = [
    "pypdf==5.1.0",        # Retained for testing
    "PyMuPDF==1.24.4",     # Primary (production)
    "pdfplumber==0.11.7",  # Testing (table validation)
]
```

## References

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- [Architecture Decision Records](https://adr.github.io/)
