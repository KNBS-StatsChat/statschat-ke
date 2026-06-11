# Documentation Index

This folder contains all documentation for StatsChat-KE. Use this file as your
starting point.

---

## New to the project? Start here

Read these in order for a complete onboarding:

1. [SPECIFICATION.md](./SPECIFICATION.md) — what the project is, its guiding principles, current status, known limitations, and recommended next steps
2. [Root README](../README.md) — architecture diagram and quick-start commands
3. [setup_guide.md](./setup_guide.md) — Python environment and dependency installation
4. [environment_setup.md](./environment_setup.md) — `.env` file, API keys, provider configuration
5. [OPERATING_MANUAL.md](./OPERATING_MANUAL.md) — running the data pipeline and the API
6. [architecture/README.md](./architecture/README.md) — how the pipeline components fit together (technical depth)
7. [CONTRIBUTING.md](./CONTRIBUTING.md) — branching, PR workflow, code style, pre-commit hooks

---

## Document Index

### Project Context and Vision

| File | Description |
|---|---|
| [SPECIFICATION.md](./SPECIFICATION.md) | What StatsChat-KE is, its guiding principles, current status, known limitations, recommended next steps, and future directions |

### Setup & Onboarding

| File | Description |
|---|---|
| [setup_guide.md](./setup_guide.md) | Installation on Mac and Windows; virtual environment setup |
| [environment_setup.md](./environment_setup.md) | `.env` configuration; API key setup for OpenRouter, OpenAI, HuggingFace |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Developer setup, branching strategy, PR workflow, code quality |

### Operations

| File | Description |
|---|---|
| [OPERATING_MANUAL.md](./OPERATING_MANUAL.md) | Configuring and running the ingestion pipeline and API; query examples; troubleshooting |
| [update_db.md](./update_db.md) | Quick reference for adding new KNBS publications to the vector store |
| [set_recurring_server_job.md](./set_recurring_server_job.md) | Setting up a scheduled (cron) job for recurring `UPDATE` runs |

### Frontends

| File | Description |
|---|---|
| [guides/flask_demo_frontend.md](./guides/flask_demo_frontend.md) | Running the lightweight Flask browser frontend for demos |

> **Note:** A separate frontend developed by the KNBS team exists but is maintained in its own repository and is not covered here.

### Architecture

| File | Description |
|---|---|
| [architecture/README.md](./architecture/README.md) | Hub overview: how all four pipeline stages connect |
| [architecture/pipeline-pdf-ingestion.md](./architecture/pipeline-pdf-ingestion.md) | PDF discovery, download, and JSON conversion |
| [architecture/pipeline-embedding.md](./architecture/pipeline-embedding.md) | JSON splitting, embedding, and FAISS index construction |
| [architecture/pipeline-retrieval.md](./architecture/pipeline-retrieval.md) | Semantic search and reranking |
| [architecture/pipeline-generation.md](./architecture/pipeline-generation.md) | LLM interaction and response parsing |
| [architecture/pipeline-input-output.md](./architecture/pipeline-input-output.md) | API request/response contract |
| [architecture/token-usage-guide.md](./architecture/token-usage-guide.md) | Token calculation and configuration tuning |
| [repo_structure.md](./repo_structure.md) | Directory layout and data folder structure |

### Configuration

| File | Description |
|---|---|
| [config_guide.md](./config_guide.md) | All `main.toml` configuration sections, keys, and current parameter values |

### Deployment

| File | Description |
|---|---|
| [server_deployment.md](./server_deployment.md) | Docker and production API deployment; runtime environment variables |
| [server_troubleshooting.md](./server_troubleshooting.md) | Common server and deployment issues |

### Automated Evaluation

The accuracy evaluation system is the **feedback loop for the whole project**.
It is not just a test suite — it is the mechanism by which any change to the
model, retrieval architecture, configuration, or corpus is validated against a
known quality baseline before being accepted.

The core idea is:

1. A curated benchmark workbook (`StatsChat_QA_Verified_Audited.xlsx`) contains
   questions with known correct answers, sourced directly from KNBS publications.
2. The evaluator runs those questions against the live API and scores the
   responses against the known answers.
3. The results are archived with a timestamp, and a cross-run ledger tracks
   accuracy over time across models and configurations.
4. Any drop in accuracy signals a regression. Any improvement should be
   confirmed here before being treated as real.

This means: **before changing the model, the retrieval config, the FAISS index,
or deploying a new version, run the evaluator and compare against the current
baseline.** The April 2026 audited baseline (cloud GPT-5.4-mini, 74-row
benchmark) is the current reference: `70/74 = 0.946` overall accuracy.

| File | Description |
|---|---|
| [tests/accuracy/README.md](../tests/accuracy/README.md) | Full technical documentation: scripts, workflow, metrics, and local/cloud parity |
| [guides/replication_instructions.md](./guides/replication_instructions.md) | Step-by-step instructions for replicating a benchmark accuracy run |
| [reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md](./reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md) | Recommended accuracy monitoring model for ongoing KNBS maintenance |
| [reports/](./reports/) | Archived accuracy evaluation reports |
| [saved_runs/](./saved_runs/) | Timestamped output snapshots from benchmark evaluation runs |

### Unit & Integration Tests

| File | Description |
|---|---|
| [testing/](./testing/) | Test strategy, test data notes, and evaluation methodology |
| [guides/latest_filtering.md](./guides/latest_filtering.md) | How latest-only filtering works and when to use `content_type=all` |
| [text_extraction_summary.md](./text_extraction_summary.md) | Summary of PDF text extraction quality across document types |

### Design Decisions

| File | Description |
|---|---|
| [decisions/README.md](./decisions/README.md) | Index of Architecture Decision Records (ADRs) |
| [decisions/001-pymupdf-migration.md](./decisions/001-pymupdf-migration.md) | Why PyMuPDF replaced pypdf for text extraction |
| [decisions/002-openrouter-default-model-selection.md](./decisions/002-openrouter-default-model-selection.md) | Default model selection rationale |
| [decisions/cost.md](./decisions/cost.md) | API cost analysis and model cost comparisons |

### Investigations & Reports

These are time-stamped reference documents produced during development. They
are not intended to be kept current, but are preserved for context.

| Folder | Contents |
|---|---|
| [investigations/](./investigations/) | Dated investigation logs: retrieval issues, extraction bugs, threshold experiments |
| [reports/](./reports/) | Accuracy evaluation reports and demo recommendations |
| [saved_runs/](./saved_runs/) | Timestamped output snapshots from benchmark evaluation runs |

### Future Development

| File | Description |
|---|---|
| [future-development/phase-1-data-preparation.md](./future-development/phase-1-data-preparation.md) | Candidate improvements to the PDF ingestion stage |
| [future-development/phase-2-retrieval.md](./future-development/phase-2-retrieval.md) | Candidate improvements to retrieval and reranking |
| [future-development/phase-3-generation-cloud.md](./future-development/phase-3-generation-cloud.md) | Candidate improvements to the cloud generation pipeline |

---

## Known Issues & Maintenance Notes

- **`repo_structure.md`** contains stale data directory paths and a stale code tree. An updated version is planned.
- **`docs/archive/`** contains `LINTING_TODO.md` and `LINTING_CHANGELOG.md` from the previous team's Dec 2025 linting refactor work. The open items in `LINTING_TODO.md` have not been resolved; they should be triaged before being formally closed or discarded.
