# StatsChat-KE Testing, Retrieval, and Accuracy Evaluation Report

April 2026

Author: Damian Ejlli

## 1. Executive Summary

StatsChat-KE is an experimental retrieval-augmented generation (RAG) system for answering questions from Kenya National Bureau of Statistics (KNBS) publications. The wider project began in mid-October 2025. This report summarises the testing, retrieval, guardrail, and accuracy-evaluation work completed by mid-April 2026, with particular focus on the April 2026 `test_infra` branch work that made the system measurable and safer to change.

The work had two linked goals:

- Build enough automated testing to make substantial architecture changes safely.
- Build an audited accuracy workflow that measures both answer correctness and retrieval quality, not just whether the API returns text.

The headline result from the best full benchmark run is:

| Metric | Result |
|---|---:|
| Total benchmark rows | 74 |
| Answerable rows | 61 |
| Unanswerable rows | 13 |
| Answerable accuracy | 57/61 = 0.934 |
| Unanswerable accuracy | 13/13 = 1.000 |
| Overall accuracy | 70/74 = 0.946 |
| False answer rate on unanswerable questions | 0/13 = 0.000 |
| Pipeline Doc Hit@8 | 56/61 = 0.918 |
| Any Reference Page Hit | 39/61 = 0.639 |

The benchmark expansion was especially important. The project did not start from a strong or stable measured baseline. Very early exploratory cloud runs on tiny subsets scored as low as 0.000 to 0.500, the first full 37-row audited cloud run scored 22/37 = 0.595, and only later did the smaller 37-row benchmark reach 0.919 after repeated tuning. When 24 new answerable rows from under-tested report families were added, answerable accuracy immediately fell to 48/61 = 0.787. This confirmed that the original 37-row set was not representative enough. Subsequent retrieval and routing improvements recovered performance to 57/61 = 0.934 answerable accuracy on the expanded benchmark.

The main technical conclusion is that retrieval architecture is now significantly stronger and more consistent. The cloud API and local API now share the same retrieval pipeline: temporal filtering, report-family routing, cross-encoder reranking, and page-aware generation-context selection. This means local/cloud comparisons can focus more directly on the generator model rather than on different retrieval implementations.

We also ran a model comparison using Mistral Small 3.1 (24B) through OpenRouter. It produced 50/61 = 0.820 answerable accuracy and 13/13 = 1.000 unanswerable accuracy, with identical retrieval metrics to the GPT-5.4-mini run. This confirms that the accuracy gap between the two models is driven entirely by answer synthesis quality rather than retrieval. The evaluator recorded the live API model directly from the `/health` endpoint, making model provenance fully auditable.

It is therefore important not to attribute the final results to a single factor. The measured improvement came from a combination of stronger retrieval architecture and stronger answer generation. Architecture changes improved retrieval and grounding quality across the benchmark, especially on the expanded 74-row set. Model choice still mattered on top of that: with the same retrieval metrics, GPT-5.4-mini outperformed Mistral Small 3.1 on answer synthesis.

Based on the current evidence, the tool appears healthy and suitable for a controlled production or pilot deployment, especially as a retrieval-first assistant that helps users find the relevant KNBS publication, page, and supporting context. The answer accuracy measured on the current audited sample is high, and guardrail behavior is strong. This should not be treated as a one-time permanent certification: the benchmark has 74 rows, no independent held-out split, and observed row-level LLM nondeterminism of roughly one to two rows between repeated runs. In practice, there is no single universally correct sample size that proves a statistical assistant is "done"; production confidence should come from continued benchmark expansion, monitoring, user feedback, and KNBS maintenance over time.

## 2. Background And Objectives

StatsChat-KE follows a RAG architecture:

```text
PDF ingestion -> JSON conversion -> chunking -> FAISS vector index -> retrieval -> LLM answer synthesis
```

Before this work, the system could answer questions from KNBS reports but had several limitations:

- Limited automated unit, integration, and end-to-end coverage.
- No sufficiently detailed audited accuracy benchmark.
- Serious quality issues in the initial QA material available for evaluation, requiring review, correction, and new QA authoring before reliable measurement was possible.
- Weak separation between retrieval quality and answer quality.
- Cloud and local APIs used different retrieval paths, making model comparisons difficult.
- The system did not meaningfully test out-of-scope or unanswerable questions.
- Some FastAPI deployment concerns, such as CORS, API-key protection, rate limiting, and health checks, were not yet handled.

The work described in this report focused on five objectives:

