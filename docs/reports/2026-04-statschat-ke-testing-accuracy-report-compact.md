# StatsChat-KE Testing, Retrieval, and Accuracy Evaluation Report

April 2026

Author: Damian Ejlli

## Executive Summary

StatsChat-KE is an experimental retrieval-augmented generation system designed to answer questions from Kenya National Bureau of Statistics publications. The project began in mid-October 2025, and this report summarises the testing, architecture, and accuracy-evaluation work completed by mid-April 2026.

The main finding is positive. On the current audited benchmark of 74 questions, the best cloud run achieved 70 correct outcomes out of 74, giving an overall accuracy of 0.946. On answerable questions, the tool answered 57 out of 61 correctly. On unanswerable questions, it correctly refused all 13 and produced no false answers.

The system should be viewed as healthy and suitable for a controlled production or pilot deployment, especially as a retrieval-first assistant. Its strongest production use case is helping users find the relevant KNBS publication, page, and supporting context. The generated answer layer is also performing strongly, but users should still be encouraged to inspect the cited source when the answer is operationally important.

The benchmark is not a permanent certification. It is a strong evidence base for cautious deployment and continued maintenance. KNBS should continue expanding the benchmark, monitoring real usage, and adding new test cases as the corpus and user needs evolve.

The final result should not be attributed to one factor alone. The improvement came from both architecture changes and model choice. Retrieval and routing improvements made the evidence pipeline stronger and more stable, while GPT-5.4-mini produced more accurate answers than Mistral Small 3.1 from the same retrieved contexts.

| Headline Metric | Result |
|---|---:|
| Total benchmark questions | 74 |
| Answerable questions | 61 |
| Unanswerable questions | 13 |
| Answerable accuracy | 57/61 = 0.934 |
| Unanswerable accuracy | 13/13 = 1.000 |
| Overall accuracy | 70/74 = 0.946 |
| False answer rate on unanswerable questions | 0/13 = 0.000 |
| Correct document in top 8 references | 56/61 = 0.918 |
| Correct evidence page found in references | 39/61 = 0.639 |

## Background And Objectives

StatsChat-KE uses a retrieval-and-generation architecture. It indexes KNBS publications, retrieves relevant content for a user question, and asks a language model to produce an answer grounded in that retrieved context.

Before this work, the system could answer questions, but it was difficult to say how reliable it was. The project did not have a mature automated test suite for the RAG behavior, and it did not have an audited benchmark that could support a defensible accuracy claim. Local and cloud modes also used different retrieval behavior. That made it hard to know whether errors came from retrieval, the language model, the evidence data, or the evaluator.

The project did not start from a strong measured baseline. The earliest exploratory cloud smoke runs on tiny 3-row and 10-row slices scored between 0.000 and 0.500. The first full audited 37-row cloud benchmark then scored 22/37 = 0.595. A later 37-row plateau of 30/37 = 0.811 is the clearest approximation of the system immediately before the main April 2026 retrieval, routing, and guardrail improvements, although it still came from a smaller benchmark with no unanswerable rows.

The work described in this report had three practical objectives. First, build automated tests so the system could be changed safely. Second, create a reliable audited accuracy benchmark with both answerable and unanswerable questions. Third, improve the retrieval and guardrail behavior until the measured performance was strong enough to support a controlled rollout.

## QA Curation And Benchmark Quality

The benchmark was not a simple pass-through of the initial QA material available from KNBS. The initial material had serious issues for automated accuracy evaluation. Some rows had missing or weak evidence fields, some questions were ambiguous, and some answer/source links were difficult to verify. In some cases, document IDs or evidence locations were not specific enough to evaluate whether the retrieval system had found the right source.

The project team therefore reviewed, amended, and extended the QA material. Existing rows were clarified where needed, evidence locations were aligned to source text, and new rows were added. The team also defined the benchmark structure needed for evaluation: each answerable row needed a question, a golden answer, a relevant document identifier, an evidence location, and a source text span. Unanswerable rows needed to be marked explicitly while leaving gold/evidence fields blank. This curation was essential. Without reliable ground truth, a high or low accuracy number would have been difficult to interpret.

The current audited benchmark contains 74 rows: 61 answerable questions and 13 unanswerable questions. The unanswerable questions are important because they test whether the system refuses out-of-scope requests rather than inventing statistics.

## Architecture Improvements

