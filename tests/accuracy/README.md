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

- auto-detects the worksheet containing the QA table
- checks that the QA sheet has the required columns
- validates row quality and authoring rules
- calls `/search` for each question unless `--validate-only` is used
- compares predicted answers against `golden_answer`
- writes per-row results to CSV
- writes aggregate summary metrics to a separate summary CSV
- appends a one-row summary to a cross-run ledger for comparing models and runs over time
- optionally writes an Excel file with:
  - the original QA sheet unchanged
  - a separate `Predicted_Answers` sheet containing tool outputs only

Important behavior:

- it can run validation only, without calling the API
- it checks generation/evaluation condition alignment if the sheet contains `Generation_Metadata`
- it can evaluate either the local or cloud API
- retrieval metrics are computed with `statschat.generative.local_llm.similarity_search(...)` as a local FAISS proxy for both local and cloud API runs
- by default it requests API debug payloads so cloud runs can capture reasoning and retrieved context; use `--no-api-debug` to disable that

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

### 4. Start The Cloud API

```bash
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001
```

The cloud API itself needs the configured provider key in its environment, for example:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `HF_TOKEN`

### 5. Evaluate Against The API

```bash
# Local API
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Auto.xlsx \
  --host http://127.0.0.1:8000 \
  --content-type all \
  --timeout 420

# Cloud API
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Auto.xlsx \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --timeout 420
```

### 6. Smoke Test A Small Subset

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
- `tests/accuracy/accuracy_results_summary.csv`
- `tests/accuracy/qa_data_issues.csv` when validation issues are found
- `tests/accuracy/StatsChat_QA_With_Answers.xlsx` if `--write-answers-excel` is used
- `tests/accuracy/runs/run_history.csv` as an append-only cross-run ledger

Important result columns include:

- `predicted_answer`
- `predicted_relevant_doc_ids`
- `predicted_evidence_locations`
- `predicted_source_text`
- `model_answered`
- `correct_refusal`
- `false_answer`
- `answered_when_expected`
- `answer_missing`
- `exact_match`
- `token_f1`
- `semantic_similarity`
- `is_refusal`
- `is_correct`
- `reference_url`
- `reference_doc_id`
- `reference_doc_ids_all`
- `reference_page`
- `reference_pages_all`
- `reference_titles`
- `context_from`
- `context_reference`
- `relevant_publications`
- `reasoning`
- `reference_doc_match`
- `any_reference_doc_match`
- `evidence_page_match`
- `any_reference_page_match`
- `faiss_proxy_doc_hit_at_1`
- `faiss_proxy_doc_hit_at_k`
- `faiss_proxy_precision_at_k`
- `faiss_proxy_recall_at_k`
- `faiss_proxy_mrr`
- `faiss_proxy_ndcg`
- `faiss_proxy_retrieved_doc_ids`
- `pipeline_doc_hit_at_1`
- `pipeline_doc_hit_at_k`
- `pipeline_precision_at_k`
- `pipeline_recall_at_k`
- `pipeline_mrr`
- `pipeline_ndcg`
- `pipeline_page_precision_at_k`
- `pipeline_page_recall_at_k`
- `pipeline_page_mrr`
- `pipeline_page_ndcg`
- `scoring_method`
- `error`

Each timestamped run folder under `tests/accuracy/runs/{local|cloud}/{timestamp}/` also contains:

- `accuracy_results.csv`
- `run_report.md`
- `run_metadata.txt`
- `summary_metrics.csv`

And `tests/accuracy/runs/run_history.csv` keeps one summary row per run, including:

- timestamp
- run directory
- requested and observed API mode
- provider
- model
- QA file
- thresholds
- top-line accuracy and retrieval metrics

This ledger is useful when comparing multiple cloud models for the same benchmark.

The Excel workbook written by `--write-answers-excel` now contains:

- the original QA sheet unchanged
- `Predicted_Answers` with:
  - `query_id`
  - `query_text`
  - `predicted_answer`
  - `predicted_relevant_doc_ids`
  - `predicted_evidence_locations`
  - `predicted_source_text`
  - `reference_url`
- any other non-QA sheets copied through, such as `Instructions`, `Explanation`, or `Notes`

## How Document Matching Works

There are three different "document" concepts in the evaluator. Keeping them separate avoids a lot of confusion.

