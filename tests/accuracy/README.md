# Accuracy Workflow

This folder contains the StatsChat accuracy workflow:

- `generate_qa_with_refs.py`: generates a synthetic QA spreadsheet from KNBS JSON conversions
- `evaluate_accuracy.py`: validates a QA spreadsheet and evaluates StatsChat answers against it
- `StatsChat_QA_Template_2.xlsx`: Excel template used for the `QA_Data` sheet format
- `KNBS_QA_Authoring_Instructions.docx`: manual QA authoring guidance
- `StatsChat_Accuracy_Measurement.docx`: metric and process reference

This is operational test tooling. The most useful documentation belongs in this folder next to the scripts and template. Broader pipeline architecture still belongs under `docs/`.

## What The Scripts Do

### `generate_qa_with_refs.py`

This script creates a synthetic "silver" QA dataset from `data/json_conversions`.

What it does:

- samples JSON files and pages from KNBS conversions
- prompts an LLM to generate:
  - `query_text`
  - `golden_answer`
  - `source_text`
- writes the results into the same `QA_Data` schema used by the manual Excel template
- copies the `Instructions` and `Explanation` sheets from the template
- adds a `Generation_Metadata` sheet recording generation settings

Important behavior:

- it does **not** compute accuracy metrics
- it uses strict grounding filters by default
- it can restrict generation to PDFs that are present in the current FAISS index via `--align-with-index`
- for local generation, it loads the Hugging Face model once and reuses it for all generated rows

This is a silver dataset, not a human-reviewed gold set.

### `evaluate_accuracy.py`

This script validates a QA sheet and optionally calls the StatsChat API to score responses.

What it does:

- checks that `QA_Data` has the required columns
- validates row quality and authoring rules
- calls `/search` for each question unless `--validate-only` is used
- compares predicted answers against `golden_answer`
- writes per-row results to CSV
- optionally writes an Excel file with answers and metrics merged back into `QA_Data`

Important behavior:

- it can run validation only, without calling the API
- it checks generation/evaluation condition alignment if the sheet contains `Generation_Metadata`
- retrieval metrics are computed only for local mode and use `statschat.generative.local_llm.similarity_search(...)` as a proxy for ranked retrieval

## Recommended Workflow

1. Make sure the FAISS index matches the corpus you want to test.
2. Generate the QA sheet.
3. Validate the QA sheet.
4. Start the StatsChat API.
5. Run the evaluation.

If QA was generated from the full corpus in `data/json_conversions`, evaluate with `--content-type all`.

If QA was generated from a latest-only corpus and latest index, evaluate with `--content-type latest`.

Generation and evaluation should use the same corpus conditions. If they do not, variance will be high and results will be hard to interpret.

## Run Commands

### 1. Generate QA With A Local Model

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

### 2. Validate The Generated Sheet

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Auto.xlsx \
  --validate-only
```

### 3. Start The Local API

```bash
uvicorn fast-api.main_api_local:app --host 127.0.0.1 --port 8000
```

### 4. Evaluate Against The API

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Auto.xlsx \
  --host http://127.0.0.1:8000 \
  --content-type all \
  --timeout 420
```

### 5. Smoke Test A Small Subset

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Auto.xlsx \
  --host http://127.0.0.1:8000 \
  --content-type all \
  --timeout 420 \
  --max-rows 3
```

## Generator Parameters

The most important generation flags are:

- `--max-files`: maximum number of JSON documents to sample. `0` means all.
- `--pages-per-doc`: number of pages sampled from each selected document.
- `--max-questions`: maximum number of accepted QA rows after filtering and deduplication.
- `--min-text-length`: minimum page text length before a page is considered.
- `--strict-filters`: enables stricter filtering for grounded and less ambiguous QA.
- `--align-with-index`: only use PDFs that are present in the current FAISS index.
- `--index-pkl`: FAISS metadata pickle used for alignment. Default is `data/db_langchain/index.pkl`.

## Output Files

### Generator output

By default:

- `tests/accuracy/StatsChat_QA_Auto.xlsx`

Sheets:

- `QA_Data`: generated rows in the manual template schema
- `Instructions`: copied from the template if present
- `Explanation`: copied from the template if present
- `Generation_Metadata`: generation parameters and selected evaluation config values

### Evaluator output

By default:

- `tests/accuracy/accuracy_results.csv`
- `tests/accuracy/qa_data_issues.csv` when validation issues are found
- `tests/accuracy/StatsChat_QA_With_Answers.xlsx` if `--write-answers-excel` is used

Important result columns include:

- `predicted_answer`
- `exact_match`
- `token_f1`
- `semantic_similarity`
- `is_refusal`
- `is_correct`
- `reference_url`
- `reference_doc_id`
- `reference_page`
- `evidence_page_match`
- `precision_at_k`
- `recall_at_k`
- `mrr`
- `ndcg`
- `retrieved_doc_ids`
- `error`

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
- Retrieval metrics do not use the exact ranked list returned by the API response. In local mode they use `similarity_search(...)` as a proxy.
- Table-heavy questions can still be brittle even with strict filters.
- If generation and evaluation use different corpus modes or different index contents, measured accuracy can collapse for reasons unrelated to model quality.

## Practical Guidance

- Use `--content-type all` when QA was generated from `data/json_conversions` and evaluated against the full index.
- Rebuild the index before QA generation if corpus contents changed.
- Do not compare runs fairly unless corpus, index, thresholds, `k_docs`, and `k_contexts` were kept aligned.
- Treat the generated QA file as a starting point for testing, not as a final benchmark without review.
