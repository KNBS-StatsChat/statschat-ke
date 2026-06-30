# PDF Ingestion Pipeline

This document details the first stage of the StatsChat-KE data pipeline: acquiring PDF reports from the KNBS website and converting them into structured JSON files for downstream processing.

## Conceptual Overview

The goal of this pipeline is to transform unstructured PDF documents hosted on the [KNBS website](https://www.knbs.or.ke) into a structured, machine-readable format. This involves two main steps:

1.  **Scraping & Downloading**: Crawling the website to find reports, downloading the PDFs, and maintaining a record of their source URLs.
2.  **JSON Conversion**: Extracting text from the PDFs, scraping additional metadata from the report pages, and combining this into a rich JSON schema.

The pipeline operates in two modes—**SETUP** (initial bulk ingestion) and **UPDATE** (incremental updates)—to ensure efficiency.

## Data Flow

```ascii
[KNBS Website]
      |
      v
+-------------------+
| pdf_downloader.py |
+-------------------+
      |
      | (Downloads PDFs + url_dict.json)
      v
[data/pdf_downloads/] OR [data/latest_pdf_downloads/]
      |
      v
+-------------------+
|  pdf_to_json.py   |
+-------------------+
      |
      | (Extracts text & metadata)
      v
[data/json_conversions/] OR [data/latest_json_conversions/]
```

## Pipeline Components

### 1. PDF Downloader (`pdf_downloader.py`)

This script is responsible for crawling the KNBS "All Reports" pages to locate and download PDF files.

-   **Entry Point**: `statschat/pdf_processing/pdf_downloader.py`
-   **Key Functions**:
    -   Iterates through paginated report lists (`https://www.knbs.or.ke/all-reports/page/{n}/`).
    -   Identifies report pages (URLs matching `/reports/`).
    -   Visits each report page to find the actual `.pdf` download link.
    -   Maintains a `url_dict.json` mapping filenames to their source URLs and report page URLs.

#### `url_dict.json`
This file is critical for the next step. It maps the local filename to its web source, allowing the converter to revisit the page for metadata.
```json
{
    "2023-Economic-Survey.pdf": {
        "pdf_url": "https://www.knbs.or.ke/.../2023-Economic-Survey.pdf",
        "report_page": "https://www.knbs.or.ke/reports/economic-survey-2023/"
    }
}
```

### 2. PDF to JSON Converter (`pdf_to_json.py`)

This script transforms the raw PDFs into structured data. It combines text extraction with web scraping to enrich the data.

-   **Entry Point**: `statschat/pdf_processing/pdf_to_json.py`
-   **Process**:
    1.  **Text Extraction**: Uses `PyMuPDF` (fitz) to extract text from every page of the PDF.
    2.  **Metadata Scraping**: Uses the `report_page` URL from `url_dict.json` to scrape the "About Report" section on the KNBS website. This provides high-quality metadata (Publication Date, Theme, Overview) that isn't always present in the PDF file properties.
    3.  **Fallback Logic**: If web metadata is missing, it falls back to PDF metadata or filename parsing.
    4.  **Output**: Saves a `.json` file for each PDF.

#### Output JSON Schema
Each generated JSON file contains:
-   **Metadata**: `title`, `release_date`, `theme`, `release_type`, `overview`, `url`.
-   **Content**: A list of page objects, each containing:
    -   `page_number`: Integer page number.
    -   `page_url`: Direct link to the specific page (e.g., `...pdf#page=5`).
    -   `page_text`: The raw text content of that page.

## Execution Modes: SETUP vs UPDATE

The pipeline behavior changes based on the `mode` setting in `config/main.toml`.

| Feature | SETUP Mode | UPDATE Mode |
| :--- | :--- | :--- |
| **Goal** | Ingest ALL available history. | Ingest only NEW reports. |
| **Download Source** | Scrapes up to 100 pages of reports. | Scrapes a limited range (default 5 pages) to find recent adds. |
| **Filtering** | Downloads everything. | Checks existing `url_dict.json` and skips known URLs. |
| **Download Dir** | `data/pdf_downloads/` | `data/latest_pdf_downloads/` |
| **JSON Dir** | `data/json_conversions/` | `data/latest_json_conversions/` |
| **Orchestration** | `pdf_runner.py` runs full sequence. | `pdf_runner.py` runs sequence, then triggers `merge_database_files.py`. |

### Directory Structure Implications

-   **SETUP**: Populates the main `data/` folders.
-   **UPDATE**: Uses `latest_` prefixed folders as a staging area. This prevents overwriting or reprocessing the entire dataset. The `merge_database_files.py` script (covered in the Embedding Pipeline docs) is responsible for merging these "latest" files into the main dataset.