1. Add automated tests around critical retrieval, API, evaluator, and pipeline behavior.
2. Create and expand an audited QA benchmark for answerable and unanswerable questions.
3. Improve retrieval architecture where benchmark evidence showed clear bottlenecks.
4. Add guardrails so the system refuses out-of-scope questions rather than hallucinating.
5. Align local and cloud retrieval so differences in results can be attributed more cleanly to the LLM used for generation.

This report should be read as a technical progress and validation report for the project period from mid-October 2025 to mid-April 2026. The most intensive accuracy, retrieval, guardrail, and deployment-hardening work described here was completed during April 2026.

## 3. Architecture Changes And Accuracy Improvements

### 3.1 Baseline Retrieval And Grounding Problems

The early benchmark runs showed that a single overall accuracy number was not enough. Several different failure modes were mixed together:

- The retriever sometimes found the right report family but the wrong edition.
- The retriever often found the correct document but not the correct page.
- The model sometimes refused even when answerable evidence was present.
- The model sometimes answered confidently from an older or near-duplicate report.
- The model initially answered some out-of-scope questions instead of refusing.

This led to a decision to treat answer quality and retrieval quality as separate measurement problems.

The earliest exploratory measurements underline how immature the initial measured state was. On 7 April 2026, the first tiny cloud smoke runs on 3-row and 10-row slices produced overall accuracies between 0.000 and 0.500. Those runs were too small to serve as a formal benchmark, but they are still useful context: the system was not starting from a high-confidence or high-performing measured baseline.

The first full audited 37-row cloud baseline on 8 April 2026 scored 22/37 = 0.595 answerable accuracy, with Pipeline Doc Hit@8 at 31/37 = 0.838. The later 30/37 = 0.811 result on the same 37-row set is better understood as a pre-expansion plateau after initial iteration, not as the true starting point. Both baselines matter. The 0.595 run is the clearest formal picture of the early system on the audited benchmark, while the 0.811 run is the closest measured approximation of the system state immediately before the April 2026 retrieval, routing, and guardrail improvements that followed. Even that later 0.811 baseline remains only a partial baseline: at that stage the benchmark was smaller, under-tested report families were not yet represented, and unanswerable rows were not yet included.

### 3.2 Retrieval And Reranking Improvements

The cloud retrieval pipeline was improved in several stages:

- **Cross-encoder reranking**: candidate chunks are reranked after initial FAISS retrieval.
- **Report-family routing**: queries are mapped to likely KNBS report families, such as CPI bulletins, Economic Surveys, KDHS, Facts and Figures, Statistical Abstract, FinAccess, Construction Input Price Indices, and Leading Economic Indicators.
- **Temporal candidate widening**: date-specific queries can widen the retrieval pool to avoid missing the correct edition.
- **Precise temporal filtering**: month, quarter, and year tokens are matched against document titles, URLs, and dates.
- **Temporal edition selection**: report periods are extracted from document titles/URLs before falling back to publication dates, avoiding mistakes such as treating a Q4 2023 report published in 2024 as a Q4 2024 report.
- **Lagged-year handling**: some annual publications contain data for the previous year; the retrieval logic accounts for this when selecting report editions.
- **Page-aware generation-context selection**: once relevant documents are selected, better pages from those same documents can be selected for generation context without changing the global document ranking.

### 3.3 Approach Tested And Abandoned: Global Page Injection

One experiment tried to improve page hit rate by injecting additional pages from the top document into the global candidate pool and reranking all candidates together. It did improve page-hit metrics, but it also disrupted cross-document ranking. In one run, page hit improved while Doc Hit@1 regressed, and accuracy stayed flat because gains and regressions cancelled out.

The lesson was important: page refinement should not change the document-level ranking. The final design applies page selection within each selected document's allocation, rather than flooding the global candidate pool with pages from one document. This preserved document retrieval while improving the pages seen by the LLM.

### 3.4 Guardrail Improvements

The benchmark was expanded with 13 unanswerable questions. These included:

- Out-of-country questions.
- Future/unavailable statistics.
- Policy or opinion questions.
- Cross-country comparisons requiring non-KNBS data.
- Vague or subjective questions.

In the first 50-row guardrail run (`tests/accuracy/runs/cloud/2026-04-14_181140`), the system answered 4 of these 13 unanswerable questions with substantive answers. That represented a 31% false-answer rate on out-of-scope queries. Prompt and policy guardrails were tightened so the model refuses questions outside the KNBS/statistical-publication scope. The best run now has:

```text
Correct refusal rate: 13/13 = 1.000
False answer rate:    0/13 = 0.000
```

