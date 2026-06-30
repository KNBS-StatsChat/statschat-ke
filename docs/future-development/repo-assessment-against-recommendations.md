# Repo assessment against the recommendations

> **Context**: This note explains why the repo-facing recommendations prioritise PDF processing over a broad retrieval rewrite. The current repo already has a stronger retrieval baseline than the original high-level recommendations assumed.

This note records how the recommendations should be adjusted after reviewing the current StatsChat-KE repository.

## Summary

The overall recommendations still stand, but the current repo is further along than the broad recommendations might imply. In particular, retrieval has already been substantially improved. The most important adjustment is therefore:

> Treat retrieval as a strong baseline to measure against, not as a component that obviously needs a rewrite. Put the largest near-term effort into PDF processing, structured evidence, table handling and ingestion-quality diagnostics.

## What the repo already does well

### PDF processing

The current pipeline already:

- crawls KNBS report pages and stores PDF/report-page provenance in `url_dict.json`;
- extracts metadata from KNBS report pages where possible;
- converts PDFs into JSON with document metadata and page-level content;
- uses PyMuPDF as the default extractor;
- includes targeted `pdfplumber` fallback/preference for known problematic families;
- records page numbers and page URLs;
- has investigations and tests around missing downloads, MuPDF warnings and extraction failures.

This means the recommendation should not be “add PDF processing from scratch”. It should be “move from page-level plain text toward structured evidence conversion and quality-controlled extraction”.

### Chunking, embedding and indexing

The repo already:

- splits JSON into page-level records;
- enriches page text with title, date, theme/type and page number before chunking;
- uses `RecursiveCharacterTextSplitter` with configurable length and overlap;
- uses `sentence-transformers/all-mpnet-base-v2` in the current config;
- stores chunks in FAISS;
- supports a latest/update flow and a latest vector store.

The recommendations should therefore focus on evidence-unit chunking, table-aware chunks and benchmarked chunk-size experiments, not simply “add chunking”.

### Retrieval

The repo already has a strong retrieval stack:

- dense FAISS retrieval;
- separation of `k_docs` from `k_contexts`;
- report-family routing;
- temporal parsing and candidate widening;
- specific handling for month/quarter/year queries;
- cross-encoder reranking;
- recency bias;
- page-aware generation-context refinement;
- deduplication and candidate expansion;
- guardrails for some out-of-scope query types.

This changes the recommendation from “introduce reranking and temporal handling” to “evaluate whether hybrid search, stronger metadata and table-aware retrieval improve the remaining failures beyond this baseline”.

### Generation and evaluation

The repo already includes:

- cloud and local generation paths, with cloud as the practical primary path;
- grounded prompts;
- Pydantic response parsing;
- answer/highlighting fields;
- source/reference handling;
- audited benchmark data;
- evaluation scripts and run artifacts;
- documentation describing benchmark discipline and maintenance.

The recommendations should therefore focus on strengthening evidence packs, logging prompt/index versions, improving refusal templates and expanding the benchmark from real usage.

## Recommendations that should be softened or reworded

### 1. “Add reranking”

Reword as:

> Cross-encoder reranking already exists. Future work should evaluate reranker alternatives, tune candidate pools, and make reranker/page-selection traces easier to inspect.

### 2. “Add latest handling”

Reword as:

> Latest and temporal handling already exists through latest indexes, recency weighting, temporal parsing and edition selection. Future work should formalise reference-period metadata during ingestion so this logic relies less on filenames, titles and regex rules.

### 3. “Replace FAISS/vector store”

Reword as:

> FAISS exact search is adequate for the current corpus size. A vector-store replacement is not a near-term priority unless maintainers need stronger metadata filtering, hybrid search integration, concurrent serving, or operational tooling.

### 4. “Use hybrid search”

Reword as:

> Hybrid retrieval is a worthwhile experiment, especially for exact statistical terms, table labels, acronyms, counties and dates. It should be evaluated against the current dense + routing + reranking baseline before adoption.

### 5. “Add structured output”

Reword as:

> Structured output already exists through `LlmResponse`. Future work should extend the output contract to include evidence status, assumptions, warnings, citation metadata and trace/debug fields.

### 6. “Add evaluation”

Reword as:

> Evaluation already exists and is one of the strongest parts of the repo. Future work should expand coverage, add failure labels by pipeline stage, and make evaluation mandatory for release-impacting changes.

## Recommendations that become stronger after repo review

### 1. Structured PDF conversion is the clearest gap

The current JSON stores page text, but not a full structured representation of layout, tables, headings, captions, cells, OCR confidence, bounding boxes or extraction method. This is the main area where a new tool such as Docling, Marker, PyMuPDF4LLM, LlamaParse or a cloud document-intelligence service could be tested.

### 2. Table-first evidence objects are needed

Many KNBS answers depend on tables. The next ingestion schema should be able to represent tables as evidence objects with titles, pages, row/column labels, units, notes and Markdown renderings. Plain page text is often insufficient.

### 3. Metadata should move upstream

The retrieval code currently compensates with family routing, temporal parsing and title/date cues. More of this should be captured during ingestion as canonical metadata: report family, publication date, reference period, geography, series, evidence type and table ID.

### 4. Documentation should be updated

Some architecture docs lag behind the code. For example, the retrieval documentation should be reviewed against the current implementation because the repo now includes cross-encoder reranking, temporal routing and page-aware context selection. Future-development docs should avoid the old “phase” naming and use workstreams instead.

## Practical conclusion

The current recommendations do not need to be reversed. They need to be made more repo-aware:

1. Preserve the current retrieval/evaluation baseline.
2. Treat PDF processing and structured evidence as the highest-priority improvement area.
3. Run targeted retrieval experiments only where they can beat the current baseline on known failure cases.
4. Keep FAISS and the current embedding model unless evaluation shows a reason to change.
5. Make all changes benchmark-led and traceable.
