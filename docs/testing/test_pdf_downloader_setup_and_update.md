# **PDF Downloader Test Suite**

This test suite validates the behavior of `pdf_downloader.py` in two operational modes: **SETUP** and **UPDATE**. Both tests use sample PDFs from the https://github.com/py-pdf/sample-files repository and mirror production logic for downloading, saving, and managing metadata.

This tests scripts can probably be combined as per `tests\unit\pdf_processing\test_pdf_downloader.py` and there are slight differences in both approaches

---

## **1. SETUP Mode (`test_pdf_downloader_setup.py`)**

### **Purpose**
Ensures correct initialization of the PDF download process and metadata handling during the initial setup phase.

### **Key Features**
- Downloads a sample PDF and saves it to:
  ```
  tests/test_data/pdf_downloads/
  ```
- Checks metadata fields and logs each as **FOUND** or **MISSING**.
- Creates a `url_dict.json` file with the expected structure (includes dummy `report_page`).
- Does **not** invoke `get_abstract_metadata` if metadata is missing.

### **Expected Metadata Fields**
- `title`
- `author`
- `producer`
- `creation_date`
- `modification_date`

### **Run Command**
```bash
pytest tests/unit/test_pdf_downloader_setup.py
```

---

## **2. UPDATE Mode (`test_pdf_downloader_update.py`)**

### **Purpose**
Validates incremental updates to the PDF download process, ensuring new PDFs are added and duplicates are avoided.

### **Key Features**
- Downloads sample PDFs and extracts metadata using **PyPDF2**.
- Verifies:
  - New PDFs are added to `url_dict`.
  - Existing PDFs are skipped with a logged message.
  - No duplicate entries are created.
- Saves PDFs to:
  ```
  tests/test_data/latest_pdf_downloads/
  ```
- Writes updated `url_dict.json` and validates its contents.
- Does **not** invoke `get_abstract_metadata` for missing metadata.

### **Expected Metadata Fields**
- `title`
- `author`
- `producer`
- `creation_date`
- `modification_date`

### **Run Command**
```bash
pytest tests/unit/test_pdf_downloader_update.py
```