### 3.5 Local And Cloud Retrieval Parity

The local API previously used a separate local retrieval path. This made it hard to tell whether cloud/local differences came from the LLM or from retrieval architecture. The local API now uses the same retrieval stack as the cloud API:

- `Inquirer.retrieve_documents(...)`
- `Inquirer.select_generation_documents(...)`

The local API still uses local Hugging Face generation, while the cloud API uses the configured cloud LLM. This means:

```text
Cloud API = shared retrieval + cloud LLM generation
Local API = shared retrieval + local Hugging Face generation
```

This is retrieval parity, not full response-shape parity. The local API still returns `references` as a single URL string, while the cloud API returns a list of reference objects.

This distinction matters when interpreting improvements. The architectural work made local/cloud retrieval behavior substantially more comparable, but the headline production numbers in this report still reflect a combination of retrieval improvements and the cloud generator used for final answer synthesis. The local Mistral smoke run is useful as a parity check, but it was only run on 15 rows and should not be treated as directly comparable to the full 74-row cloud results.

## 4. Testing Infrastructure

The architecture changes were supported by automated tests across unit, integration, and end-to-end layers. The latest full test run completed with:

```text
232 passed
```

Warnings remain, mainly FastAPI `on_event` deprecation warnings and some dependency/runtime warnings, but no test failures were present at the time this report was drafted.

### 4.1 Unit Tests

Unit tests cover:

- Cloud retrieval helpers.
- Temporal token parsing.
- Report-family inference.
- Temporal edition selection.
- Retrieval metric helpers.
- Accuracy evaluator matching logic.
- Local retrieval helper behavior.
- Guardrail classification behavior.
- Pydantic response model edge cases.

### 4.2 Integration Tests

Integration tests cover:

- FastAPI `/search` behavior.
- FastAPI `/feedback` behavior.
- FastAPI `/health` behavior.
- API-key protection.
- Local and cloud API schema behavior.
- Search fallback behavior for invalid content types.

### 4.3 End-To-End Tests

End-to-end tests cover:

- Local search UX flow.
- Pipeline failure recovery.
- Update-mode behavior.
- Full update run behavior.

The testing work was not separate from the accuracy work. It made the retrieval refactors safe enough to attempt and gave the team confidence to reject experiments that improved one metric but damaged another.

## 5. Accuracy Benchmark Design

### 5.1 QA Curation And KNBS-Provided Material

The benchmark used in this report should not be understood as a simple pass-through of originally supplied questions. The initial QA material available from KNBS had serious issues for automated accuracy evaluation. Examples included missing or weak evidence fields, ambiguous questions, answer/source alignment problems, and rows that did not give the evaluator enough reliable information to determine whether the system had retrieved the right document and evidence. Concretely, this included cases where the golden answer was difficult to verify against the cited source text, and cases where document IDs or evidence locations were not specific enough for retrieval evaluation.

The project team therefore had to review, amend, and extend the QA material. This included correcting or clarifying existing rows, aligning questions to audited source text and evidence locations, and adding new answerable and unanswerable rows. This curation work was essential: without it, low or high accuracy numbers would have been difficult to interpret because the ground truth itself would not have been sufficiently reliable.

### 5.2 Active Benchmark Workbook

The active audited benchmark is:

```text
tests/accuracy/StatsChat_QA_Verified_Audited.xlsx
```

The current benchmark contains:

| Row type | Count |
|---|---:|
| Answerable | 61 |
| Unanswerable | 13 |
| Total | 74 |

Answerable rows include a question, golden answer, relevant document IDs, evidence locations, and source text. Unanswerable rows follow the authoring guidance by leaving gold/evidence fields blank and setting `should_answer=False`.

### 5.3 Benchmark Evolution

The benchmark evolved in stages:

1. Original 37 answerable rows.
2. Additional evaluator metrics and scoring-method labels.
3. 13 unanswerable guardrail rows.
4. 24 new answerable rows from previously under-tested report families.

The expansion was important because the original 37 rows were too small and too familiar after several optimisation passes. The first 74-row run exposed a large gap on new answerable rows:

| Run | Original 37 accuracy | New 24 accuracy | Overall answerable accuracy |
|---|---:|---:|---:|
| First expanded 74-row run | 33/37 = 0.892 | 15/24 = 0.625 | 48/61 = 0.787 |
| Best GPT-5.4-mini 74-row run | 34/37 = 0.919 | 23/24 = 0.958 | 57/61 = 0.934 |

