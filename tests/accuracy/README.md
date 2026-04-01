# Accuracy Workflow

This folder contains two independent workflows for measuring StatsChat answer quality:

1. **Evaluation** (the main workflow): score StatsChat answers against a QA spreadsheet
2. **QA Generation** (optional): create a synthetic QA spreadsheet from KNBS documents

Most of the time you will only run the evaluation, using a curated set of questions that already exists.

### Files

- `evaluate_accuracy.py`: validates a QA spreadsheet and evaluates StatsChat answers against it
- `generate_qa_with_refs.py`: generates a synthetic QA spreadsheet from KNBS JSON conversions
- `StatsChat_QA_Template_2.xlsx`: Excel template used for the `QA_Data` sheet format
- `KNBS_QA_Authoring_Instructions.docx`: manual QA authoring guidance
- `StatsChat_Accuracy_Measurement.docx`: metric and process reference

---

## Part 1 — Evaluating StatsChat

This is the primary workflow. It takes an existing QA spreadsheet, sends each question to the StatsChat API, and scores the responses.

### Prerequisites

- A QA spreadsheet with a `QA_Data` sheet containing the required columns (see [Validation Rules](#validation-rules))
- The FAISS index at `data/db_langchain/` matching the corpus you want to test
- The StatsChat API running (local or cloud)

### Quick Start

The commands are the same for local and cloud — only the API URL changes.

**Step 1 — Validate the QA sheet** (no API needed):

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --validate-only
```

**Step 2 — Start the API** (pick one):

```bash
# Local (loads Mistral-7B — allow a few minutes for model loading)
uvicorn fast-api.main_api_local:app --host 127.0.0.1 --port 8000

# Cloud (requires API key — starts in seconds)
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001
```

For cloud mode, set the API key for the configured provider before starting:

| Provider | Environment variable |
|---|---|
| `openrouter` | `OPENROUTER_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `huggingface_inference` | `HF_TOKEN` |

The provider is read from `statschat/config/main.toml` under `[search] provider`.

**Step 3 — Run the evaluation** (in a new terminal):

```bash
# Against local API
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --host http://127.0.0.1:8000 \
  --content-type all \
  --timeout 420

# Against cloud API
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --host http://127.0.0.1:8001 \
  --content-type all \
  --timeout 420
```

The evaluator auto-detects local vs cloud from the API response. You can force a mode with `--api-mode local` or `--api-mode cloud`.

If `--api-mode cloud` is set and the required API key is missing, the evaluator will fail fast with an actionable error message.

**Smoke test** — evaluate only the first few rows:

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel "tests/accuracy/your_qa_sheet.xlsx" \
  --host http://127.0.0.1:8000 \
  --content-type all \
  --timeout 420 \
  --max-rows 3
```

### Evaluator Output

Each evaluation run creates a timestamped folder:

```
tests/accuracy/runs/
  cloud/
    2026-03-30_143012/
      accuracy_results.csv      # per-row metrics (same as before)
      run_report.md             # human-readable comparison report
      run_metadata.txt          # run configuration and summary stats
      qa_data_issues.csv        # validation issues (if any)
  local/
    2026-03-30_091500/
      ...
```

The `runs/` directory is gitignored.

**`run_report.md`** is the main output for reviewing StatsChat's performance. For each question it shows:

- Golden answer vs predicted answer side-by-side
- Expected documents vs returned documents
- Key metrics (EM, F1, semantic similarity, evidence match)
- StatsChat's reasoning and key phrases (cloud mode)
- Retrieved context chunks used for generation
- Expected source text from the QA sheet

**`run_metadata.txt`** records the run configuration: API mode, provider, model, QA file, thresholds, and summary accuracy stats.

**`accuracy_results.csv`** contains the full per-row results. Important columns:

| Column | Description |
|---|---|
| `predicted_answer` | The API response text |
| `exact_match` | 1 if normalised answer matches gold |
| `token_f1` | Token-overlap F1 score |
| `semantic_similarity` | Cosine similarity of sentence embeddings |
| `is_refusal` | Whether the response was a refusal |
| `is_correct` | Overall correctness judgement |
| `reference_urls` | All reference URLs returned (semicolon-joined) |
| `reference_doc_ids` | Normalised doc IDs from references (semicolon-joined) |
| `reference_pages` | Page numbers from references (semicolon-joined) |
| `evidence_page_match` | Whether any reference matched the expected evidence |
| `reasoning` | LLM reasoning text (cloud mode with debug) |
| `context_texts` | Retrieved context chunks sent to the LLM |
| `precision_at_k` | Precision@k from retrieval |
| `recall_at_k` | Recall@k from retrieval |
| `mrr` | Mean Reciprocal Rank |
| `ndcg` | Normalised Discounted Cumulative Gain |
| `error` | Error message if the API call failed |

---

## Part 2 — Generating QA Data (Optional)

Use this when you need to create a new QA spreadsheet rather than using an existing one.

### What It Does

`generate_qa_with_refs.py` creates a synthetic "silver" QA dataset from `data/json_conversions`:

- Samples JSON files and pages from KNBS conversions
- Prompts an LLM to generate `query_text`, `golden_answer`, and `source_text`
- Writes results into the `QA_Data` schema used by the manual Excel template
- Adds a `Generation_Metadata` sheet recording generation settings

This is a silver dataset, not a human-reviewed gold set. Use it as a starting point; review and curate rows before treating them as a benchmark.

### When To Use

- You need a new QA set aligned to a different corpus or index
- You want to expand coverage beyond manually authored questions
- You are bootstrapping initial test data for a new deployment

### Run Commands

```bash
python tests/accuracy/generate_qa_with_refs.py \
  --provider local \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --json-dir data/json_conversions \
  --template tests/accuracy/StatsChat_QA_Template_2.xlsx \
  --output tests/accuracy/StatsChat_QA_Auto.xlsx \
  --query-id-prefix Q \
  --strict-filters \
  --max-files 40 \
  --pages-per-doc 2 \
  --max-questions 60 \
  --min-text-length 220 \
  --max-new-tokens 128 \
  --seed 7
```

### Generator Parameters

| Flag | Purpose |
|---|---|
| `--max-files` | Maximum JSON documents to sample. `0` means all. |
| `--pages-per-doc` | Pages sampled from each document |
| `--max-questions` | Maximum accepted rows after filtering and deduplication |
| `--min-text-length` | Minimum page text length to consider |
| `--strict-filters` | Stricter filtering for grounded, less ambiguous QA |
| `--align-with-index` | Only use PDFs present in the current FAISS index |
| `--index-pkl` | FAISS metadata pickle for alignment (default: `data/db_langchain/index.pkl`) |

### Generator Output

- `tests/accuracy/StatsChat_QA_Auto.xlsx`

Sheets: `QA_Data`, `Instructions`, `Explanation`, `Generation_Metadata`

### Important

Generation and evaluation should use the same corpus conditions (same `--content-type`, same index). If they do not, variance will be high and results will be hard to interpret.

---

## Metric Definitions

### Accuracy

- `Answerable accuracy`: fraction of answerable rows marked correct
- `Unanswerable accuracy`: fraction of refusal rows marked correct
- `Overall accuracy`: correct rows divided by total evaluated rows

### Exact Match (EM)

`1` if normalized predicted answer equals normalized gold answer, else `0`.

### Token F1

Token-overlap F1 between normalized gold answer and predicted answer.

### Semantic Similarity

Cosine similarity between sentence-transformer embeddings of the gold and predicted answers.

### Numeric Match

Numeric answers are also checked with absolute and relative tolerance, including percent handling.

### Retrieval Metrics

Computed for both local and cloud modes using `similarity_search(...)` as a proxy with the shared FAISS index — not from the ranked list in the API response. This provides a consistent comparison across modes.

- `Precision@k`: relevant retrieved docs in top `k`, divided by `k`
- `Recall@k`: unique relevant docs found in top `k`, divided by total relevant docs
- `MRR`: reciprocal rank of the first relevant retrieved doc
- `nDCG`: discounted ranking quality relative to an ideal ranking

### Safe Response Rate

In the current implementation this is equal to `overall_accuracy`.

## Validation Rules

For answerable rows, the evaluator expects:

- `query_id`
- `query_text`
- `golden_answer`
- `relevant_doc_ids`
- `evidence_locations`
- `source_text`
- `should_answer`
- `Reviewers`

Additional checks include:

- query ID format, default `Q###`
- duplicate query IDs
- quoted `source_text`
- evidence page formatting
- evidence/doc alignment
- optional reviewer initials validation with `--require-reviewers`

For LLM-generated QA, reviewer initials are intentionally optional.

## Known Limitations

- `generate_qa_with_refs.py` creates silver data, not a reviewed benchmark.
- The generator currently uses local Hugging Face or OpenAI providers. It does **not** use RAGAS.
- Retrieval metrics do not use the exact ranked list returned by the API response. They use `similarity_search(...)` as a proxy, which provides a consistent comparison across local and cloud modes.
- Table-heavy questions can still be brittle even with strict filters.
- If generation and evaluation use different corpus modes or different index contents, measured accuracy can collapse for reasons unrelated to model quality.

## Practical Guidance

- Use `--content-type all` when QA was generated from `data/json_conversions` and evaluated against the full index.
- Rebuild the index before QA generation if corpus contents changed.
- Do not compare runs fairly unless corpus, index, thresholds, `k_docs`, and `k_contexts` were kept aligned.
- Treat the generated QA file as a starting point for testing, not as a final benchmark without review.