- `relevant_doc_ids`: the gold relevant document IDs from the QA spreadsheet. This is the ground truth.
- `retrieved_doc_ids`: the ranked document IDs produced during evaluation by local retrieval proxy `similarity_search(...)`. These are used for retrieval metrics such as `Precision@k`, `Recall@k`, `MRR`, and `nDCG`.
- `reference_doc_id` / `reference_doc_ids_all`: the document IDs extracted from the API response `references` field. These are used for citation-style checks, not for the retrieval formulas.

Important distinction:

- retrieval metrics compare `relevant_doc_ids` against `retrieved_doc_ids`
- reference and page-match metrics compare gold evidence against the API's returned references

This means a first-reference mismatch does **not** automatically mean the `Precision@k` or `Recall@k` formula is wrong. It usually means the API cited a different document first, or returned multiple references and the gold one was not first.

## Metric Definitions And Formulas

For retrieval metrics, the script first:

- normalizes all document IDs
- removes duplicate retrieved documents while keeping rank order
- keeps the first `k` unique retrieved docs

Let:

- `G` = set of normalized gold relevant document IDs from `relevant_doc_ids`
- `R_k` = first `k` normalized unique retrieved document IDs
- `rel_i = 1` if the document at rank `i` in `R_k` is in `G`, otherwise `0`

### Accuracy

The evaluator first computes a per-row boolean `is_correct`, then aggregates it.

For answerable rows (`should_answer = TRUE`):

- a refusal-style answer is automatically incorrect
- otherwise a row is marked correct if **any** of the following passes:
  - exact match
  - numeric match within tolerance
  - RapidFuzz text similarity above threshold
  - token F1 above threshold
  - semantic similarity above threshold

For unanswerable rows (`should_answer = FALSE`):

- a row is marked correct if the model refused appropriately

Aggregate accuracy metrics are then:

#### `Answerable accuracy`

```text
Answerable accuracy =
(# answerable rows with is_correct = TRUE) / (# answerable rows)
```

#### `Unanswerable accuracy`

```text
Unanswerable accuracy =
(# unanswerable rows with is_correct = TRUE) / (# unanswerable rows)
```

This is effectively the current evaluator's refusal accuracy over `should_answer = FALSE` rows.

#### `Overall accuracy`

```text
Overall accuracy =
(# all evaluated rows with is_correct = TRUE) / (# all evaluated rows)
```

### Exact Match (EM)

`1` if normalized predicted answer equals normalized gold answer, else `0`.

### Token F1

Token-overlap F1 between normalized gold answer and predicted answer.

### Semantic Similarity

Cosine similarity between sentence-transformer embeddings of the gold and predicted answers.

### Numeric Match

Numeric answers are also checked with absolute and relative tolerance, including percent handling.

### Retrieval Metrics

#### `Precision@k`

Mathematical expression:

```text
Precision@k = (sum from i=1 to k of rel_i) / k
```

Implementation notes:

- the denominator is always `k`
- if fewer than `k` unique docs are retrieved, the remaining ranks are treated as non-relevant (`0`)

#### `Recall@k`

Mathematical expression:

```text
Recall@k = |R_k ∩ G| / |G|
```

Implementation notes:

- recall uses unique relevant docs found in the top `k`
- if a row has only one gold document, `Recall@k` can only be `0` or `1`

#### `MRR`

If the first relevant retrieved document appears at rank `r`, then:

```text
MRR = 1 / r
```

If no relevant document appears in the top `k`, then:

```text
MRR = 0
```

#### `DCG@k`

```text
DCG@k = sum from i=1 to k of rel_i / log2(i + 1)
```

#### `IDCG@k`

The ideal ranking places all relevant documents first:

```text
IDCG@k = sum from i=1 to min(|G|, k) of 1 / log2(i + 1)
```

#### `nDCG@k`

```text
nDCG@k = DCG@k / IDCG@k
```

#### `Doc Hit@1`

```text
Doc Hit@1 = 1 if the first retrieved unique document is in G, else 0
```

#### `Doc Hit@k`

```text
Doc Hit@k = 1 if any document in R_k is in G, else 0
```

### Reference And Evidence Match Metrics

These are different from retrieval metrics. They are based on the API response `references` field.

#### `First Reference Doc Match`

```text
First Reference Doc Match = 1 if reference_doc_id is in G, else 0
```

#### `Any Reference Doc Match`

```text
Any Reference Doc Match = 1 if any doc in reference_doc_ids_all is in G, else 0
```

#### `First Reference Page Hit`

```text
First Reference Page Hit = 1 if the first returned (doc, page) pair matches the
gold evidence page for that document, else 0
```