The benchmark showed that overall accuracy alone was not enough. The system could fail in several ways: it could retrieve the wrong report edition, find the right report but the wrong page, refuse an answerable question, or answer from an older near-duplicate source.

The retrieval architecture was improved to address these problems. The system now uses stronger reranking, report-family recognition, temporal edition selection, and page-aware context selection. In practical terms, the retrieval stage no longer relies only on raw vector similarity. It now also uses knowledge about report families, dates, months, quarters, and report editions. This means that questions about specific families such as CPI bulletins, Economic Surveys, KDHS, Facts and Figures, Statistical Abstracts, FinAccess, Construction Input Price Indices, and Leading Economic Indicators are routed more reliably to the correct publications.

One experiment was deliberately abandoned. An early page-selection approach inserted many pages from the top document into the global ranking pool. It improved page-hit metrics but disrupted document ranking and did not improve accuracy. The final design keeps document ranking stable and improves page selection only within already selected documents. This is a better architecture for long reports.

The local and cloud APIs now share the same retrieval behavior. The intended difference is the language model used for answer generation. This makes local/cloud comparisons more meaningful because retrieval is no longer a hidden source of divergence.

## Testing Infrastructure

Automated tests were added across unit, integration, and end-to-end layers. This was a major part of the work: the test suite was built to give the team confidence that retrieval changes, API changes, evaluator changes, and pipeline changes could be made without silently breaking existing behavior. The latest full test run completed successfully with 232 tests passing.

The tests cover retrieval helpers, temporal parsing, report-family recognition, API endpoints, guardrails, evaluator logic, feedback endpoints, health checks, and end-to-end search flows. This test coverage made the retrieval refactors safer and allowed the team to reject changes that improved one metric while damaging another.

## Evaluation Methodology

The evaluator measures answer quality, retrieval quality, and refusal quality. This distinction is central to interpreting the results because a RAG system can fail in different ways: it can retrieve the wrong evidence, retrieve the right evidence but synthesize the wrong answer, or answer when it should refuse.

Accuracy is measured row by row against the audited benchmark. For answerable questions, a row is correct when the predicted answer matches the audited golden answer. For unanswerable questions, a row is correct when the system refuses or returns no substantive answer. The report therefore separates answerable accuracy, unanswerable accuracy, overall accuracy, answer coverage, and false answer rate.

For answerable rows, correctness is not judged by one string test alone. The evaluator computes exact match, numeric match, RapidFuzz similarity, token F1, and semantic similarity. The final rule is an OR rule, but it depends on the type of gold answer:

- if the gold answer is primarily numeric, the row is correct only if exact match or numeric match succeeds;
- if the gold answer is not primarily numeric, the row is correct if exact match, numeric match, RapidFuzz similarity, token F1, or semantic similarity passes its threshold.

The default thresholds are:

- RapidFuzz token-set ratio: `85.0`
- token F1: `0.80`
- semantic similarity: `0.90`
- numeric absolute tolerance: `0.1`
- numeric relative tolerance: `0.01`

This design is deliberate. A wrong number can still look textually similar to the right answer, so fuzzy and semantic signals are not allowed to overrule numeric mismatch when the gold answer is numeric.

Example: if the gold answer is `6.3 per cent` and the model answers `Inflation was 6.3%`, the row is correct because numeric matching succeeds. If the gold answer is `KSh 5,774,645 million` and the model returns only `5,774,645`, deterministic scoring may still mark it wrong because the unit and currency wording were omitted.

Retrieval metrics measure whether the system returned the right document and page before answer generation. The report distinguishes raw FAISS proxy retrieval from the final API pipeline, because the production pipeline includes reranking, temporal handling, report-family routing, and page selection. The detailed formulas and scoring rules used for these metrics are included in Appendix 2.

## Results Over Time

The evaluation process revealed an important overfitting risk. The original 37-row benchmark eventually reached high accuracy, but when 24 new answerable questions from under-tested report families were added, answerable accuracy initially dropped to 48 out of 61. This showed that the original set was not representative enough.

After targeted retrieval improvements, performance recovered on the expanded benchmark. The best run reached 57 correct answerable rows out of 61 and retained perfect refusal behavior on the 13 unanswerable rows.

