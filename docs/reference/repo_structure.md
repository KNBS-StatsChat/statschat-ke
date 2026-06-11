## Project Structure

This document describes the directory layout and key files. The `data/`
directories are local build artifacts not tracked in git.

### Repository Root

```
📦statschat-ke
 ┣ 📂data              ← local build artifacts (not in git; see Data section below)
 ┣ 📂docs              ← project documentation
 ┣ 📂fast-api          ← FastAPI backend entrypoints
 ┣ 📂flask-app         ← lightweight Flask demo frontend
 ┣ 📂log               ← pipeline and API log files (not in git)
 ┣ 📂outputs           ← download audit reports and run outputs
 ┣ 📂scripts           ← one-off utility and diagnostic scripts
 ┣ 📂statschat         ← core Python package
 ┣ 📂tests             ← automated tests (unit, integration, e2e, accuracy)
 ┣ 📜AGENTS.md         ← AI agent context file
 ┣ 📜Dockerfile        ← container definition for cloud deployment
 ┣ 📜LICENSE
 ┣ 📜pyproject.toml    ← package metadata and dependencies
 ┗ 📜README.md
```

### Data Directories

The `data/` folder is not tracked in git. It is populated by running the
ingestion pipeline. Directory names are configured in `main.toml`.

```
📦data
 ┣ 📂db_langchain_rebuild_v1      ← primary FAISS vector index (April 2026 rebuild)
 ┣ 📂db_langchain_rebuild_v1_latest  ← temporary index built during UPDATE; merged and removed
 ┣ 📂json_conversions             ← full-document JSON output from PDF extraction
 ┣ 📂json_split_rebuild_v1        ← section-level JSON chunks used to build the index
 ┣ 📂pdf_downloads                ← downloaded PDFs; contains url_dict.json
 ┣ 📂latest_pdf_downloads         ← staging area: new PDFs during UPDATE run
 ┣ 📂latest_json_conversions      ← staging area: new JSON conversions during UPDATE run
 ┗ 📂latest_json_split            ← staging area: new split JSONs during UPDATE run
```

> **Note:** `latest_*` directories and `db_langchain_*_latest` are staging areas
> used only during `UPDATE` runs. After the merge step they will be empty.
> The configured index and split directory names (`db_langchain_rebuild_v1`,
> `json_split_rebuild_v1`) reflect the April 2026 full index rebuild. If a new
> rebuild is performed with different settings, update `main.toml` to point to
> the new directories.

### Core Package: `statschat/`

```
📦statschat
 ┣ 📜__init__.py
 ┣ 📜api_common.py          ← shared FastAPI hardening helpers (CORS, auth, rate limiting, logging)
 ┣ 📜pdf_runner.py          ← orchestrates the full ingestion pipeline (SETUP or UPDATE)
 ┣ 📂config
 ┃ ┣ 📜main.toml            ← primary configuration file
 ┃ ┣ 📜questions.toml       ← sample questions for manual testing
 ┃ ┗ 📜utils.py             ← config loading helpers
 ┣ 📂embedding
 ┃ ┣ 📜preprocess.py        ← JSON splitting, embedding, FAISS index construction
 ┃ ┣ 📜latest_flag_helpers.py  ← helpers for latest-bulletin flagging
 ┃ ┗ 📜latest_updates.py    ← logic for identifying new publications in UPDATE mode
 ┣ 📂generative
 ┃ ┣ 📜cloud_llm.py         ← Inquirer class: retrieval + cloud LLM generation
 ┃ ┣ 📜local_llm.py         ← local Hugging Face generation path
 ┃ ┣ 📜prompts_cloud.py     ← prompt templates for cloud LLM
 ┃ ┣ 📜prompts_local.py     ← prompt templates for local LLM
 ┃ ┣ 📜query_policy.py      ← guardrail and temporal constraint detection
 ┃ ┣ 📜response_model.py    ← Pydantic response schema
 ┃ ┗ 📜utils.py             ← shared generation utilities
 ┣ 📂model_evaluation
 ┃ ┗ 📜evaluation.py        ← answer scoring helpers used by the accuracy evaluator
 ┗ 📂pdf_processing
   ┣ 📜audit_downloads.py           ← audits downloaded PDFs for completeness
   ┣ 📜confirm_missing_downloads.py ← cross-checks KNBS discovery against local url_dict
   ┣ 📜merge_database_files.py      ← moves staging files into main dirs after UPDATE
   ┣ 📜pdf_downloader.py            ← scrapes KNBS website and downloads PDFs
   ┣ 📜pdf_to_json.py               ← converts PDFs to structured JSON
   ┗ 📜scan_text_extraction_errors.py ← identifies PDFs with poor text extraction
```

### API Backends: `fast-api/`

```
📦fast-api
 ┣ 📜main_api_cloud.py   ← FastAPI app using cloud LLM (OpenRouter / OpenAI)
 ┗ 📜main_api_local.py   ← FastAPI app using local Hugging Face model
```

### Demo Frontend: `flask-app/`

```
📦flask-app
 ┣ 📜app.py              ← Flask application
 ┣ 📜requirements.txt    ← frontend-specific dependencies
 ┣ 📜Dockerfile          ← container definition for frontend deployment
 ┣ 📜deploy_app.sh       ← deployment helper script
 ┣ 📂templates           ← Jinja2 HTML templates
 ┗ 📂static              ← CSS, JS, and static assets
```

See [docs/guides/flask_demo_frontend.md](./guides/flask_demo_frontend.md) for
instructions on running the demo frontend.

### Tests: `tests/`

```
📦tests
 ┣ 📂unit           ← fast, isolated unit tests
 ┣ 📂integration    ← tests requiring the running API or database
 ┣ 📂e2e            ← end-to-end pipeline tests
 ┣ 📂accuracy       ← benchmark evaluation workflow (see tests/accuracy/README.md)
 ┗ 📂test_data      ← small fixture files used by unit tests
```
