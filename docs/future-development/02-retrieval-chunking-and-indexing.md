# Retrieval, chunking and indexing recommendations

> **When to use this file**: Treat the current retrieval system as the baseline. Start major retrieval experiments after the Docling/structured-ingestion trial has shown what metadata and evidence objects are available.

## Current baseline

The current repo already has a relatively strong retrieval pipeline. It includes:

- page-level JSON loading;
- metadata prefixes before chunking;
- configurable chunk length and overlap;
- `sentence-transformers/all-mpnet-base-v2` embeddings in the current config;
- FAISS storage;
- latest and full indexes;
- dense similarity search;
- report-family routing;
- temporal parsing and candidate widening;
- cross-encoder reranking;
- recency bias;
- `k_docs` / `k_contexts` separation;
- page-aware context selection for generation;
- retrieval metrics in the accuracy workflow.

This is not a simple dense-only RAG implementation. Future retrieval changes should therefore be evaluated against this baseline rather than assumed to be improvements.

## Core recommendation

Keep the current retrieval stack as the baseline, improve the evidence it retrieves, and test targeted enhancements only after the structured-ingestion trial gives the system better metadata and evidence chunks.

The biggest near-term retrieval gains are likely to come from better ingestion metadata and table-aware chunks, not from replacing FAISS, swapping embedding models, or rewriting retrieval from scratch.

## Chunking recommendations

The current system chunks page text by character length. This is simple and works reasonably well, but it can split statistical evidence away from its context.

Future chunking should be based on evidence units where possible:

| Chunk type | Purpose |
|---|---|
| Page chunk | Good fallback and useful for page-level citation. |
| Section chunk | Good for prose explanations and definitions. |
| Table chunk | Necessary for numeric values, row/column labels and units. |
| Table-summary chunk | Useful for retrieval when the full table is too large. |
| Parent document chunk | Useful for report-family and edition selection. |

A useful approach is parent-child retrieval:

1. search over small evidence chunks;
2. rerank candidate chunks;
3. assemble a larger parent context such as the full table, surrounding page, or neighbouring pages for generation.

## Metadata recommendations

Add or strengthen metadata fields that can be used for filtering, boosting and explanation:

- `document_id`
- `chunk_id`
- `evidence_id`
- `report_family`
- `publication_date`
- `reference_period`
- `page_number`
- `section_heading`
- `table_id`
- `table_title`
- `evidence_type`
- `geography`
- `unit`
- `source_url`
- `parser_name`
- `index_version`

Some metadata should also be included in the chunk text because embedding models cannot search fields they never see. The current repo already prepends title/date/theme/page metadata; extend that idea carefully for table and evidence-object chunks.

## Embedding recommendations

Do not change the embedding model casually. The current `all-mpnet-base-v2` setup is a reasonable baseline and the corpus is not large.

Future embedding work should be benchmarked as experiments:

- current model vs a modern retrieval embedding model;
- generic embeddings vs table-aware/context-enriched chunk text;
- raw chunks vs metadata-prefixed chunks;
- full-page chunks vs evidence-unit chunks;
- current chunk length/overlap vs smaller/larger options.

A model swap is only worth adopting if it improves retrieval and answer metrics on the audited benchmark and known failure cases.

## Vector-store recommendations

FAISS exact search is probably adequate for the current corpus size. Replacing it is not an immediate priority.

Consider a different vector/search store only if the project needs:

- stronger metadata filtering;
- integrated hybrid search;
- multi-user/concurrent production operation;
- easier index versioning and deployment;
- hosted operational tooling;
- larger future corpora.

Possible future options include Qdrant, Weaviate, OpenSearch/Elasticsearch, Postgres/pgvector or a managed search service. For now, the priority should be retrieval quality, not infrastructure churn.

## Hybrid retrieval recommendation

Hybrid retrieval remains worth testing, especially for KNBS questions involving:

- exact table labels;
- acronyms such as CPI, GVA or KDHS;
- county names;
- dates and reference periods;
- unusual commodity names or sector labels;
- exact phrases from tables.

A safe experimental flow is:

```text
query
→ dense FAISS candidates
→ lexical/BM25 candidates
→ metadata candidates
→ merge/deduplicate
→ cross-encoder rerank
→ select k_docs
→ select k_contexts/evidence pack
```

Do not adopt hybrid search until it beats the current dense + routing + reranking stack on agreed metrics.

## Latest and temporal retrieval

The repo already includes advanced temporal handling. The next improvement is to move temporal information upstream into ingestion metadata.

Recommended additions:

- distinguish publication date from reference period;
- record month, quarter and year fields explicitly where possible;
- identify report edition separately from data period;
- label report families with known lag behaviour, such as annual reports describing the previous year;
- add test cases for “latest”, “in 2024”, “February 2025”, “Q3 2023” and similar questions.

This should reduce dependence on filename/title parsing and hard-coded temporal heuristics.

## Retrieval traceability

Make it easy for maintainers to inspect retrieval behaviour for a query.

A useful trace should show:

- original query;
- query rewrite/interpretation if any;
- latest/content-type setting;
- candidate counts;
- filters applied;
- top dense candidates;
- top lexical candidates if hybrid search is used;
- report-family matches;
- temporal matches;
- reranker scores;
- selected `k_docs`;
- selected `k_contexts`;
- final evidence pack passed to the LLM.

This should be available in logs or an evaluator/debug output, not necessarily in the public UI.

## Practical next experiments

1. Run the current benchmark and save the baseline run.
2. Label current retrieval failures by type: wrong family, wrong edition, right document wrong page, table not extracted, generation failure.
3. Test evidence-unit/table chunks on a small re-indexed subset.
4. Test hybrid retrieval against the current retrieval stack.
5. Test a reranker alternative only after candidate generation is stable.
6. Compare using document hit@k, page hit@k, answer accuracy, false-answer rate and missing-answer rate.

## Links to existing repo material

- `statschat/embedding/preprocess.py`
- `statschat/generative/cloud_llm.py`
- `statschat/generative/query_policy.py`
- `docs/architecture/pipeline-embedding.md`
- `docs/architecture/pipeline-retrieval.md`
- `docs/architecture/2026-04-accuracy-architecture-changes.md`
- `docs/guides/latest_filtering.md`
- `tests/accuracy/README.md`
