# Future development recommendations

This folder gives practical next-step recommendations for StatsChat-KE. It is intended for maintainers and onboarding teams who need to understand what to work on next without reading the full project history.

## Start here

The immediate priority is:

> **Trial Docling for structured PDF-to-JSON/Markdown conversion, compare it against the current parser, and use the result to decide the next ingestion and retrieval changes.**

This does not mean rewriting the whole pipeline now. The current repo already has a working ingestion, retrieval, generation and evaluation pipeline. The recommended next step is a small, measured trial focused on better PDF structure: tables, headings, page references, units, dates, footnotes and metadata.

Read these first:

1. [`00-recommendations-overview.md`](00-recommendations-overview.md) — short overall direction.
2. [`repo-assessment-against-recommendations.md`](repo-assessment-against-recommendations.md) — how the recommendations map onto what the current repo already does. Read this early to avoid misreading the workstream files as "start from scratch" proposals.
3. [`01b-docling-trial-for-ingestion.md`](01b-docling-trial-for-ingestion.md) — the first practical experiment to run.
4. [`04-evaluation-and-monitoring.md`](04-evaluation-and-monitoring.md) — how to decide whether the trial improves StatsChat.

The other files give supporting detail.

## Why the first focus is PDF processing

The current retrieval stack is already relatively sophisticated: it includes dense FAISS search, report-family routing, temporal handling, cross-encoder reranking, recency bias and page-aware context selection. That should be protected as the baseline.

The clearest remaining bottleneck is likely earlier in the pipeline. If PDF extraction loses table structure, page references, units or reference periods, retrieval cannot reliably recover them later. Better structured ingestion should therefore come before major retrieval rewrites.

## Files in this folder

| File | How to use it |
|---|---|
| [`00-recommendations-overview.md`](00-recommendations-overview.md) | Short summary of the recommended direction and priority order. |
| [`01-data-preparation-and-pdf-processing.md`](01-data-preparation-and-pdf-processing.md) | Main data-preparation recommendation: move toward structured evidence, with Docling as the first trial. |
| [`01a-pdf-to-json-markdown-tool-options.md`](01a-pdf-to-json-markdown-tool-options.md) | Supporting comparison of PDF-to-JSON/Markdown tools. Useful background, not the first thing to implement. |
| [`01b-docling-trial-for-ingestion.md`](01b-docling-trial-for-ingestion.md) | **First action file.** Practical plan for the Docling ingestion trial. |
| [`02-retrieval-chunking-and-indexing.md`](02-retrieval-chunking-and-indexing.md) | Retrieval, chunking and indexing improvements to consider after the ingestion trial has produced better evidence objects. |
| [`03-generation-and-evidence-packaging.md`](03-generation-and-evidence-packaging.md) | How to package cleaner retrieved evidence for the LLM. |
| [`04-evaluation-and-monitoring.md`](04-evaluation-and-monitoring.md) | How to evaluate ingestion, retrieval, generation and answer quality before accepting changes. |
| [`repo-assessment-against-recommendations.md`](repo-assessment-against-recommendations.md) | **Read early.** Notes on how the recommendations were adjusted after reviewing the current repository. Explains what not to misread the workstream files as. |
| [`background/detailed-rationale-and-research-notes.md`](background/detailed-rationale-and-research-notes.md) | Long-form rationale and evidence base. Read this only when you need the full reasoning behind the shorter files. |

## Recommended first sequence

1. Preserve the current benchmark baseline and current parser output for comparison.
2. Select 15–25 representative KNBS PDFs, including known table/layout/scan failures.
3. Run the current parser on the sample set.
4. Run Docling on the same sample set and export JSON plus Markdown.
5. Add light StatsChat-specific post-processing for metadata, page references, headings, tables, stable IDs and quality flags.
6. Re-index the sample corpus and run retrieval/answer evaluation.
7. Decide whether Docling should become the default parser, a selective fallback, or not adopted.
8. Only after this, test retrieval changes such as hybrid search or stronger metadata filtering.

## Rule for future changes

Any change that could affect extracted content, chunks, retrieval order, context packaging, generation output, citations or indexed corpus contents should be tested against the audited benchmark before being accepted. See [`04-evaluation-and-monitoring.md`](04-evaluation-and-monitoring.md) and the repo's existing accuracy-test documentation.