This is the clearest evidence that the expanded benchmark was necessary. It exposed overfitting risk and then provided a more realistic target for retrieval improvements.

## 6. Metrics And Evaluation Methodology

### 6.1 Overall Accuracy

Overall accuracy is:

```text
correct rows / total evaluated rows
```

For the best GPT-5.4-mini run:

```text
70 / 74 = 0.946
```

### 6.2 Answerable Accuracy

Answerable accuracy is:

```text
correct answerable rows / answerable rows
```

For the best GPT-5.4-mini run:

```text
57 / 61 = 0.934
```

### 6.3 Unanswerable Accuracy And False Answer Rate

Unanswerable accuracy measures correct refusals:

```text
correct refusals / unanswerable rows
```

False answer rate measures hallucination or over-answering on unanswerable rows:

```text
substantive answers on unanswerable rows / unanswerable rows
```

For the best GPT-5.4-mini run:

```text
Correct refusal rate = 13 / 13 = 1.000
False answer rate    = 0 / 13  = 0.000
```

### 6.4 Answer Matching

The evaluator uses deterministic answer matching. For answerable rows, it computes several signals:

- Exact string match.
- Numeric match.
- RapidFuzz text similarity.
- Token F1.
- Semantic similarity.

The final row-level `is_correct` decision uses an explicit OR rule, but the rule has two branches:

- If the audited golden answer is primarily numeric, the row is correct only if `exact_match == 1` or `numeric_match == True`.
- If the audited golden answer is not primarily numeric, the row is correct if any of the following is true:
  - `exact_match == 1`
  - `numeric_match == True`
  - RapidFuzz token-set ratio `>= 85.0`
  - token F1 `>= 0.80`
  - semantic similarity `>= 0.90`

This matters because fuzzy text similarity can create false positives on statistical values. A wrong number can still look textually similar to the right answer, especially when the wording around the number is similar. For that reason, numeric-gold rows deliberately ignore fuzzy/semantic signals when deciding correctness. Those extra signals are still recorded for diagnostics, but they do not override numeric mismatch on numeric rows.

The numeric matcher uses:

```text
absolute tolerance = 0.1
relative tolerance = 0.01
```

This supports common statistical formatting differences such as percentages, scaled values, and rounded figures.

The numeric parser also handles scaled units such as `thousand`, `million`, `billion`, and `trillion`, and treats `('000)`-style table unit markers as a multiplier of 1,000. This was important for KNBS tables where values are often shown in thousands without repeating the word "thousand" in every cell.

Examples:

- Gold: `6.3 per cent`; predicted: `Inflation was 6.3%`. This is correct because numeric matching succeeds even though the wording is different.
- Gold: `KSh 5,774,645 million`; predicted: `5,774,645`. This can fail deterministic answer correctness if the unit/currency wording is omitted, even though the underlying number is right. That is why the report treats some residual cases as evaluator edge cases rather than pure retrieval failures.
- If the gold answer is a short text label without critical numbers, such as a county name or a report family name, correctness can come from exact match, fuzzy similarity, token overlap, or semantic similarity depending on the wording.

### 6.5 Answer Coverage And Missing Answers

Answer coverage is separate from correctness. It measures whether the model produced a substantive answer when `should_answer=True`:

```text
answer coverage = answered answerable rows / answerable rows
```

Answer missing rate is the complement:

```text
answer missing rate = missing or refusal answers on answerable rows / answerable rows
```

An answered row can still be wrong. Conversely, a missing answer on an answerable row is automatically incorrect but is diagnostically different from a confident wrong answer.

### 6.6 Retrieval Metrics

Retrieval metrics compare ranked retrieved documents/pages against audited gold evidence.

The main metrics are:

| Metric | Meaning |
|---|---|
| Precision@k | Relevant hits in top-k divided by k |
| Recall@k | Relevant hits in top-k divided by number of gold items |
| MRR | Reciprocal rank of the first relevant hit |
| nDCG | Discounted ranking score normalised by the ideal ranking |
| Doc Hit@1 | Whether the top retrieved document is gold |
| Doc Hit@k | Whether any top-k document is gold |
| Page Hit | Whether the returned page matches audited evidence pages |

For document metrics, the evaluator first normalises document IDs, removes duplicates, and then scores the unique top-k ranking against the audited `relevant_doc_ids`. Retrieval correctness is therefore not a single OR condition in the same way as answer correctness. Instead, the evaluator reports several complementary ranking metrics so it is possible to distinguish:

- whether the right document was present at all,
- whether it appeared near the top of the ranking,
- and whether the correct evidence page was also returned.

