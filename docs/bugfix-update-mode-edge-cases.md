# Bug Fixes: UPDATE Mode Edge Cases

**Date:** 2024-12-02  
**Branch:** `production_fitz`

## Problem

Running `pdf_runner.py` in UPDATE mode crashed when there were no new PDFs to process. This is the normal case when running regular scheduled updates between KNBS publication releases.

## Root Cause

Three scripts assumed there would always be content to process, causing crashes on empty data:

1. **`preprocess.py`** - Tried to create FAISS index from empty document list
2. **`preprocess.py`** - Tried to merge non-existent embeddings 
3. **`merge_database_files.py`** - Tried to load non-existent `url_dict.json`

## Fixes Applied

### 1. `statschat/embedding/preprocess.py` - `_embed_documents()`

```python
# Added check before embedding
if not self.chunks or len(self.chunks) == 0:
    print("No document chunks to embed. Skipping embedding step.")
    self.db = None
    return None
```

### 2. `statschat/embedding/preprocess.py` - `_merge_faiss_db()`

```python
# Added check before merging
if self.db is None:
    print("No new embeddings to merge. Skipping merge step.")
    return None
```

### 3. `statschat/pdf_processing/merge_database_files.py`

```python
# Added check before loading url_dict
if LATEST_URL_DICT_PATH.exists():
    # ... existing merge logic ...
else:
    print("No new url_dict.json to merge. Skipping URL dictionary update.")
```

## Testing

Verified by running UPDATE mode twice:
1. **First run:** Downloaded and processed 73 new PDFs ✅
2. **Second run:** Correctly detected no new PDFs and completed gracefully ✅

## Impact

- UPDATE mode now handles "no new content" scenario without crashing
- Scheduled/automated updates will complete successfully even when no new publications exist
