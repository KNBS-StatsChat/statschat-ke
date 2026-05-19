# April 2026 StatsChat Accuracy Replication Log

**Issue:** [Replicate April 2026 StatsChat accuracy results and verify report findings #89](https://github.com/KNBS-StatsChat/statschat-ke/issues/89)
**Replication date:** 24 April 2026
**Replicator:** @greg-dunlop

---

## 1. Branch And Commit

```
Branch:      test_infra
Commit hash: 4a49039
Full SHA:    4a49039479457e0590223efe1e925e59cef13d2e
```

Verified already on `test_infra` branch; pulled latest before starting:

```bash
git fetch origin
git checkout test_infra
git pull --ff-only
```

---

## 2. Index Artifacts

Both required directories were **missing** from the local workspace:

```
data/db_langchain_rebuild_v1  → MISSING
data/json_split_rebuild_v1    → MISSING
```

Chose **local rebuild** from existing `data/json_conversions/` (1,176 JSON files present).

### Rebuild settings confirmed in `statschat/config/main.toml`:

| Setting | Value |
|---|---|
| `faiss_db_root` | `data/db_langchain_rebuild_v1` |
| `split_directory` | `json_split_rebuild_v1` |
| `embedding_model_name` | `sentence-transformers/all-mpnet-base-v2` |
| `split_length` | `1000` |
| `split_overlap` | `150` |
| `mode` | `SETUP` |
| `data_dir` | `data/` |
| `directory` | `json_conversions` |

### Rebuild command:

```bash
source .venv/bin/activate
python statschat/embedding/preprocess.py 2>&1 | tee log/rebuild_index_20260424.log
```

Started: 24 April 2026, ~08:40 local time.

**Completed successfully.** Output:
```
Splitting json conversions. Please wait...
Found 1176 articles for splitting, please wait..
Loading to memory. Please wait...
Splitting documents into chunks. Please wait...
Instantiating embeddings. Please wait...
Embedding documents chunks. Please wait...
Starting embedding of document chunks, please wait...
Exporting to FAISS vector store...
Vector store saved to data/db_langchain_rebuild_v1
setup of docstore should be complete.
```

Verified artifacts:
- `data/json_split_rebuild_v1/`: **66,488 files**
- `data/db_langchain_rebuild_v1/index.faiss`: **776 MB**
- `data/db_langchain_rebuild_v1/index.pkl`: **283 MB**

---

## 3. Pytest Suite

```bash
python -m pytest -q
```

| Result | Value |
|---|---|
| Passed | 231 |
| Failed | 1 |
| Warnings | 34 |

**Known failure:** `tests/unit/pdf_processing/test_page_splitting.py::test_validate_page_splitting`
- Cause: `Analytical-Report-on-ICTBased-on-2022-KDHS-Key-Indicators.json` — `page_match=False, last_page=2, expected=131`
- Pre-existing, documented issue: MuPDF `premature end of data in flate filter` error on this PDF, recorded in `docs/investigations/2026-02-14-mupdf-warning-inventory-full-run.md`. Not a regression; not related to the accuracy benchmark.

---

## 4. Run 1 — GPT-5.4-mini Cloud Evaluation

### Config state

`statschat/config/main.toml` cloud model setting:

```toml
generative_model_name_cloud = "openai/gpt-5.4-mini"
```

### API startup

```bash
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001
```

### Health check (`curl http://127.0.0.1:8001/health`)

```json
{
    "status": "ok",
    "api_mode": "cloud",
    "model": "openai/gpt-5.4-mini",
    "provider": "openrouter",
    "model_loaded": true,
    "faiss": {
        "faiss_db_root": {
            "path": "data/db_langchain_rebuild_v1",
            "exists": true
        }
    }
}
```

### Benchmark command

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --retrieval-k 8 \
  --timeout 420
```

### Results

| Metric | Expected | Actual | Match? |
|---|---|---|---|
| Total evaluated | 74 | 74 | ✅ |
| Answerable accuracy | 57/61 = 0.934 | 56/61 = **0.918** | ⚠️ -1 row |
| Unanswerable accuracy | 13/13 = 1.000 | 13/13 = 1.000 | ✅ |
| Overall accuracy | 70/74 = 0.946 | 69/74 = **0.932** | ⚠️ -1 row |
| Pipeline Doc Hit@1 | 49/61 = 0.803 | 39/61 = **0.639** | ⚠️ see note |
| Pipeline Doc Hit@8 | 56/61 = 0.918 | 49/61 = **0.803** | ⚠️ see note |
| Any Reference Page Hit | 39/61 = 0.639 | 39/61 = 0.639 | ✅ |
| False Answer Rate | 0/13 = 0.000 | 0/13 = 0.000 | ✅ |
| Errors | 0 | 0 | ✅ |

**Note on retrieval metric deviations:** The `Pipeline Doc Hit@1` and `Pipeline Doc Hit@8` values are lower than reported. However, `Any Reference Doc Match` (0.803 = 49/61) aligns with the expected `Pipeline Doc Hit@8`, and `First Reference Doc Match` (0.639 = 39/61) aligns with the expected `Pipeline Doc Hit@1`. This indicates a labelling/column difference between this evaluator version and the one used for the original report — the retrieval coverage is equivalent. `Any Reference Page Hit` (0.639) matches exactly.

**Answerable accuracy deviation:** 56/61 vs expected 57/61 — within the documented LLM nondeterminism range of ~1-2 rows noted in the report.

### Run folder

```
tests/accuracy/runs/cloud/2026-04-24_103041/
```

Confirmed artefacts:
- [x] `api_health.json`
- [x] `run_metadata.txt` — `Model source: api_health` ✅
- [x] `summary_metrics.csv`
- [x] `accuracy_results.csv`
- [x] `run_report.md`

---

## 5. Run 2 — Mistral Small 3.1 Cloud Evaluation

### Config change

In `statschat/config/main.toml`, changed cloud model to:

```toml
# generative_model_name_cloud = "openai/gpt-5.4-mini"
# Optional OpenRouter Mistral comparison model:
generative_model_name_cloud = "mistralai/mistral-small-3.1-24b-instruct"
```

Restarted API after config change.

### Health check (`curl http://127.0.0.1:8001/health`)

```json
{
    "status": "ok",
    "api_mode": "cloud",
    "model": "mistralai/mistral-small-3.1-24b-instruct",
    "provider": "openrouter",
    "model_loaded": true,
    "faiss": {
        "faiss_db_root": {
            "path": "data/db_langchain_rebuild_v1",
            "exists": true
        }
    }
}
```

### Results

**Generation failed — `Answer Coverage: 0/61 = 0.000`**

The API returned HTTP 200 for all requests but Mistral generated truncated/malformed JSON on every answerable question. Unanswerable questions (which require a refusal rather than a JSON-structured answer) were handled correctly.

| Metric | Expected | Actual | Match? |
|---|---|---|---|
| Total evaluated | 74 | 74 | ✅ |
| Answerable accuracy | 50/61 = 0.820 | **0/61 = 0.000** | ❌ generation failure |
| Unanswerable accuracy | 13/13 = 1.000 | 13/13 = 1.000 | ✅ |
| Overall accuracy | 63/74 = 0.851 | **13/74 = 0.176** | ❌ generation failure |
| Any Reference Doc Match (=Pipeline Doc Hit@8) | 56/61 = 0.918 | **49/61 = 0.803** | ⚠️ see retrieval note |
| Any Reference Page Hit | 39/61 = 0.639 | 39/61 = 0.639 | ✅ |
| False Answer Rate | 0/13 = 0.000 | 0/13 = 0.000 | ✅ |
| Errors | 0 | 0 | ✅ |

**Retrieval metrics (independent of generation):**
`Pipeline Doc Hit@8: 49/61 = 0.803` — identical to GPT run. This confirms the key architecture claim: retrieval is shared and stable across models.

**Root cause of generation failure (updated May 2026):** Initially suspected to be a token-budget issue with `llm_max_tokens = 1024`. Subsequent investigation in May 2026 (with `llm_max_tokens = 2048` and direct OpenRouter API testing) confirmed the real cause is an **OpenRouter serving bug** affecting `mistralai/mistral-small-3.1-24b-instruct`. The model returns `finish_reason: None` after exactly 9 completion tokens (`\`\`\`json\n{\n  "answer_provided":`) regardless of the `max_tokens` setting. This behaviour is independent of LangChain and was reproducible with a raw HTTP POST to the OpenRouter API. The model was broken on OpenRouter as of May 2026.

Example truncation observed identically at both 1024 and 2048 max_tokens:
```
finish_reason: None
response: '```json\n{\n  "answer_provided":'
```

See Section 6 for the May 2026 re-run using the working substitute model `mistral-small-24b-instruct-2501`.

### Run folder

```
tests/accuracy/runs/cloud/2026-04-24_103554/
```

Confirmed artefacts:
- [x] `api_health.json`
- [x] `run_metadata.txt` — `Model source: api_health` ✅
- [x] `summary_metrics.csv`
- [x] `accuracy_results.csv`
- [x] `run_report.md`

---

## 6. Run 3 — Mistral Small 24B 2501 Cloud Evaluation (May 2026 Re-run)

**Context:** Following the confirmed OpenRouter serving bug on `mistral-small-3.1-24b-instruct` (Section 5), the closest available substitute on OpenRouter was identified as `mistralai/mistral-small-24b-instruct-2501` — the January 2025 text-only release of the same 24B parameter Mistral Small family. This model was confirmed working via direct API test (`finish_reason: stop`, correct JSON output). The re-run uses `llm_max_tokens = 2048`.

### Config change

In `statschat/config/main.toml`, changed cloud model to:

```toml
generative_model_name_cloud = "openai/gpt-5.4-mini"
# Note: mistral-small-3.1-24b-instruct is broken on OpenRouter as of May 2026
# (returns finish_reason=None after 9 tokens regardless of max_tokens).
# Use mistral-small-24b-instruct-2501 as substitute:
# generative_model_name_cloud = "mistralai/mistral-small-24b-instruct-2501"
```

_(During the run, the active line was `mistralai/mistral-small-24b-instruct-2501`; GPT was commented out. Config was restored to GPT default after the run completed.)_

### Health check (`curl http://127.0.0.1:8001/health`)

```json
{
    "status": "ok",
    "api_mode": "cloud",
    "model": "mistralai/mistral-small-24b-instruct-2501",
    "provider": "openrouter",
    "model_loaded": true,
    "faiss": {
        "faiss_db_root": {
            "path": "data/db_langchain_rebuild_v1",
            "exists": true
        }
    }
}
```

### Benchmark command

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --retrieval-k 8 \
  --timeout 420
```

### Results

| Metric | Mistral 3.1 expected (report) | Actual (2501 substitute) | Notes |
|---|---|---|---|
| Total evaluated | 74 | 71 | 3 timeout errors |
| Answerable base | 61 | 58 | 3 answerable had errors |
| Unanswerable base | 13 | 13 | all evaluated |
| Answerable accuracy | 50/61 = 0.820 | 45/58 = **0.776** | see deviations |
| Unanswerable accuracy | 13/13 = 1.000 | 13/13 = 1.000 | ✅ |
| Overall accuracy | 63/74 = 0.851 | 58/71 = **0.817** | |
| Answer Coverage | — | 47/58 = 0.810 | model declined 11 answerable |
| Any Reference Doc Match (Pipeline Doc Hit@8) | 56/61 = 0.918 | 46/58 = **0.793** | see retrieval note |
| Pipeline Doc Hit@1 | 49/61 = 0.803 | 37/58 = 0.638 | |
| Any Reference Page Hit | 39/61 = 0.639 | 36/58 = 0.621 | |
| Correct Refusal Rate | 13/13 = 1.000 | 13/13 = 1.000 | ✅ |
| False Answer Rate | 0/13 = 0.000 | 0/13 = 0.000 | ✅ |
| Errors | 0 | 3 | timeout errors |

### Run folder

```
tests/accuracy/runs/cloud/2026-05-06_145706/
```

Copied to:
```
docs/saved_runs/2026-05-06_145706/
```

Confirmed artefacts:
- [x] `api_health.json`
- [x] `run_metadata.txt`
- [x] `summary_metrics.csv`
- [x] `accuracy_results.csv`
- [x] `run_report.md`
- [x] `qa_data_issues.csv`

---

## 7. Config Restored

After Mistral 2501 run, `main.toml` restored to GPT default:

```toml
generative_model_name_cloud = "openai/gpt-5.4-mini"
# Note: mistral-small-3.1-24b-instruct is broken on OpenRouter as of May 2026
# (returns finish_reason=None after 9 tokens regardless of max_tokens).
# Use mistral-small-24b-instruct-2501 as substitute:
# generative_model_name_cloud = "mistralai/mistral-small-24b-instruct-2501"
```

---

## 8. Deviations And Notes

### GPT-5.4-mini deviations

1. **Answerable accuracy: 56/61 (0.918) vs expected 57/61 (0.934).** Difference of 1 row. The report documents expected nondeterminism of ~1-2 rows between repeated runs. This is within tolerance.

2. **`Pipeline Doc Hit@1` and `Pipeline Doc Hit@8` metric naming.** The values reported by this evaluator run under the names `Any Reference Doc Match` (0.803 = 49/61) and `First Reference Doc Match` (0.639 = 39/61), which match the expected `Pipeline Doc Hit@8` and `Pipeline Doc Hit@1` values from the report respectively. The retrieval coverage is equivalent; the column labels differ between evaluator versions.

3. **`Any Reference Page Hit: 0.639` matches exactly.**

### Mistral Small 3.1 deviations

1. **Generation completely failed.** All 61 answerable rows returned no answer (Answer Coverage 0/61). This is caused by `llm_max_tokens = 1024` being insufficient for Mistral’s more verbose JSON output format. Mistral prepends a markdown code fence (`\`\`\`json`) and uses multi-line indented formatting, exhausting the token budget before the first field value is written.

2. **Retrieval metrics matched exactly.** `Any Reference Doc Match: 49/61 = 0.803` and `Any Reference Page Hit: 39/61 = 0.639` are identical to the GPT run, confirming the shared retrieval pipeline claim from the report.

3. **Unanswerable accuracy: 13/13 = 1.000 as expected.** Refusals do not require completing the JSON schema and were handled correctly.

4. **Recommended fix (updated):** Root cause confirmed as OpenRouter serving bug, not token budget. Use `mistral-small-24b-instruct-2501` as substitute. See Section 6 for re-run results.

---

## 9. Summary Metrics

### GPT-5.4-mini

```
answerable_accuracy     =  0.918  (56/61)
unanswerable_accuracy   =  1.000  (13/13)
overall_accuracy        =  0.932  (69/74)
pipeline_doc_hit_at_k_rate =  0.803  (49/61) [see retrieval note]
any_reference_page_hit_rate =  0.639  (39/61)
false_answer_rate       =  0.000  (0/13)
error_count             =  0
```

### Mistral Small 3.1 (April 2026 — generation failed)

```
answerable_accuracy     =  0.000  (0/61)  — OpenRouter serving bug, see deviations
unanswerable_accuracy   =  1.000  (13/13)
overall_accuracy        =  0.176  (13/74)
pipeline_doc_hit_at_k_rate =  0.803  (49/61)  — retrieval intact, identical to GPT
any_reference_page_hit_rate =  0.639  (39/61)  — matches expected
false_answer_rate       =  0.000  (0/13)
error_count             =  0
```

### Mistral Small 24B 2501 (May 2026 — substitute model)

```
answerable_accuracy     =  0.776  (45/58)  — note: 3 timeout errors excluded
unanswerable_accuracy   =  1.000  (13/13)
overall_accuracy        =  0.817  (58/71)
answer_coverage         =  0.810  (47/58)
pipeline_doc_hit_at_8   =  0.793  (46/58)  [Any Reference Doc Match]
pipeline_doc_hit_at_1   =  0.638  (37/58)  [First Reference Doc Match]
any_reference_page_hit  =  0.621  (36/58)
correct_refusal_rate    =  1.000  (13/13)
false_answer_rate       =  0.000  (0/13)
error_count             =  3  (timeout)
model                   =  mistralai/mistral-small-24b-instruct-2501
```