On the current benchmark, most rows have one gold document. In that situation, `Recall@k` and `Doc Hit@k` often converge numerically. They are not the same metric in general: multi-gold rows would make them diverge.

Examples:

- If the gold document appears at rank 3 in the top 8 results, then `Doc Hit@8 = 1`, `Doc Hit@1 = 0`, and `MRR = 1/3 = 0.333`.
- If there is only one gold document and it appears anywhere in the top 8, then `Recall@8 = 1.0`. If it is absent, `Recall@8 = 0.0`.
- If the correct document is returned but the cited page does not match the audited evidence page, document retrieval can still score as a hit while page-level retrieval scores as a miss. This is why page metrics are reported separately from document metrics.
- Pipeline page metrics compare returned `(document, page)` pairs against audited evidence-page pairs. For example, if the API cites the right report but page 17 instead of audited page 22, `Doc Hit@k` may be 1 while page hit remains 0.

### 6.7 FAISS Proxy Metrics vs Pipeline Metrics

The evaluator reports two retrieval metric families:

- `faiss_proxy_*`: diagnostic metrics based on evaluator-side local similarity search.
- `pipeline_*`: metrics based on the API's returned `references`.

Pipeline metrics are more representative of what the API actually used and cited. The FAISS proxy remains useful for comparing raw vector retrieval against the final API retrieval pipeline.

### 6.8 Saved-Run Rescoring And Data Integrity

The evaluator can enrich and rescore saved result CSVs by joining them back to the audited workbook by `query_id`. The `enrich_saved_results_dataframe(...)` path rereads the current gold answers, evidence pages, `should_answer` flags, and relevant document IDs, then recomputes:

- answer correctness
- scoring method
- answer/refusal flags
- pipeline retrieval metrics
- page-hit metrics

This prevents stale cached scores from surviving after workbook edits or evaluator improvements. It also fails loudly if no saved rows match the supplied workbook, which protects against accidentally rescoring a run with the wrong QA file.

## 7. Accuracy Results Over Time

### 7.1 Key Run History

| Stage | Run folder | Rows | Answerable accuracy | Unanswerable accuracy | Overall accuracy | Pipeline Doc Hit@8 |
|---|---|---:|---:|---:|---:|---:|
| Exploratory tiny-slice runs | `2026-04-07_173551` to `2026-04-07_182241` | 3 to 10 | 0.000 to 0.500 | N/A | 0.000 to 0.500 | 0.667 to 0.800 |
| First full 37-row audited cloud baseline | `2026-04-08_114523` | 37 | 22/37 = 0.595 | N/A | 0.595 | 31/37 = 0.838 |
| Early 37-row cloud run | `2026-04-09_162741` | 37 | 30/37 = 0.811 | N/A | 0.811 | 34/37 = 0.919 |
| Page/context improvement on 37 rows | `2026-04-13_142946` | 37 | 33/37 = 0.892 | N/A | 0.892 | 34/37 = 0.919 |
| Guardrail benchmark with 50 rows | `2026-04-14_182404` | 50 | 34/37 = 0.919 | 13/13 = 1.000 | 0.940 | 35/37 = 0.946 |
| First expanded 74-row run | `2026-04-14_185041` | 74 | 48/61 = 0.787 | 13/13 = 1.000 | 0.824 | 50/61 = 0.820 |
| Intermediate expanded run | `2026-04-16_170115` | 74 | 51/61 = 0.836 | 13/13 = 1.000 | 0.865 | 50/61 = 0.820 |
| Family-routing expanded run | `2026-04-16_171338` | 74 | 56/61 = 0.918 | 13/13 = 1.000 | 0.932 | 54/61 = 0.885 |
| Best GPT-5.4-mini run | `2026-04-16_175219` | 74 | 57/61 = 0.934 | 13/13 = 1.000 | 0.946 | 56/61 = 0.918 |

The key result is not only that final accuracy improved. The important engineering signal is that the measured starting point was weak, the first full audited benchmark was only moderate, the expanded benchmark then exposed a much lower score than the team might otherwise have believed, and targeted family-routing and temporal-edition work recovered the score without sacrificing guardrail behavior.

### 7.2 Best GPT-5.4-mini Run

Run:

```text
tests/accuracy/runs/cloud/2026-04-16_175219
```

