## PDF Text Extraction Evaluation

**Last Updated**: November 19, 2025

**Purpose**: Validate text extraction accuracy between PDFs and their JSON conversions using multiple extractors.

**Coverage**: Extraction accuracy, normalization, diff reporting, spelling checks, and summary generation.

---

## Overview
This script evaluates **PDF → JSON text consistency** across different extraction methods. It ensures:
- Text extracted from PDFs matches JSON conversion text.
- Differences are logged and summarized.
- Spelling and irregular character checks are performed.
- Reports are generated in **JSON**, **CSV**, and **Markdown** formats.

**Recent Updates**:
- ✅ Migrated from PyPDF2 to **pypdf**.
- ✅ Added support for **fitz (PyMuPDF)** and **pdfplumber**.
- ✅ Integrated normalization and diff filtering (ignores numeric differences).
- ✅ Generates combined summaries for quick review.

---

## Quick Start

### Run Full Evaluation
```bash
python tests/unit/pdf_processing/check_pdf_text_extraction.py