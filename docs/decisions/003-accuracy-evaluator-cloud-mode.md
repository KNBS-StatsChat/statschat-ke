# ADR-003: Accuracy Evaluator — Cloud Mode Support and Multi-Reference Capture

**Status:** Accepted
**Date:** 2026-03-25

## Context

The accuracy evaluation system (`tests/accuracy/evaluate_accuracy.py`) was built to
measure StatsChat answer quality by feeding questions into the `/search` API and
comparing outputs against golden answers and source documents. It was originally
designed for **local mode only** — where StatsChat runs a local Mistral-7B model with
a local FAISS vector store.

StatsChat also has a **cloud mode** (`fast-api/main_api_cloud.py`) that uses remote LLM
providers (OpenRouter, OpenAI, or HuggingFace Inference) via the `Inquirer` class. As
the project moves towards cloud deployment, we need the same evaluation tooling to work
against both API modes, producing comparable metrics from the same QA test data.

### Pre-existing cloud awareness

The evaluator already contained partial cloud support, added during initial development:

- `--api-mode` CLI flag accepting `auto`, `local`, or `cloud`
- `detect_api_mode()` auto-detecting the API type by checking if `references` is a
  string (local) or list (cloud)
- `extract_reference_details()` handling both reference formats

However, two key limitations remained:

1. **Retrieval metrics were disabled for cloud mode.** The guard at the retrieval
   metrics block (`api_mode_used == "local"`) meant cloud evaluations skipped Precision@k,
   Recall@k, MRR, and nDCG entirely. Since both modes share the **identical FAISS index
   and embedding model** (`sentence-transformers/all-mpnet-base-v2`), there was no
   technical reason for this restriction.

2. **Only the first API reference was captured.** `extract_reference_details()` broke
   after finding the first reference with a valid `page_url`, discarding any additional
   documents returned by the cloud API. This meant the evaluation could not assess
   whether StatsChat returned all the relevant source documents.

### API response differences

| Aspect | Local API | Cloud API |
|--------|-----------|-----------|
| `references` type | `str` (single URL) | `list[dict]` (each with `page_url`) |
| Extra fields | `context_from`, `context_reference`, `relevant_publication_one/two` | `debug_response` (optional) |
| Reference count | Always 0 or 1 | Typically 1–5 |

Both APIs accept the same request parameters (`q`, `content_type`, `debug`) and return
the same core fields (`question`, `content_type`, `answer`, `references`).

## Decision

Adapt the evaluator to work for both local and cloud modes as a single unified system.

### Changes made

#### 1. Multi-reference capture (`extract_reference_details`)

**Before:** Extracted only the first reference (URL, doc ID, page number) from the API
response. Cloud mode's multiple references were discarded.

**After:** Collects **all** references returned by the API. Returns semicolon-joined
strings for URLs, doc IDs, and pages — consistent with the existing `retrieved_doc_ids`
field convention.

| Field | Before (type) | After (type) | Format |
|-------|---------------|--------------|--------|
| `reference_url` | `Optional[str]` | `reference_urls: Optional[str]` | Semicolon-joined URLs |
| `reference_doc_id` | `Optional[str]` | `reference_doc_ids: Optional[str]` | Semicolon-joined normalised doc IDs |
| `reference_page` | `Optional[int]` | `reference_pages: Optional[str]` | Semicolon-joined page numbers |
| `reference_count` | `Optional[int]` | `Optional[int]` | Unchanged |

For local mode, these fields contain a single value (backward compatible). For cloud
mode, they contain all returned documents.

**CSV column rename impact:** Any downstream scripts consuming
`accuracy_results.csv` that reference `reference_url`, `reference_doc_id`, or
`reference_page` will need updating to the plural names.

#### 2. Evidence page match across all references

**Before:** Checked only the first returned reference page against golden evidence
locations.

**After:** Iterates all returned (doc_id, page) pairs. `evidence_page_match` is `True`
if **any** returned reference page matches the golden evidence pages for that document.

#### 3. Retrieval metrics enabled for cloud mode

**Before:** The guard `api_mode_used == "local"` blocked retrieval metric computation
for cloud, setting `retrieval_metric_source = "disabled_non_local_api"`.

**After:** Changed to `api_mode_used in {"local", "cloud"}`. Both modes use the same
FAISS index and embedding model, so `similarity_search()` produces valid retrieval
rankings regardless of which API served the answer. The retrieval metrics measure the
quality of the vector store — they are independent of the generation layer.