| Metric | Result |
|---|---:|
| Total evaluated | 74 |
| Answerable | 61 |
| Unanswerable | 13 |
| Answerable accuracy | 57/61 = 0.934 |
| Unanswerable accuracy | 13/13 = 1.000 |
| Overall accuracy | 70/74 = 0.946 |
| Answer coverage | 59/61 = 0.967 |
| Answer missing rate | 2/61 = 0.033 |
| Correct refusal rate | 13/13 = 1.000 |
| False answer rate | 0/13 = 0.000 |
| Pipeline Doc Hit@1 | 49/61 = 0.803 |
| Pipeline Doc Hit@8 | 56/61 = 0.918 |
| Any Reference Page Hit | 39/61 = 0.639 |
| FAISS Proxy Doc Hit@8 | 46/61 = 0.754 |

The difference between FAISS proxy Doc Hit@8 and Pipeline Doc Hit@8 shows the value of the retrieval pipeline beyond raw vector search:

```text
FAISS Proxy Doc Hit@8 = 46/61 = 0.754
Pipeline Doc Hit@8    = 56/61 = 0.918
```

## 8. Model Comparison: GPT-5.4-mini vs Mistral Small 3.1

The team also tested Mistral Small 3.1 (24B) through OpenRouter using the cloud API path. The purpose was to keep retrieval constant while changing the generator model. The evaluator recorded the live API model directly from the `/health` endpoint, making model provenance fully auditable.

| Model / Mode | Run folder | Answerable accuracy | Unanswerable accuracy | Overall accuracy | Pipeline Doc Hit@8 |
|---|---|---:|---:|---:|---:|
| GPT-5.4-mini cloud | `2026-04-16_175219` | 57/61 = 0.934 | 13/13 = 1.000 | 70/74 = 0.946 | 56/61 = 0.918 |
| Mistral Small 3.1 OpenRouter cloud | `2026-04-20_165105` | 50/61 = 0.820 | 13/13 = 1.000 | 63/74 = 0.851 | 56/61 = 0.918 |
| Local Mistral smoke test | `2026-04-20_141856` | 12/15 = 0.800 | Not tested | 12/15 = 0.800 | 14/15 = 0.933 |

The two full cloud runs had identical retrieval metrics:

| Metric | GPT-5.4-mini | Mistral Small 3.1 |
|---|---:|---:|
| Pipeline Doc Hit@1 | 49/61 = 0.803 | 49/61 = 0.803 |
| Pipeline Doc Hit@8 | 56/61 = 0.918 | 56/61 = 0.918 |
| Any Reference Page Hit | 39/61 = 0.639 | 39/61 = 0.639 |
| Answer Coverage | 59/61 = 0.967 | 54/61 = 0.885 |

Retrieval metrics are identical across both models, confirming that document retrieval quality is model-independent. The difference in overall accuracy is driven entirely by generation: GPT produces more accurate synthesised answers from the same retrieved contexts. Both models achieve perfect guardrail compliance on unanswerable questions.

The recorded answer-scoring methods also help interpret these results. Fuzzy text matching is not the dominant source of correct rows on the audited benchmark. On the best GPT run, most correct answerable rows were recorded as `numeric_match`, not as fuzzy text matches. On the clean Mistral comparison run, the same pattern holds, although Mistral produced fewer numeric matches and more misses.

| Recorded scoring method on correct answerable rows | GPT-5.4-mini | Mistral Small 3.1 |
|---|---:|---:|
| Numeric match | 52 | 40 |
| Exact match | 0 | 7 |
| Text match | 5 | 3 |

This table should be read carefully. The `scoring_method` column records the first successful rule in evaluator order. For non-numeric rows, `text_match` is checked before token F1 and semantic similarity, so some rows recorded as `text_match` may also have passed those later thresholds. Even with that caveat, the benchmark is clearly dominated by exact or numeric grounding rather than by fuzzy matching.

This also clarifies how to interpret the overall improvement from the earlier system state. Retrieval and routing changes raised the quality of the evidence delivered to the generator, while GPT-5.4-mini provided a stronger synthesis layer than Mistral on top of that evidence. This supports the recommendation that KNBS can rely on the system primarily as a document retrieval tool — retrieval performance is strong and stable regardless of which generation model is configured.

## 9. Error Analysis

The best GPT-5.4-mini run had four incorrect answerable rows:

| Query ID | Failure type | Diagnosis |
|---|---|---|
| QQ006 | Synthesis / LLM noise | Correct KDHS document was returned, but the model returned no answer. This row has shown run-to-run variability. |
| QQ025 | Retrieval / wrong edition | Query asks for 2022 employment data, but older Economic Survey editions were returned instead of the target edition. |
| QQ028 | Retrieval / edition-policy ambiguity | Query asks for birth certificate percentage without specifying year; older KDHS editions were returned. Fixing this requires a policy decision about preferring latest-in-family when the query lacks a year. |
| QQ070 | Evaluator / unit-formatting gap | Retrieved correct Leading Economic Indicators report and the predicted answer contained the correct number, but omitted currency/unit wording (`KSh` and `million`), so deterministic matching marked it wrong. |

Grouped by category:

| Category | Count | Rows |
|---|---:|---|
| Retrieval / wrong edition or policy | 2 | QQ025, QQ028 |
| Synthesis / LLM variability | 1 | QQ006 |
| Evaluator or answer-formatting edge case | 1 | QQ070 |

No unanswerable rows failed in the best run.

## 10. Evidence Span Diagnostic And RAGAS Decision

The team considered using the RAGAS Python library for retrieval/answer evaluation. During investigation, two issues emerged:

- Installing RAGAS introduced dependency conflicts in the main project environment.
- The relevant non-LLM RAGAS context metrics were not suitable for this dataset shape. The audited `source_text` spans are short human-selected quotes, while retrieved contexts are longer page-sized chunks. String-distance metrics can score a valid short quote embedded in a long chunk as a miss because the compared strings have very different lengths.

Instead, the team implemented a deterministic evidence-span diagnostic:

```text
tests/accuracy/evaluate_ragas.py
```

Despite the filename, the current tool is a RAGAS-like diagnostic rather than a wrapper around the RAGAS library. It computes:

- exact evidence-span containment
- RapidFuzz partial-ratio overlap
- combined evidence-span hit

This tool is useful for case-work, such as investigating whether retrieved context contains the audited evidence span. It is not used as a headline KPI because span-hit did not reliably predict answer correctness on the current benchmark. In many cases, the model answered correctly from adjacent tables or surrounding text even when the auditor's exact quote was not present.

## 11. Deployment Hardening

The FastAPI deployment surface was improved alongside accuracy work.

Changes include:

- Dockerfile entrypoint correction for the cloud API.
- Python base image update.
- CORS middleware with configurable allowed origins.
- API-key protection for query-costing endpoints.
- In-process rate limiting with documented limitations.
- `/health` endpoint with non-secret runtime metadata.
- Structured JSON logging support.
- Pydantic optional-field defaults to avoid response-validation failures.
- Shared query guardrail policy.

These changes strengthen the case for a controlled production or pilot deployment by removing several practical blockers between a local prototype and a deployable API. They should still be paired with operational monitoring, feedback capture, and routine benchmark updates.

## 12. Production Interpretation, Limitations, And Risks

The current evidence supports treating StatsChat-KE as ready for controlled production or pilot use, provided expectations are set correctly. The strongest production use case is document retrieval and evidence navigation: the system is now very good at surfacing the relevant KNBS document, and it should present citations and links prominently so users can inspect the source material directly. The generated answer layer is also performing strongly on the audited sample, but it should be understood as an assistant over the retrieved evidence, not as a replacement for the source publication.

In other words, the project should not be described as "not production ready" solely because the benchmark is smaller than an ideal research benchmark. The measured performance is high enough to support a cautious deployment decision. The right framing is that the system is healthy enough to use, while KNBS should continue maintaining the corpus, expanding the benchmark, monitoring real usage, and improving edge cases over time.

### 12.1 Benchmark Size

The benchmark has improved from 37 rows to 74 rows. This is a meaningful sample for development validation, but it remains smaller than an ideal long-term production benchmark. There is no fixed sample size at which a RAG system becomes definitively "OK"; larger benchmarks simply reduce uncertainty and expose more edge cases. A useful next target would be 100+ rows with a meaningful held-out set.

### 12.2 No Held-Out Split

The current benchmark has been used for both diagnosis and validation. The expanded 74-row benchmark reduced overfitting risk, but it is still not an independent held-out test set.

### 12.3 LLM Nondeterminism

Some rows have changed outcome between repeated runs with the same retrieval results. This suggests a row-level noise floor of roughly one to two rows. The reported 57/61 answerable score should therefore be read as a development estimate, not a fixed deterministic property.

### 12.4 Remaining Retrieval Edge Cases

QQ025 and QQ028 remain unresolved retrieval or policy issues. Fixing them may require deeper edition-selection logic or explicit product policy around "latest" interpretations.

### 12.5 Page-Level Grounding

Pipeline Doc Hit@8 is strong at 56/61 = 0.918, but Any Reference Page Hit is lower at 39/61 = 0.639. Page-level grounding remains an area for further improvement.

