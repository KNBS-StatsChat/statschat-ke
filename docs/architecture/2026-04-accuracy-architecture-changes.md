# April 2026 Accuracy-Driven Architecture Changes

This document is the engineering companion to the April 2026 testing and
accuracy reports. Its purpose is narrower than the stakeholder reports: it
records the concrete architecture changes that were made to StatsChat-KE,
where they were inserted in the codebase, why they were expected to help, and
what benchmark evidence suggested that they actually did help.

It should be read together with:

- `docs/reports/2026-04-statschat-ke-testing-accuracy-report.md`
- `tests/accuracy/README.md`
- `tests/accuracy/evaluate_accuracy.py`

## 1. Why This Document Exists

The April 2026 work improved measured accuracy substantially, but the final
improvement came from more than one source:

- retrieval and routing architecture improvements
- stronger guardrails for unanswerable questions
- better benchmark coverage and evaluator quality
- stronger cloud answer generation with GPT-5.4-mini than with Mistral

The stakeholder reports already explain the overall outcome. This document
answers a more engineering-focused question:

> Which code changes actually changed the retrieval or answer pipeline, where do
> they live, and why should we believe they improved accuracy?

## 2. What Counts As An Architecture Change Here

This document focuses on changes to the live query path or closely related API
behavior:

- retrieval candidate generation
- report-family routing
- temporal edition selection
- reranking
- page-aware generation-context selection
- shared retrieval behavior across local and cloud APIs
- guardrail refusal logic

It does **not** treat these as architecture changes, even though they were
important for the project:

- audited QA curation
- evaluator scoring logic
- benchmark expansion
- switching from one generation model to another

Those matter for measured performance, but they are not retrieval or serving
architecture changes in the narrow sense.

## 3. Summary Table

| Change | Main code insertion points | Why it helps | Example evidence |
|---|---|---|---|
| Shared retrieval stack for local and cloud APIs | `statschat/generative/cloud_llm.py`, `fast-api/main_api_local.py` | Removes hidden retrieval differences between API modes | GPT and Mistral cloud runs have identical retrieval metrics; local smoke run uses the same retriever |
| Report-family routing | `infer_query_report_families`, `_doc_report_families`, `Inquirer.retrieve_documents(...)` | Prevents unrelated report families from crowding out the right family before reranking | Family-routing run lifted expanded-benchmark Doc Hit@8 from `50/61` to `54/61` |
| Temporal candidate widening and precise edition selection | `parse_temporal_tokens`, `_doc_period_tokens`, `_select_precise_temporal_subset`, `_select_lagged_year_subset`, API `latest_filter` override | Helps month/quarter/year queries reach the correct edition instead of a recent but wrong report | QQ004, QQ061, and QQ070 are the clearest examples |
| Cross-encoder reranking and recency bias | `_get_reranker`, `_build_reranker_passage`, `_rerank_results`, `_apply_recency_bias(...)` | Improves ordering beyond raw FAISS similarity, especially among near-duplicate reports | Best GPT run: FAISS proxy Doc Hit@8 `46/61`; pipeline Doc Hit@8 `56/61` |
| Page-aware generation-context selection | `select_generation_contexts(...)`, `_expand_doc_local_candidates(...)`, `_rank_generation_page_shortlist(...)`, `_refine_generation_context_pages(...)` | Improves the pages shown to the LLM without destabilizing document ranking | Replaced the abandoned global page-injection approach |
| Query guardrails for unanswerable questions | `statschat/generative/query_policy.py`, cloud/local API entrypoints | Prevents hallucinated answers on out-of-scope queries | Correct refusal rate improved from `9/13` to `13/13` |

## 4. Shared Retrieval Stack Across Local And Cloud APIs

### What changed

The project previously had a meaningful retrieval split between cloud and local
API paths. During April 2026, the local API was changed to use the same shared
retrieval stack as the cloud API:

- `statschat/generative/cloud_llm.py`
  - `Inquirer.retrieve_documents(...)`
  - `Inquirer.select_generation_documents(...)`