#### 4. Cloud API key pre-flight validation

Added `_check_cloud_api_key()` which runs before sending any queries when
`--api-mode cloud` is set. It:

- Reads the `provider` field from `statschat/config/main.toml`
- Checks for the matching environment variable:
  - `openrouter` → `OPENROUTER_API_KEY`
  - `openai` → `OPENAI_API_KEY`
  - `huggingface_inference` → `HF_TOKEN`
- Exits with code 1 and an actionable error message if the key is missing

This prevents a full evaluation run from starting and failing partway through due to
authentication errors.

#### 5. `normalize_doc_id` empty string guard

**Before:** Could return an empty string for malformed URLs (e.g. `"http://example.com"`
with no path component), which would break retrieval metric comparisons.

**After:** Falls back to the original (lowered, stripped) input value if URL processing
produces an empty string.

### Files changed

| File | Changes |
|------|---------|
| `tests/accuracy/evaluate_accuracy.py` | Multi-reference extraction, EvaluationResult field renames, evidence match across all refs, retrieval guard relaxed, API key validation, normalize_doc_id fix |
| `tests/accuracy/README.md` | Added cloud evaluation run commands (section 4b), updated output column names, updated retrieval metric description |

## Rationale

### Why enable retrieval metrics for cloud?

Both modes share the identical FAISS index built from the same embeddings. The
`similarity_search()` function queries this index directly — it does not depend on
which API served the answer or which LLM generated it. Retrieval quality is a property
of the vector store, not the generation layer. Disabling these metrics for cloud mode
would leave a gap in the evaluation that has no technical justification.

### Why capture all references?

The purpose of the evaluation system is to assess whether StatsChat returns correct
answers **and relevant source documents**. Capturing only the first reference discards
information that is essential to this goal. The cloud API can return multiple source
documents, and the evaluation should compare all of them against the golden
`relevant_doc_ids`.

### Why semicolon-joined strings instead of lists?

The CSV output format uses one row per question. Semicolon-joined strings are already
the convention used by `retrieved_doc_ids` in the same output. Using the same pattern
keeps the output consistent and avoids introducing nested data structures into a flat
CSV.

### Why fail-fast on missing API keys?

A 190-row evaluation run that fails at row 1 due to a missing API key wastes no time.
A run that fails at row 50 after half an hour wastes significant time. The pre-flight
check prevents this.

## Consequences

### Positive

- The evaluator now works for both local and cloud modes using the same QA data,
  same metrics, and same output format.
- All documents returned by StatsChat are captured and compared against golden
  references.
- Cloud evaluation includes retrieval metrics (Precision@k, Recall@k, MRR, nDCG),
  enabling direct comparison with local mode.
- Missing API keys are caught immediately with an actionable error.

### Trade-offs

- CSV column names changed (`reference_url` → `reference_urls`, etc.). Any existing
  analysis scripts referencing the old names will need a one-line update.
- The `similarity_search()` import from `statschat.generative.local_llm` is still
  required even for cloud-only evaluation, because retrieval metrics use it directly.
  This means the FAISS index must be available locally regardless of API mode.

### Not in scope

- **QA generator cloud adaptation:** `generate_qa_with_refs.py` already supports
  `--provider openai` for QA generation. Cloud `Inquirer`-based generation was
  deferred until the provider strategy stabilises.
- **CI integration:** Evaluation remains local tooling. Future work could run it in
  GitHub Actions with a cloud API endpoint.
- **Multi-reference retrieval metrics:** The retrieval metrics still use the
  `similarity_search()` proxy, not the actual references returned by the API.
  A future enhancement could compare API-returned references directly against
  golden doc IDs.

## Verification

Tested end-to-end against the cloud API (OpenRouter, `mistralai/mistral-small-3.1-24b-instruct:free`):

1. **Validate-only mode:** Ran successfully, found 72 data quality issues in
   template QA data (expected — template uses placeholder doc IDs).
2. **Cloud evaluation (3 rows):** All metrics populated, `api_mode: cloud`,
   `retrieval_metric_source: local_similarity_search_proxy`.
3. **Multi-reference capture confirmed:** Q001 returned 2 references with
   `reference_doc_ids: 2020-kenya-facts-figures;2025-facts-and-figures` and
   `reference_pages: 33;45`.
4. **API key fail-fast:** Without `OPENROUTER_API_KEY`, evaluator exited with
   code 1 and message: `"Cloud mode requires the OPENROUTER_API_KEY environment
   variable (provider=openrouter). Set it and retry."`
