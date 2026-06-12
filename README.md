# KNBS StatsChat

[![Stability](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental)
[![Shared under the MIT License](https://img.shields.io/badge/license-MIT-green)](https://github.com/datasciencecampus/Statschat/blob/main/LICENSE)
[![Mac-OS compatible](https://shields.io/badge/MacOS--9cf?logo=Apple&style=social)]()

> [!WARNING]
> StatsChat-KE is under active development and not yet in production. It uses Large Language Models (LLMs) which can produce inaccurate, incomplete, or hallucinated answers. All responses should be verified against the cited source documents before being relied upon. The system depends on external LLM APIs which may change or become unavailable.

## What it is

StatsChat-KE is a retrieval-augmented generation (RAG) tool that helps users find answers in [KNBS statistical publications](https://www.knbs.or.ke/all-reports/). Users ask a natural-language question, then the system retrieves the most relevant pages from the indexed corpus and uses an LLM to produce a grounded answer with source references.

Its primary use case is speeding up the process of searching through PDFs — helping staff locate the right document, page, and extract faster, while they continue to verify the cited source before relying on the answer.

<img width="1661" height="580" alt="System architecture overview" src="https://github.com/user-attachments/assets/34eb5fbd-0965-48f8-acd3-bcc7ee945de2" />

## Quick start

1. **Set up your environment** — install dependencies and configure API credentials: [docs/guides/setup_guide.md](docs/guides/setup_guide.md) · [docs/guides/environment_setup.md](docs/guides/environment_setup.md)
2. **Build the vector store** — run `python statschat/pdf_runner.py` with `mode = "SETUP"` in `statschat/config/main.toml`: [docs/guides/OPERATING_MANUAL.md](docs/guides/OPERATING_MANUAL.md)
3. **Start the API** — `uvicorn fast-api.main_api_cloud:app --reload` then open `http://127.0.0.1:8000/docs`
4. **Ask a question** — `http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023`

> [!TIP]
> To use a different model locally without changing the shared config, set `STATSCHAT_GENERATIVE_MODEL` in your `.env` file (e.g. `STATSCHAT_GENERATIVE_MODEL=mistralai/mistral-nemo`). Remove it to revert to the repo default.

> [!NOTE]
> Running the local LLM (`main_api_local.py` or `local_llm.py`) requires ~16 GB RAM and 3–5 minutes per query. The cloud API is faster and recommended for most use.

## Documentation

| Document | Description |
|---|---|
| [docs/SPECIFICATION.md](docs/SPECIFICATION.md) | What the project is, its current status, known limitations, and recommended next steps |
| [docs/guides/setup_guide.md](docs/guides/setup_guide.md) | Environment and dependency installation |
| [docs/guides/environment_setup.md](docs/guides/environment_setup.md) | API keys and `.env` configuration |
| [docs/guides/OPERATING_MANUAL.md](docs/guides/OPERATING_MANUAL.md) | Running the data pipeline and API; troubleshooting |
| [docs/reference/api-reference.md](docs/reference/api-reference.md) | HTTP endpoint reference (`/health`, `/search`, `/feedback`) |
| [docs/reference/config_guide.md](docs/reference/config_guide.md) | All `main.toml` configuration options and current values |
| [docs/architecture/README.md](docs/architecture/README.md) | Technical pipeline architecture |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Branching, PR workflow, and code quality standards |
| [docs/README.md](docs/README.md) | Full documentation index |

## License

The code, unless otherwise stated, is released under the [MIT License](LICENSE).