- `fast-api/main_api_local.py`
  - calls `retriever.retrieve_documents(...)`
  - then `retriever.select_generation_documents(...)`

The cloud API continues to use the same `Inquirer` path through
`fast-api/main_api_cloud.py`.

### Why it helps

Before this change, local/cloud comparisons mixed together two variables:

- the generator model
- the retrieval implementation

That made it harder to tell whether a cloud/local difference came from the LLM
or from retrieval.

After this change, the intended difference is much cleaner:

- cloud API = shared retrieval + cloud generation
- local API = shared retrieval + local Hugging Face generation

### Why we think it worked

The strongest evidence is the clean GPT vs Mistral cloud comparison:

- GPT-5.4-mini cloud:
  - Pipeline Doc Hit@8 = `56/61`
  - Any Reference Page Hit = `39/61`
- Mistral Small 3.1 cloud:
  - Pipeline Doc Hit@8 = `56/61`
  - Any Reference Page Hit = `39/61`

The retrieval metrics are identical. The answerable-accuracy difference is
therefore attributable to generation quality, not retrieval.

The 15-row local smoke run also supports parity at a smaller scale:

- local Mistral smoke:
  - answerable accuracy = `12/15 = 0.800`
  - Pipeline Doc Hit@8 = `14/15 = 0.933`

This is not directly comparable to the full 74-row cloud benchmark, but it does
show that local mode is now using the stronger retrieval stack rather than a
weaker legacy search path.

## 5. Report-Family Routing

### What changed

Report-family routing was inserted into the shared cloud retriever in
`statschat/generative/cloud_llm.py`:

- `infer_query_report_families(text)`
- `_doc_report_families(doc)`
- `apply_family_filter(...)` inside `Inquirer.retrieve_documents(...)`

The family matcher uses explicit report names and metric cues to infer likely
families such as:

- CPI bulletins
- Economic Survey
- KDHS
- Facts and Figures
- Statistical Abstract
- FinAccess
- Construction Input Price Indices
- Leading Economic Indicators

One important special case was added directly in
`infer_query_report_families(...)`:

- if `construction_input_price_indices` is inferred, remove
  `cpi_inflation`

That prevents a query containing “inflation rate” from being hijacked by the
general CPI family when it is really about construction inflation.

### Why it helps

FAISS similarity search is strong at retrieving semantically related material,
but large KNBS families often contain many near-duplicate reports. If the
candidate pool mixes multiple families before reranking, the right family may
never get a fair chance.

Family routing narrows the reranking pool to candidates from the same report
family whenever the query gives enough signal to do so.

### Why we think it worked

This was one of the clearest structural improvements on the expanded 74-row
benchmark.

Relevant benchmark movement:

- first expanded 74-row run:
  - answerable accuracy = `48/61 = 0.787`
  - Pipeline Doc Hit@8 = `50/61 = 0.820`
- family-routing expanded run:
  - answerable accuracy = `56/61 = 0.918`
  - Pipeline Doc Hit@8 = `54/61 = 0.885`

### Example wins

- `QQ053`, `QQ055`, `QQ057`, and `QQ064`
  - These rows came from newer document families that were under-represented in
    the original benchmark.
  - Before family recognition, the correct documents were often absent from the
    top 8.
  - After family routing, these rows became recoverable without broad
    retriever-wide retuning.

- `QQ061`
  - Query type: construction inflation
  - Failure mode: “inflation rate” initially pulled the CPI family instead of
    the Construction Input Price Indices family.
  - Fix: construction family recognition now explicitly overrides the generic
    CPI family cue.

## 6. Temporal Candidate Widening And Edition Selection

### What changed

Temporal logic now influences retrieval in several places.

Shared token parsing:

- `statschat/generative/query_policy.py`
  - `parse_temporal_tokens(...)`
  - `has_temporal_constraint(...)`

Shared cloud retriever logic:

- `statschat/generative/cloud_llm.py`
  - `_doc_temporal_tokens(doc)`
  - `_doc_period_tokens(doc)`
  - `_doc_matches_query_temporal(...)`
  - `_select_precise_temporal_subset(...)`
  - `_select_lagged_year_subset(...)`
  - `retry_wider_temporal_pool(...)` inside `Inquirer.retrieve_documents(...)`

API layer behavior:

- `fast-api/main_api_cloud.py`
- `fast-api/main_api_local.py`

Both APIs now override `latest_filter` when a query carries an explicit year,
month, or quarter. This prevents the latest-only FAISS store from silently
dropping the historical report needed to answer a dated query.

### Why it helps

KNBS reports often have two different time signals:

- the publication date
- the period of data reported inside the publication

Those are not the same thing. A Q4 2023 report may be published in 2024. If the
retriever only trusts publication date, it can return the wrong edition for a
month- or quarter-specific question.

The new logic improves this in three ways:

1. It parses explicit query time tokens.
2. It prefers title/URL period tokens over publication date when identifying a
   report edition.
3. It widens the candidate pool when a narrow first pass misses the right
   historical edition.

### Why we think it worked

The benchmark showed multiple temporal-edition wins, especially on report
families with monthly, quarterly, or annual-lagged editions.

### Example wins

- `QQ004`
  - Query asked for the April 2025 CPI figure.
  - Earlier retrieval missed the correct monthly bulletin.
  - After family recognition and temporal retry logic, the right April 2025 CPI
    report was retrieved and the row became correct.

- `QQ061`
  - Query asked about construction inflation in Q4 2024.
  - A construction report for Q4 2023 published in 2024 can look deceptively
    similar if publication date is trusted too heavily.
  - `_doc_period_tokens(...)` fixes this by using the report period in the
    title/URL before falling back to publication date.

- `QQ070`
  - Leading Economic Indicators are a lagged publication family.
  - The best interpretation for “August 2023” is often the August 2024
    publication containing August 2023 data.
  - `_select_precise_temporal_subset(...)` contains a family-specific
    year+1 preference for this case.
  - In the final benchmark, this row still had an evaluator/unit-formatting
    issue, but retrieval reached the correct report and number.

## 7. Cross-Encoder Reranking And Recency Bias

### What changed

The shared retriever now reranks FAISS candidates with a cross-encoder:

- `statschat/generative/cloud_llm.py`
  - `_get_reranker(...)`
  - `_build_reranker_passage(doc)`
  - `_rerank_results(...)`

The reranker output is then combined with a year-aware recency bias:

- `_apply_recency_bias(...)`

There is also a legacy local retrieval path in
`statschat/generative/local_llm.py::similarity_search(...)` that uses a
cross-encoder, but the main architectural change for serving accuracy was
moving the live local API over to the shared `Inquirer` retriever.

### Why it helps

Bi-encoder FAISS search is good for recall, but not always for ranking the best
edition or best evidence chunk at the top. Cross-encoder reranking gives the
retriever a stronger second pass over a smaller candidate pool.

The recency bias helps with yearless or latest-oriented queries without
removing historical answers from consideration when the query is explicitly
temporal.

### Why we think it worked

The clearest evidence is the gap between raw FAISS-proxy performance and final
pipeline retrieval performance in the best GPT run:

- FAISS Proxy Doc Hit@8 = `46/61 = 0.754`
- Pipeline Doc Hit@8 = `56/61 = 0.918`

That 10-row difference is too large to attribute to LLM synthesis. It shows
that the retrieval pipeline is adding substantial value beyond raw vector
similarity.

## 8. Page-Aware Generation-Context Selection

### What changed

Page selection is now handled in a document-aware way instead of a global
page-pool injection approach.

Main insertion points:

- `statschat/generative/cloud_llm.py`
  - `select_generation_contexts(...)`
  - `_expand_doc_local_candidates(...)`
  - `_rank_generation_page_shortlist(...)`
  - `_refine_generation_context_pages(...)`

### Why it helps

