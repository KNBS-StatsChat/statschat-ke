# Operating Manual

*COULD DO WITH UPDATING TO ALSO INCLUDE HOW TO RUN STATSCHAT OR CLEARLY DEFINE THIS DOCUMENT*

---

This document provides detailed instructions for configuring, running, and managing the `StatsChat-KE` data pipeline. It is intended for developers and operators who need to ingest data or update the vector store.

## 1. System Configuration
The system's behavior is primarily controlled by `statschat/config/main.toml`. Before running any scripts, ensure this configuration matches your intent.

### Modes: SETUP vs UPDATE
The `pdf_files_mode` parameter determines the pipeline's strategy.

*   **SETUP Mode**:
    *   **Goal**: Initial bulk ingestion.
    *   **Behavior**: Scrapes *all* available PDFs from the target page range. Ignores previous state.
    *   **Use Case**: First-time installation or complete rebuilds.

*   **UPDATE Mode**:
    *   **Goal**: Incremental updates.
    *   **Behavior**: Scrapes only the most recent pages (controlled by `max_pages`). Filters out files that already exist in `url_dict.json`.
    *   **Use Case**: Weekly/Monthly data refreshes.

## 2. Running Data Ingestion

### Configuring Page Ranges
To save time during development or testing, you can limit the scope of the scraper in `main.toml` (under `[app]`) or by modifying `pdf_downloader.py` arguments.

*   `page_start`: The page number on the KNBS website to start scraping from.
*   `page_end`: The page number to stop at.

> **Note**: Higher page numbers on the KNBS website correspond to *older* publications.
> *   `page=1`: Most recent reports.
> *   `page=38`: Reports from ~2010.

#### Example Scenarios
*   **Scrape everything**: `page_start=1`, `page_end=100` (or sufficient max).
*   **Scrape only old archives**: `page_start=37`, `page_end=38`.

### The Update Logic ("Merge-and-Move")
When running in **UPDATE** mode, the system uses a staging approach to prevent data corruption.
1.  **Download**: New files are saved to `data/latest_pdf_downloads/`.
2.  **Process**: JSON conversions are saved to `data/latest_json_conversions/`.
3.  **Embed**: A temporary vector index is built in `data/db_langchain_latest/`.
4.  **Merge**: The `merge_database_files.py` script moves files from `latest_` directories to the main directories and merges the vector indices.

## 3. Troubleshooting
*   **Missing Files**: If PDFs are failing to download, check `logs/` for HTTP 404 errors or connection timeouts.
*   **Zero-Byte Files**: ensure `pdf_downloader.py` is not being blocked by a firewall.
*   **OpenRouter model errors**: If generation fails with `No endpoints found`, update `statschat/config/main.toml` to a currently served model. The current free default is `mistralai/mistral-small-3.1-24b-instruct:free`; a low-cost paid option to consider later is `mistralai/mistral-nemo`.