### 12.6 FAISS Deserialization Trust Boundary

The project uses FAISS deserialization for local vector indexes. This is acceptable when the index files are controlled and trusted, but the trust boundary should be documented for production.

## 13. Recommendations

### 13.1 Controlled Production Or Pilot Use

- Use the tool initially as a retrieval-first assistant: show the generated answer, but make the supporting documents, pages, and context highly visible.
- Encourage users to open the cited KNBS source when the answer is operationally important.
- Treat the current 0.946 overall accuracy and 1.000 unanswerable accuracy as strong evidence for a controlled rollout, not as a permanent guarantee.
- Maintain an ongoing feedback loop where user issues become new benchmark rows.
- Keep KNBS ownership of content maintenance, source publication updates, and benchmark review.

### 13.2 Continuous Improvement Priorities

- Expand the benchmark to 100+ rows.
- Add more unanswerable, causal, policy, and cross-country boundary cases.
- Create a held-out evaluation split as the benchmark grows.
- Run periodic repeated evaluations to monitor LLM variability.
- Investigate remaining report-edition edge cases, including QQ025 and QQ028, after product policy around edition preference is agreed.
- Continue improving page-level grounding where document retrieval succeeds but page-level evidence is missed.
- Improve evaluator handling of currency and unit wording so correct statistical values are not marked wrong because of formatting differences.

### 13.3 Production Monitoring

If deployed, the API should log:

- query text
- content type
- model/provider
- retrieval metadata
- refusal/answer status
- latency
- user feedback

These logs should avoid sensitive data and should be used to build future benchmark rows from real failure modes.

## 14. Appendices

### Appendix A: Key Run Folders

| Purpose | Run folder |
|---|---|
| Early 37-row cloud baseline | `tests/accuracy/runs/cloud/2026-04-09_162741` |
| 37-row page/context run | `tests/accuracy/runs/cloud/2026-04-13_142946` |
| 50-row guardrail run | `tests/accuracy/runs/cloud/2026-04-14_182404` |
| First expanded 74-row run | `tests/accuracy/runs/cloud/2026-04-14_185041` |
| Intermediate expanded run | `tests/accuracy/runs/cloud/2026-04-16_170115` |
| Family-routing expanded run | `tests/accuracy/runs/cloud/2026-04-16_171338` |
| Best GPT-5.4-mini run | `tests/accuracy/runs/cloud/2026-04-16_175219` |
| Local Mistral smoke run | `tests/accuracy/runs/local/2026-04-20_141856` |
| Mistral Small 3.1 OpenRouter comparison run | `tests/accuracy/runs/cloud/2026-04-20_165105` |

### Appendix B: Best Run Failure Details

| Query ID | Question | Golden answer | Predicted answer | Returned docs/pages | Diagnosis |
|---|---|---|---|---|---|
| QQ006 | According to the 2022 Kenya Demographic and Health Survey, what was the average household size in Kenya? | 3.7 | Empty / missing | KDHS 2022 summary report pages 4, 38, 49, 3, 378 | Synthesis/no-answer despite correct document. |
| QQ025 | What was the total recorded employment in Kenya in 2022, in thousands? | 19,148.2 | Empty / missing | Older Economic Surveys, not the target edition | Retrieval wrong-edition issue. |
| QQ028 | What percentage of children in Kenya have a birth certificate? | 34 percent | About one-quarter / 24 percent | KDHS 2014 and KDHS 2008 pages | Retrieval/policy issue around latest KDHS edition. |
| QQ070 | What was Kenya's broad money supply (M3) in August 2023? | KSh 5,774,645 million | 5,774,645 | Leading Economic Indicators August 2024 pages 14, 15, 13 | Correct number but missing unit/currency wording; evaluator formatting gap. |

### Appendix C: Commands For Reproducing Main Evaluation

Cloud GPT-style benchmark:

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --retrieval-k 8 \
  --timeout 420
```

Local smoke benchmark:

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --host http://127.0.0.1:8000 \
  --api-mode local \
  --content-type all \
  --retrieval-k 8 \
  --timeout 420 \
  --max-rows 15
```

### Appendix D: Current Report Source And Planned Exports

Report source:

```text
docs/reports/2026-04-statschat-ke-testing-accuracy-report.md
```

Planned exports:

```text
docs/reports/2026-04-statschat-ke-testing-accuracy-report.docx
docs/reports/2026-04-statschat-ke-testing-accuracy-report.pdf
```