Document retrieval and page retrieval are related but not identical.

Two things are needed at once:

- keep the right report family and right document near the top
- show the LLM the strongest pages from that already-correct document

The current design preserves document ranking first and only improves pages
inside the already selected documents. This is safer than flooding the global
ranking with many pages from one document.

### Why we think it worked

The team explicitly tried an earlier alternative and rejected it:

- global page injection improved some page-hit metrics
- but it damaged document ranking
- overall accuracy did not improve reliably

The current page-aware design was kept because it preserves document retrieval
while still improving the evidence pages shown to the model.

### Example

If a report family is correct but the first retrieved chunk lands on a summary
page rather than the table page that contains the answer, the current retriever
can pull neighboring pages or rerank a within-document shortlist and swap in
better pages from the same report. That improves grounding without changing
which report family won retrieval.

## 9. Guardrail Refusal Policy

### What changed

The out-of-scope refusal logic was extracted into shared query-policy code:

- `statschat/generative/query_policy.py`
  - `guardrail_refusal_reason(...)`
  - `parse_temporal_tokens(...)`
  - `has_temporal_constraint(...)`

Cloud wrappers remain available in `statschat/generative/cloud_llm.py`, but the
main policy logic now lives in the shared query-policy module.

The refusal rules cover:

- non-Kenya / cross-country unsupported questions
- policy advice
- subjective judgement
- unsupported topics
- future or unpublished statistics

### Why it helps

These queries should not be answered from the KNBS corpus. Without an explicit
policy, the system tends to behave like a general assistant and can fabricate
numbers or advice.

### Why we think it worked

The guardrail benchmark provides the clearest before/after evidence:

- first 50-row guardrail run:
  - correct refusals = `9/13`
  - false answers = `4/13`
- later guardrail-fixed run:
  - correct refusals = `13/13`
  - false answers = `0/13`

This is one of the cleanest measured wins in the entire project because the
before/after behavior is so easy to interpret.

### Example

Out-of-country or policy/opinion questions such as:

- “What was Tanzania’s GDP growth rate in 2023?”
- “Should Kenya reduce interest rates to control inflation?”

should now be refused rather than answered from guessed or external material.

## 10. What Worked, What Did Not, And Why

### Changes that clearly improved the system

- shared retrieval stack across API modes
- report-family routing
- temporal edition handling
- cross-encoder reranking
- page-aware within-document refinement
- shared guardrail refusal policy

### Changes that were useful for measurement, but are not architecture

- audited QA curation
- unanswerable-row authoring
- evaluator improvements
- live API model provenance capture

### Changes that were deliberately not kept

- global page injection into the overall ranking pool

It improved some page metrics but weakened document ranking. The retained
architecture is intentionally more conservative: fix the family, fix the
edition, rerank the right candidates, then improve pages inside the winning
documents.

## 11. How To Read Accuracy Gains Correctly

This document should not be used to make the claim that “architecture alone”
produced the final headline score.

The clean reading is:

1. early measured system state was weak
2. architecture and guardrail changes materially improved retrieval and refusal
   behavior
3. benchmark expansion exposed overfitting risk and forced better retrieval
4. GPT-5.4-mini still outperformed Mistral Small 3.1 on answer synthesis even
   with the same retrieval metrics

So the final production-facing improvement came from:

- stronger retrieval architecture
- stronger guardrails
- stronger benchmark/evaluator discipline
- stronger cloud generation model

## 12. Practical Recommendation

If a future engineer wants to understand or extend the April 2026 work, the
best order is:

1. read this document
2. read `docs/reports/2026-04-statschat-ke-testing-accuracy-report.md`
3. inspect `tests/accuracy/README.md`
4. inspect `statschat/generative/cloud_llm.py`
5. inspect `statschat/generative/query_policy.py`
6. inspect `fast-api/main_api_local.py` and `fast-api/main_api_cloud.py`

That path gives the most complete picture of:

- what changed
- where it changed
- why the changes were expected to help
- and what evidence suggested they did help