| Stage | Rows | Answerable Accuracy | Unanswerable Accuracy | Overall Accuracy | Correct Document In Top 8 |
|---|---:|---:|---:|---:|---:|
| Exploratory tiny-slice runs | 3 to 10 | 0.000 to 0.500 | N/A | 0.000 to 0.500 | 0.667 to 0.800 |
| First full 37-row audited cloud baseline | 37 | 22/37 = 0.595 | N/A | 0.595 | 31/37 = 0.838 |
| Early 37-row cloud run | 37 | 30/37 = 0.811 | N/A | 0.811 | 34/37 = 0.919 |
| Improved 37-row run | 37 | 33/37 = 0.892 | N/A | 0.892 | 34/37 = 0.919 |
| Guardrail benchmark | 50 | 34/37 = 0.919 | 13/13 = 1.000 | 0.940 | 35/37 = 0.946 |
| First expanded 74-row run | 74 | 48/61 = 0.787 | 13/13 = 1.000 | 0.824 | 50/61 = 0.820 |
| Family-routing expanded run | 74 | 56/61 = 0.918 | 13/13 = 1.000 | 0.932 | 54/61 = 0.885 |
| Best GPT-5.4-mini run | 74 | 57/61 = 0.934 | 13/13 = 1.000 | 0.946 | 56/61 = 0.918 |

The most important lesson is not just that the final score improved. The early measured system state was weak, the first full audited benchmark was only moderate, the expanded benchmark then exposed a real weakness, and the subsequent retrieval improvements recovered performance without sacrificing guardrail behavior.

The results also show why both testing and benchmark work were needed. Without the expanded audited benchmark, the team might have concluded too early that the system was already performing near its final level. Without the automated tests, the architecture changes required to recover performance on the expanded benchmark would have been riskier to make.

The best run is summarised in more detail below.

| Best Run Metric | Result |
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

## Model Comparison

The team also compared GPT-5.4-mini with Mistral Small 3.1 (24B) through OpenRouter. The purpose was to hold retrieval constant and compare answer generation. The evaluator recorded the live API model directly from the `/health` endpoint, making model provenance fully auditable.

Both full cloud runs had identical retrieval metrics. The correct document appeared in the top eight references for 56 out of 61 answerable questions in both runs. The correct evidence page appeared for 39 out of 61 in both runs. The difference was answer synthesis: GPT-5.4-mini answered 57 out of 61 answerable questions correctly, while Mistral answered 50 out of 61 correctly.

| Model And Mode | Answerable Accuracy | Unanswerable Accuracy | Overall Accuracy | Correct Document In Top 8 |
|---|---:|---:|---:|---:|
| GPT-5.4-mini via cloud API | 57/61 = 0.934 | 13/13 = 1.000 | 70/74 = 0.946 | 56/61 = 0.918 |
| Mistral Small 3.1 via OpenRouter | 50/61 = 0.820 | 13/13 = 1.000 | 63/74 = 0.851 | 56/61 = 0.918 |
| Local Mistral smoke test | 12/15 = 0.800 | Not tested | 12/15 = 0.800 | 14/15 = 0.933 |

Retrieval metrics are identical across both models, confirming that document retrieval quality is model-independent. The difference in overall accuracy is driven entirely by generation quality. Both models achieve perfect guardrail compliance on unanswerable questions. This supports the recommendation that KNBS can rely on the system primarily as a document retrieval tool — retrieval performance is strong and stable regardless of which generation model is configured.

The recorded scoring methods show that fuzzy matching is not dominating the benchmark. On the best GPT run, 52 correct answerable rows were recorded as `numeric_match` and only 5 as `text_match`. On the clean Mistral comparison run, 40 correct answerable rows were recorded as `numeric_match`, 7 as `exact_match`, and 3 as `text_match`. This means the benchmark is mostly being won through correct numeric or exact grounding rather than through permissive fuzzy matching.

## Error Analysis

The best GPT-5.4-mini run had four incorrect answerable rows. Two were retrieval or report-edition issues, one was a synthesis/no-answer issue, and one was a formatting/evaluator edge case.

| Category | Count | Explanation |
|---|---:|---|
| Retrieval or edition policy | 2 | The system selected the wrong edition or needed a clearer policy for latest-in-family behavior. |
| Synthesis variability | 1 | The correct document was present, but the model returned no answer. |
| Formatting or evaluator edge case | 1 | The model returned the correct number but omitted currency/unit wording needed by the deterministic evaluator. |

| Query ID | Issue | Diagnosis |
|---|---|---|
| QQ006 | Synthesis variability | The correct KDHS document was returned, but the model returned no answer. |
| QQ025 | Wrong edition | The query asked for 2022 employment data, but older Economic Survey editions were returned. |
| QQ028 | Edition policy | The query did not specify a year, and older KDHS editions were returned instead of the likely latest edition. |
| QQ070 | Formatting/evaluator edge case | The model returned the correct number but omitted `KSh` and `million`, so deterministic matching marked it wrong. |

