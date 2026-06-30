# Recommendations overview

## Purpose

This note gives the short version of the recommended future direction for StatsChat-KE.

For most readers, this file plus [`01b-docling-trial-for-ingestion.md`](01b-docling-trial-for-ingestion.md) is enough to understand the immediate next step. The longer rationale is in [`background/detailed-rationale-and-research-notes.md`](background/detailed-rationale-and-research-notes.md).

## Main recommendation

StatsChat should continue to develop as a **retrieval-first evidence assistant** for KNBS publications. Its value is not that it is a general chatbot, but that it helps users find relevant KNBS evidence and produce an answer that can be checked against official sources.

The immediate development priority is:

> **Improve PDF processing by trialling Docling as a structured PDF-to-JSON/Markdown converter, with light StatsChat-specific post-processing, before making major retrieval changes.**

## Why this is first

The current repo already has a reasonably advanced retrieval pipeline. It includes dense search, report-family routing, temporal handling, cross-encoder reranking and page-aware context selection. Retrieval may still be improved, but it is not the obvious place to start with a broad rewrite.

PDF processing is the more likely bottleneck. KNBS reports often contain tables, charts, multi-column layouts, scanned pages, footnotes, units and dates. If these are lost during extraction, the retrieval and generation steps cannot reliably recover them.

## First practical experiment

Run the same 15–25 representative KNBS PDFs through three paths:

1. the current PyMuPDF / targeted `pdfplumber` pipeline;
2. Docling output directly;
3. Docling output after a thin StatsChat-specific post-processing layer.

For each path, compare:

- whether headings and reading order are preserved;
- whether tables remain readable and complete;
- whether row labels, column labels, units and notes stay attached to values;
- whether source document, page, section and table references are preserved;
- whether retrieval finds better evidence for known benchmark questions;
- whether generated answers improve without adding unacceptable complexity.

Adopt Docling only if it improves evidence quality and remains easy to run, inspect and debug. If results are mixed, keep the current parser as the default and consider using Docling selectively for difficult PDFs.

## What comes after the Docling trial

Once the ingestion comparison has been run, use the results to decide the next work:

| If the trial shows... | Then... |
|---|---|
| Docling improves tables, headings and retrieval evidence | Build a fuller Docling-to-StatsChat processing route and test on the whole corpus. |
| Docling helps only on some report types | Use it selectively for difficult PDFs and keep the current parser as the default. |
| Docling does not improve evidence quality | Keep the current parser and trial Marker or another structured converter. |
| Structured metadata improves retrieval | Test metadata-aware retrieval and table-aware chunks. |
| Retrieval still misses correct evidence after better ingestion | Run targeted retrieval experiments such as hybrid search, query rewriting or reranker tuning. |

## Supporting priorities

### Data preparation

Create canonical structured JSON as the durable ingestion output, with Markdown derived from it for inspection and LLM context. Preserve page numbers, report metadata, headings, tables, units, dates, footnotes and quality flags.

### Retrieval

Protect the current retrieval baseline. After structured ingestion improves the evidence objects, test targeted retrieval improvements rather than replacing the whole stack.

### Generation

Pass the LLM compact, citation-ready evidence packs rather than noisy page text. Keep grounded answering, refusal behaviour and structured output.

### Evaluation

Use the existing audited benchmark as the control mechanism. Add ingestion and retrieval diagnostics so failures can be assigned to the right stage.

## Suggested priority order

1. Reproduce the current benchmark baseline.
2. Select a representative PDF sample set.
3. Trial Docling against the current parser.
4. Add light StatsChat post-processing to Docling output.
5. Compare extraction quality, retrieval quality and answer quality.
6. Decide whether and how to adopt Docling.
7. Test retrieval improvements using the improved evidence objects.
8. Tighten generation context packaging.
9. Expand evaluation using real internal-pilot questions.
