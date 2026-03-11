# Phase 2: Retrieval

This file tracks future ideas for improving retrieval quality in the StatsChat-KE pipeline.

## Scope

- Embeddings
- Chunking and overlap strategy
- FAISS indexing
- Similarity search
- Reranking and recency weighting
- Context selection before generation

## Candidate Improvements

- Revisit chunk size and overlap choices for KNBS tables, summaries, and long-form narrative sections.
- Compare alternative embedding models for factual retrieval quality and cost.
- Introduce targeted evaluation sets for retrieval accuracy on known statistical questions.
- Explore better reranking for time-sensitive questions, especially latest bulletin and quarter-specific queries.
- Record retrieval misses where relevant documents exist but are not surfaced in the top results.

## Questions to Explore

- Are current chunk boundaries causing answers to miss critical numeric context?
- Should retrieval differ for definitions, time-series facts, and report-location questions?
- Would hybrid retrieval or metadata-aware filtering improve precision?

## Notes

Use this file to capture retrieval experiments, benchmark ideas, and known failure patterns.
