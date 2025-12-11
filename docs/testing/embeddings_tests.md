# Embedding Pipeline Tests

## Overview

This directory contains focused, fast tests for the StatsChat-KE embedding pipeline.

**Philosophy**: Keep tests simple, fast, and focused on real failure scenarios. No over-engineering.

--- 

## Running Tests

### Quick Reference
```bash
# All embedding tests (recommended)
pytest tests/unit/embedding/ -v

# Specific test file
pytest tests/unit/embedding/test_json_splitter.py -v

# Single test function
pytest tests/unit/embedding/test_json_splitter.py::test_json_splitter_preserves_metadata -v

# With debug output
pytest tests/unit/embedding/ -s -v

# Stop on first failure
pytest tests/unit/embedding/ -x

# Show coverage
pytest tests/unit/embedding/ --cov=statschat.embedding --cov-report=term-missing
```

---

## Test Coverage (5 Tests Total)

### 1. **JSON Splitter Tests** (`test_json_splitter.py`) - 5 tests
**Purpose**: Data integrity validation for splitting full JSONs into section-level JSONs.

- ✅ Metadata preservation across splits
- ✅ Latest flag filtering (`latest_only=True`)
- ✅ Short text filtering (len <= 5)
- ✅ Missing key handling
- ⚠️ **Critical**: This is where data corruption could occur

### 2. **Latest Matching Tests** (`test_latest_matching.py`) - 7 tests
**Purpose**: Fuzzy matching logic for identifying newer publication versions.

- ✅ Exact match detection (2024 → 2025 versions)
- ✅ No false positives (different publications)
- ✅ Threshold edge cases (75% similarity)
- ✅ Flag updates (latest=True → False)
- ⚠️ **Critical**: Wrong matches could delete current publications

### 3. **Integration Tests** (`test_preprocess_integration.py`) - 6 tests
**Purpose**: End-to-end pipeline flow with mocked embeddings.

- ✅ SETUP mode: JSON → split → embed → FAISS
- ✅ UPDATE mode: Directory path handling
- ✅ Document chunking with metadata
- ✅ Latest-only filtering
- ✅ Empty directory handling
- ⚠️ **Critical**: Full pipeline validation

## Mocking Strategy

### Why Mock Embeddings?
- **Original time**: 5-10 seconds per document
- **Mocked time**: <1 second for all tests
- **Model size**: 420MB download on first run

### How It Works
```python
# Mock returns fixed 768-dim vectors instantly
class MockEmbeddings:
    def embed_documents(self, texts):
        return [[0.1] * 768 for _ in texts]
```

---

## Test Execution Time

| Test File | Tests | Time |
|-----------|-------|------|
| `test_json_splitter.py` | 5 | ~1-2 sec |
| `test_latest_matching.py` | 7 | ~1 sec |
| `test_preprocess_integration.py` | 6 | ~3-4 sec |
| **TOTAL** | **18** | **~5-7 sec** |

## What We DON'T Test

Following our "keep it simple" philosophy, we intentionally skip:

- ❌ **LangChain internals** - External library, well-tested
- ❌ **FAISS indexing accuracy** - External library, not our code
- ❌ **HuggingFace model quality** - External model, not our concern
- ❌ **Actual embedding generation** - Too slow, external dependency
- ❌ **Network requests** - Not part of embedding pipeline
- ❌ **Edge cases that can't happen** - Our JSONs are pre-validated

## What We DO Test

Focused on **real failure scenarios**:

- ✅ **Data integrity** - Metadata must not be lost during splits
- ✅ **Mode switching** - SETUP vs UPDATE use correct paths
- ✅ **Filtering logic** - latest_only and text length thresholds
- ✅ **Fuzzy matching** - Publication version detection
- ✅ **Error handling** - Graceful degradation on missing data

## Dependencies

Tests use standard pytest fixtures:
- `tmp_path` - Isolated temporary directories
- `monkeypatch` - Mock external dependencies
- `caplog` - Capture log output

Additional test dependencies:
- `pytest>=7.0`
- `rapidfuzz` (for fuzzy matching tests)

## Environment Setup

The `conftest.py` automatically sets:
- `TRANSFORMERS_OFFLINE=1` - Prevents model downloads
- `HF_DATASETS_OFFLINE=1` - Prevents dataset downloads  
- `TQDM_DISABLE=1` - Disables progress bars

## Common Issues

### "FAISS not found" error
```bash
pip install faiss-cpu
```

### "HuggingFace model download" during tests
- Check `conftest.py` is being loaded
- Verify `TRANSFORMERS_OFFLINE=1` is set

### Tests hang on embedding step
- Mocking may not be applied correctly
- Check `mock_embeddings` fixture is used

## Test Data Structure

All tests use realistic JSON structures matching KNBS publications:

```json
{
    "id": "test_pub_001",
    "title": "Test Publication",
    "release_date": "2025-01-01",
    "latest": true,
    "content": [
        {
            "page_number": 1,
            "page_url": "https://...",
            "page_text": "Page content..."
        }
    ]
}
```

## Future Test Additions

If needed, consider adding:
- ⏸️ **FAISS merge validation** - Check no data loss during UPDATE mode merge
- ⏸️ **Large dataset stress test** - Performance with 100+ publications
- ⏸️ **Concurrent access** - Multiple processes updating vector store

## Contributing

When adding new tests:
1. Keep them **fast** (<5 seconds each)
2. Use **tmp_path** for file isolation
3. **Mock external services** (embeddings, network)
4. Test **real failure scenarios** only
5. Add **clear docstrings** explaining why the test exists

## Questions?

See: `docs/development_and_testing.md` for general testing philosophy.