The remaining errors are understandable and bounded. The highest priority for a production pilot is not to optimise these four rows further, but to monitor real usage and add new benchmark cases as issues are discovered.

## Evidence Span Diagnostic

The team considered using the RAGAS Python library. During testing, the library introduced dependency concerns, and its non-LLM context metrics were not well matched to this benchmark. The audited evidence spans are short human-selected quotes, while retrieved contexts are longer page-sized chunks. Direct string-distance comparison between those two shapes can be misleading.

The team therefore implemented a deterministic evidence-span diagnostic instead. It checks whether audited source text appears in retrieved contexts exactly or approximately. This diagnostic is useful for case-work, but it is not used as the headline KPI because span-hit did not reliably predict answer correctness on this benchmark.

## Deployment Hardening

The API was also hardened for deployment. The work included CORS configuration, API-key protection, rate limiting, a health endpoint, structured logging support, Dockerfile correction, response-schema fixes, and shared guardrail policy.

These changes strengthen the case for controlled deployment. They should be paired with operational monitoring, feedback capture, and routine benchmark updates.

## Production Interpretation

The current evidence supports treating StatsChat-KE as ready for controlled production or pilot use, provided the product is framed correctly. The strongest use case is document retrieval and evidence navigation. The tool should show the generated answer, but it should also make the supporting publication, page, and context easy to inspect.

The measured answer accuracy is high enough to support a cautious deployment decision. However, the tool should not be treated as finished. KNBS will need to maintain the indexed corpus, review user feedback, expand the benchmark, and continue improving the system as publications and user needs evolve.

There is no universal sample size at which a RAG system becomes definitively acceptable. A larger benchmark reduces uncertainty and reveals more edge cases, but production confidence should come from a combination of benchmark performance, monitoring, user feedback, and operational governance.

Key limitations and risks are:

| Limitation | Interpretation |
|---|---|
| Benchmark size | The benchmark has improved to 74 rows, which is meaningful for development validation, but a larger benchmark would reduce uncertainty. |
| No held-out split | The current benchmark has been used for both diagnosis and validation, so a future held-out set would give a stronger independent signal. |
| LLM nondeterminism | Some individual rows have changed outcome between repeated runs; the measured accuracy should be read as a strong estimate, not a fixed deterministic value. |
| Model comparison | The Mistral run uses a smaller model; GPT outperforms on synthesis while retrieval remains identical. |
| Remaining edge cases | A small number of report-edition and formatting cases remain. |
| FAISS trust boundary | The vector index files should be treated as trusted artifacts; this should be documented for production operations. |

## Recommendations

For a pilot or controlled production deployment, the tool should be positioned as a retrieval-first assistant. Users should see the answer, but the cited KNBS source should remain central. This is especially important for operational or policy-relevant use.

KNBS should maintain ownership of source updates, benchmark review, and feedback triage. New user issues should be converted into benchmark rows. The benchmark should be expanded beyond 74 rows, with more unanswerable, causal, policy, and cross-country boundary questions.

Future technical work should include improving unit and currency matching in the evaluator, investigating the remaining edition-selection edge cases, and continuing to improve page-level grounding.

## Appendix 1: Main Evaluation Runs

| Purpose | Run Folder |
|---|---|
| Early 37-row cloud baseline | `tests/accuracy/runs/cloud/2026-04-09_162741` |
| Improved 37-row run | `tests/accuracy/runs/cloud/2026-04-13_142946` |
| Guardrail run with initial false answers | `tests/accuracy/runs/cloud/2026-04-14_181140` |
| Guardrail run after fix | `tests/accuracy/runs/cloud/2026-04-14_182404` |
| First expanded 74-row run | `tests/accuracy/runs/cloud/2026-04-14_185041` |
| Family-routing expanded run | `tests/accuracy/runs/cloud/2026-04-16_171338` |
| Best GPT-5.4-mini run | `tests/accuracy/runs/cloud/2026-04-16_175219` |
| Local Mistral smoke run | `tests/accuracy/runs/local/2026-04-20_141856` |
| Mistral Small 3.1 OpenRouter comparison run | `tests/accuracy/runs/cloud/2026-04-20_165105` |

