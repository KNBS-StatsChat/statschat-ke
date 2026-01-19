# E2E Tests

End-to-end (E2E) tests validate system behavior across components (API + retrieval + generation) from an external user perspective.

## Current Status

The `tests/e2e/` directory currently contains a placeholder only (no runnable E2E tests).

## Intended Scope (When Added)

E2E tests should answer questions like:
- “Can a user query the API and receive a well-formed response?”
- “Do deployments fail safely when required resources are missing?”

## Maintainership Notes

Because StatsChat-KE depends on stateful artifacts (PDFs/JSON/FAISS DBs), E2E tests should:
- use small, controlled fixtures under `tests/test_data/`
- avoid relying on the full `data/` directory
- clearly document any required environment configuration

## How to Run

When E2E tests exist:

```bash
pytest tests/e2e/ -v
```
