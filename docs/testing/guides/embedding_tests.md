# Embedding Tests (Maintained)

This guide documents the unit tests that protect the embedding pipeline: splitting JSON into chunks, marking latest publications, and persisting/merging vector-store artifacts.

> Historical reference guide: `docs/testing/guides/embeddings_tests.md` (kept for context; may be outdated).

## Where the Tests Live

- `tests/unit/embedding/test_json_splitter.py`
- `tests/unit/embedding/test_latest_matching.py`
- `tests/unit/embedding/test_preprocess_integration.py`
- `tests/unit/embedding/test_merge_faiss_db.py`
- Shared fixtures: `tests/unit/embedding/conftest.py`

## What These Tests Protect

- **Data integrity** when splitting JSON → section/page-level chunks (metadata should not silently disappear)
- **Latest-version logic** (fuzzy matching and latest-flag updates should not produce false positives)
- **Pipeline behavior** across modes (SETUP vs UPDATE) without depending on model downloads
- **FAISS merge behavior** (merging latest DB into original without corrupting state)

## Mocking & Isolation (Maintainership Notes)

The embedding pipeline normally involves heavyweight model inference and FAISS disk state.
The tests aim to validate *our logic and orchestration* while keeping runtime stable.

Typical techniques used:
- `tmp_path` for isolated directory layouts
- `monkeypatch` to replace embedding/model calls with deterministic stubs
- mocking FAISS load/save calls when validating merge behavior

If tests start downloading models or reaching the network:
- check `tests/unit/embedding/conftest.py` for offline/environment settings
- confirm new code paths are still exercised through a mocked embedding implementation

## How to Run

```bash
# All embedding tests
pytest tests/unit/embedding/ -v

# A single file
pytest tests/unit/embedding/test_latest_matching.py -v

# A single test
pytest tests/unit/embedding/test_merge_faiss_db.py::test_merge_faiss_db_merges_and_cleans -v
```

## When to Update These Tests

Update/add embedding tests when:
- chunk metadata schema changes (keys, required fields)
- latest matching heuristics/thresholds change
- FAISS persistence paths or directory layout changes
- pipeline mode behavior changes (SETUP/UPDATE semantics)

Aim for tests that are:
- deterministic
- isolated from real `data/` state
- explicit about “what” and “why” (docstrings), with implementation details kept minimal