## Appendix 2: Detailed Metric Definitions And Formulas

This appendix gives the technical definitions behind the metrics used in the report. The main body uses the metrics to tell the evaluation story; this appendix explains how they are calculated.

Accuracy is measured row by row against the audited benchmark workbook. For answerable rows, the system is correct when the generated answer matches the audited golden answer. For unanswerable rows, the system is correct when it refuses or returns no substantive answer. Overall accuracy combines both row types.

| Metric | Formula |
|---|---|
| Overall accuracy | Correct rows / total evaluated rows |
| Answerable accuracy | Correct answerable rows / answerable rows |
| Unanswerable accuracy | Correct refusals / unanswerable rows |
| False answer rate | Substantive answers on unanswerable rows / unanswerable rows |
| Safe response rate | Correct answers and correct refusals / total evaluated rows |

Answerable rows use deterministic answer matching rather than manual judgment during evaluation. Exact match checks normalized string equality. Numeric match extracts numbers and units from the gold and predicted answers, handles scaled units such as thousands and millions, and compares values with an absolute tolerance of 0.1 and a relative tolerance of 0.01. This is important because statistical answers are often expressed with different wording while containing the same value. The evaluator also handles KNBS table unit markers such as `('000)`, where table values must be interpreted in thousands.

For text-heavy rows, the evaluator also records fuzzy text similarity, token-overlap F1, and semantic similarity. These are useful diagnostics, but numeric rows are primarily judged by exact or numeric match because most benchmark questions ask for statistical values. This is why exact match can be low while overall accuracy is high: the model may answer "inflation was 6.3 per cent" while the gold cell contains only "6.3".

Answer coverage is separate from correctness. It measures whether the model produced a substantive answer when the row was answerable. An answer can be present but wrong, so coverage should not be read as accuracy.

| Coverage Metric | Formula |
|---|---|
| Answer coverage | Answered answerable rows / answerable rows |
| Answer missing rate | Missing answers on answerable rows / answerable rows |

Retrieval metrics measure whether the right source material was returned before answer generation. They are calculated separately from answer correctness so that retrieval failures can be distinguished from synthesis failures.

| Retrieval Metric | Formula Or Meaning |
|---|---|
| Precision@k | Relevant hits in top-k results / k |
| Recall@k | Relevant hits in top-k results / total gold relevant items |
| Doc Hit@1 | 1 if the first returned document is a gold document, otherwise 0 |
| Doc Hit@k | 1 if any top-k returned document is a gold document, otherwise 0 |
| MRR | 1 / rank of the first relevant result, or 0 if none is found |
| nDCG | Discounted gain of the returned ranking divided by the ideal discounted gain |
| Page Hit | 1 if a returned reference page matches an audited evidence page, otherwise 0 |

For document metrics, document IDs are normalised, duplicates are removed, and then the unique top-k ranking is compared against the audited `relevant_doc_ids`. Retrieval correctness is therefore described by a family of metrics, not by one yes/no rule.

Examples:

- If the right document appears third in the ranking, then `Doc Hit@8 = 1`, `Doc Hit@1 = 0`, and `MRR = 1/3`.
- If there is one gold document and it appears anywhere in the top 8, then `Recall@8 = 1.0`.
- If the right document is returned but the wrong page is cited, document retrieval can still be correct while page hit remains 0.

On the current benchmark, most answerable rows have one gold document. In that single-gold setting, Recall@k and Doc Hit@k often converge numerically because finding the one gold document means recall is 1 and missing it means recall is 0. They are not the same metric in general. If a future row has multiple relevant documents, Recall@k can take fractional values while Doc Hit@k remains a binary "any hit" signal.

The report includes both FAISS proxy retrieval and pipeline retrieval. FAISS proxy metrics are a diagnostic view of raw vector search. Pipeline metrics are based on the API's returned references after the full retrieval stack has run, including reranking, temporal handling, report-family routing, and page selection. In the best run, raw FAISS retrieval found the correct document in the top eight for 46 of 61 answerable rows, while the full API pipeline found it for 56 of 61. This difference shows that the retrieval architecture adds value beyond basic vector similarity.

Saved evaluation runs can be rescored against the current audited workbook. This protects data integrity when the benchmark is corrected or extended: the evaluator rereads the current golden answers, evidence pages, relevant documents, and answerability flags, then recomputes answer correctness and retrieval metrics. The reported scores are therefore not stale cached values from an earlier version of the workbook.