#### `Any Reference Page Hit`

```text
Any Reference Page Hit = 1 if any returned (doc, page) pair matches the
gold evidence pages, else 0
```

Implementation note:

- the evaluator now records both the first returned reference and the full returned reference set, so citation analysis is no longer limited to only one returned reference

### Safe Response Rate

In the current implementation this is equal to `overall_accuracy`.

### Refusal And Guardrail Metrics

These metrics use the `should_answer` label together with the model's observed behavior.

The evaluator derives:

- `model_answered = TRUE` if the model returned a non-refusal answer
- `model_answered = FALSE` if the model returned a refusal-style answer

#### `Correct Refusal Rate`

Over rows where `should_answer = FALSE`:

```text
Correct Refusal Rate =
(# rows where model_answered = FALSE) / (# rows where should_answer = FALSE)
```

This corresponds to "the tool refused when it should refuse."

#### `False Answer Rate`

Over rows where `should_answer = FALSE`:

```text
False Answer Rate =
(# rows where model_answered = TRUE) / (# rows where should_answer = FALSE)
```

This is the key guardrail failure rate.

#### `Answer Coverage`

Over rows where `should_answer = TRUE`:

```text
Answer Coverage =
(# rows where model_answered = TRUE) / (# rows where should_answer = TRUE)
```

This measures whether the tool answered when an answer was expected.

#### `Answer Missing Rate`

Over rows where `should_answer = TRUE`:

```text
Answer Missing Rate =
(# rows where model_answered = FALSE) / (# rows where should_answer = TRUE)
```

This detects overly cautious refusals or missing answers on answerable questions.

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
- extra columns such as `source_url` are allowed and ignored unless explicitly used

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
- Reference-based metrics and retrieval metrics are intentionally different:
  - retrieval metrics evaluate ranked retrieval against `relevant_doc_ids`
  - reference/page metrics evaluate what the API actually cited in `references`
- Table-heavy questions can still be brittle even with strict filters.
- If generation and evaluation use different corpus modes or different index contents, measured accuracy can collapse for reasons unrelated to model quality.

## Practical Guidance

- Use `--content-type all` when QA was generated from `data/json_conversions` and evaluated against the full index.
- Rebuild the index before QA generation if corpus contents changed.
- Do not compare runs fairly unless corpus, index, thresholds, `k_docs`, and `k_contexts` were kept aligned.
- Treat the generated QA file as a starting point for testing, not as a final benchmark without review.
- For report writing, use:
  - the Excel workbook for human-readable gold vs predicted comparison
  - the per-row results CSV for detailed technical analysis
  - the summary CSV for headline metrics such as overall accuracy, retrieval metrics, and refusal rates

## Standalone Evidence Span Evaluation

For additional retrieval diagnostics, you can evaluate a saved run with
deterministic evidence-span checks using `tests/accuracy/evaluate_ragas.py`.

This script does not call the API again. It reads:

- the audited workbook, typically `tests/accuracy/StatsChat_QA_Verified_Audited.xlsx`
- an existing `accuracy_results.csv` from a saved run

It computes:

- exact evidence-span containment
- RapidFuzz `partial_ratio` overlap
- a combined evidence-span hit flag

The mapping is:

- `user_input <- query_text`
- `source_text <- audited evidence span`
- `retrieved_contexts <- context_texts.split("\\n---\\n")`

Example:

```bash
.venv/bin/python tests/accuracy/evaluate_ragas.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --results-input tests/accuracy/runs/cloud/2026-04-09_162741/accuracy_results.csv
```

By default this writes:

- `span_recall_results.csv`
- `span_recall_summary.csv`
- `span_recall_report.md`

into the same directory as the supplied `accuracy_results.csv`.

Notes:

- Rows are only evaluated when `should_answer = TRUE`, `predicted_answer` is non-empty,
  `source_text` is present, and `context_texts` contains at least one retrieved chunk.
- Exact hit is a normalized substring check of `source_text` inside any retrieved chunk.
- Fuzzy hit uses `RapidFuzz partial_ratio` to tolerate OCR drift and minor chunk noise.
- On the audited KNBS benchmark, this evaluator is best used as a row-level
  diagnostic rather than a headline KPI. See
  [Evidence Span Evaluator Limitations](/Users/EjlliD/Developer/statschat-ke/docs/investigations/2026-04-09-evidence-span-evaluator-limitations.md).
- This is a secondary diagnostic layer. It does not replace the main deterministic
  benchmark in `evaluate_accuracy.py`.
