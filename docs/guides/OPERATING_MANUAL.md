# Operating Manual

This document covers configuring, running, and managing StatsChat-KE. It is intended for developers and operators who need to ingest data, update the vector store, or run the API.

For first-time installation, see [setup_guide.md](./setup_guide.md) and [environment_setup.md](./environment_setup.md) first.

---

## Contents

1. [System Configuration](#1-system-configuration)
2. [Running Data Ingestion](#2-running-data-ingestion)
3. [Running the API](#3-running-the-api)
4. [Making Queries](#4-making-queries)
5. [Logs](#5-logs)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. System Configuration

All system behaviour is controlled by `statschat/config/main.toml`. Review and update this file before running any scripts.

### Pipeline Mode: SETUP vs UPDATE

The `mode` key under `[preprocess]` determines how the ingestion pipeline behaves.

| Mode | Goal | Behaviour | When to use |
|---|---|---|---|
| `SETUP` | Full rebuild | Scrapes all PDFs from the configured page range; builds the vector store from scratch | First-time setup or a full index rebuild |
| `UPDATE` | Incremental refresh | Scrapes only the most recent pages; skips PDFs already in `url_dict.json`; merges new content into the existing index | Routine data refreshes when new KNBS reports are published |

```toml
# statschat/config/main.toml
[preprocess]
mode = "SETUP"   # or "UPDATE"
```

### Page Range Configuration

The `[app]` section controls how many KNBS website pages are scraped. Higher page numbers correspond to older publications.

```toml
[app]
page_start = 1    # page 1 = most recent reports
page_end   = 5    # page ~38 = reports from ~2010
```

**Example scenarios:**
- Scrape the full archive: `page_start = 1`, `page_end = 100`
- Scrape only recent reports: `page_start = 1`, `page_end = 5`
- Scrape old archives only: `page_start = 37`, `page_end = 38`

---

## 2. Running Data Ingestion

With the configuration set, run the full pipeline using:

```shell
python statschat/pdf_runner.py
```

This single script orchestrates all pipeline steps in sequence. Progress is logged to `log/`.

### What the pipeline does

**SETUP mode:**
1. Download all PDFs → `data/pdf_downloads/`
2. Convert PDFs to JSON → `data/json_conversions/`
3. Split and embed documents → builds the FAISS vector store at the configured `faiss_db_root`

**UPDATE mode (staging approach):**
1. Download new PDFs → `data/latest_pdf_downloads/`
2. Convert new PDFs to JSON → `data/latest_json_conversions/`
3. Split and embed new documents → builds a temporary FAISS index at `{faiss_db_root}_latest`; then merges it into the main index
4. Move staged files into the main directories (`data/pdf_downloads/`, `data/json_conversions/`, `data/json_split/`) and merge `url_dict.json`

The staging approach means the main index is only updated after all new content has been successfully processed.

---

## 3. Running the API

StatsChat-KE has two API variants. Both expose the same endpoints; the difference is how they generate answers.

| Variant | Script | LLM | When to use |
|---|---|---|---|
| Cloud | `fast-api/main_api_cloud.py` | Remote model via OpenRouter / OpenAI (configured in `main.toml`) | Default for development and production |
| Local | `fast-api/main_api_local.py` | Mistral-7B downloaded and run locally | Offline use; requires ~16 GB RAM |

### Start the cloud API

```shell
uvicorn fast-api.main_api_cloud:app --reload
```

### Start the local API

```shell
uvicorn fast-api.main_api_local:app --reload
```

> **Note:** The local API downloads the model on first startup. This can take several minutes.

The API will be available at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` in your browser for the interactive Swagger UI.

### Production / deployed instances

For deployed environments, set the following environment variables instead of committing secrets:

```shell
export OPENROUTER_API_KEY=...
export STATSCHAT_API_KEY=...            # enables API key auth on /search and /feedback
export STATSCHAT_CORS_ORIGINS=https://your-frontend.example
export STATSCHAT_RATE_LIMIT_PER_MINUTE=10
```

When `STATSCHAT_API_KEY` is set, the `/search` and `/feedback` endpoints require either an `X-API-Key` header or an `Authorization: Bearer ...` header. The `/health` endpoint remains public.

---

## 4. Making Queries

### Browser

```
http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023
```

Append `&content_type=all` to search the full archive rather than only the latest bulletins (the default).

### curl

```shell
curl "http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023"
```

With API key authentication:

```shell
curl -H "X-API-Key: your_api_key" \
     "http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023"
```

### Response format

The API returns JSON with the following fields:

| Field | Description |
|---|---|
| `question` | The sanitised input question |
| `content_type` | `"latest"` or `"all"` |
| `answer` | Generated answer text (empty string if no answer meets the threshold) |
| `references` | Retrieved source documents used to construct the answer |
| `debug_response` | Full LLM response object (included when `debug=true`, the default) |

### Health check

```shell
curl http://127.0.0.1:8000/health
```

Returns non-secret runtime status including the active model name and whether the model is loaded.

---

## 5. Logs

All pipeline and API logs are written to `log/`. Log filenames include a timestamp and the run type:

- `statschat_preprocess_YYYY_MM_DD_HH:MM.log` — ingestion pipeline runs
- `statschat_api_YYYY_MM_DD_HH:MM.log` — API request logs (JSON-lines format in production)

---

## 6. Troubleshooting

- **PDFs failing to download**: Check `log/` for HTTP 404 errors or connection timeouts. Zero-byte files usually indicate a firewall or network issue blocking the download.
- **`No existing url_dict.json` error in UPDATE mode**: The primary `data/pdf_downloads/url_dict.json` index is missing. Either run `SETUP` first or restore the file from backup before running `UPDATE`.
- **OpenRouter model errors (`No endpoints found`)**: The configured model may no longer be served. Update `generative_model_name_cloud` in `statschat/config/main.toml`. The current cloud model is `openai/gpt-5.4-mini`; a low-cost alternative is `mistralai/mistral-nemo`.
- **Local API OOM / slow generation**: The local model requires ~16 GB RAM. Consider using the cloud API instead, or set `STATSCHAT_GENERATIVE_MODEL` in `.env` to override the model without editing `main.toml`.

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
*   **OpenRouter model errors**: If generation fails with `No endpoints found`, update `statschat/config/main.toml` to a currently served model. Also remember that a served route can still be unstable for structured-output tasks. The April 2026 benchmark used `mistralai/mistral-small-3.1-24b-instruct`, but May 2026 replication probes showed that this OpenRouter route could return truncated JSON. For current Mistral-family comparisons, prefer `mistralai/mistral-small-24b-instruct-2501` or `mistralai/mistral-small-3.2-24b-instruct`. A low-cost paid option to consider later is `mistralai/mistral-nemo`.
