# context for AI Agents

## Project Overview
**StatsChat-KE** is an experimental RAG (Retrieval Augmented Generation) system designed to answer questions based on statistical reports from the Kenya National Bureau of Statistics (KNBS). It scrapes PDFs, creates embeddings, and uses an LLM to synthesis answers.

## Architecture Guidelines
- **Language**: Python 3.10+
- **Framework**: LangChain, FastAPI (backend)
- **Vector Store**: FAISS
- **Data Flow**: `Ingestion (PDF)` -> `Transformation (JSON)` -> `Embedding (Vector Store)` -> `Retrieval (RAG)`

## Development Standards
1.  **Code Style**: Follow PEP 8. Use extensive type hinting (`typing` module) for all function signatures.
2.  **Linting**: This project uses `pre-commit` hooks. Ensure code passes linting before suggesting commits.
3.  **Paths**: Always use `pathlib` for file system operations. The project relies heavily on specific directory structures in `data/`.
4.  **Async**: The API (`fast-api/`) is asynchronous. Use `async/await` patterns where appropriate for I/O bound tasks.

## Key Directories
- `statschat/`: Core application logic (the python package).
- `data/`: Local storage for PDFs, JSONs, and Vector DBs. **Note**: This folder is heavily state-dependent (`SETUP` vs `UPDATE` modes).
- `tests/`: Pytest suite. Split into `unit`, `integration`, and `e2e`.
- `docs/`: Comprehensive detailed documentation. Refer to `docs/architecture/` for pipeline details.

## Testing Strategy
- **Runner**: `pytest`
- **Scope**: Focus on critical data handling (PDF text extraction correctness) and RAG pipeline components.
- **Data**: Uses `tests/test_data/` for fixtures. Do not rely on the full 2GB+ `data/` folder for unit tests.

## Critical Constraints
- **Experimental Status**: The project is a prototype. Stability is strictly "Experimental".
- **LLM Safety**: Be aware that generation components may hallucinate.
- **Configuration**: The system behavior is heavily driven by `statschat/config/main.toml`. Always check the `mode` ("SETUP" vs "UPDATE") before assuming data flow paths.
