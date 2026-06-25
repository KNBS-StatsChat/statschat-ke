# Trial Docling for StatsChat PDF ingestion

> **First action**: This is the first practical future-development task recommended for StatsChat. Run this trial before making major retrieval, embedding or generation changes.

## Purpose

This note gives the practical first experiment for improving StatsChat PDF processing. It is the recommended starting point for future development because it can improve the evidence available to the existing retrieval and generation system without requiring a broad rewrite. It should be read alongside [`01-data-preparation-and-pdf-processing.md`](01-data-preparation-and-pdf-processing.md).

## Decision

The recommendation is to trial **Docling** as the first focused improvement to the current PDF-to-text extraction approach in the original StatsChat Kenya project.

The recommended approach is:

1. Use **Docling** to convert KNBS PDFs into structured document outputs.
2. Export both **Markdown** and **JSON**.
3. Add a thin layer of **StatsChat-specific post-processing** to clean, normalise and enrich the outputs before chunking and embedding.
4. Evaluate the result against a small set of real StatsChat questions and known difficult PDFs before adopting it as the default ingestion route.

This should be treated as a practical trial, not an immediate full migration. The decision after the trial may be to adopt Docling as the default parser, use it selectively for difficult PDFs, compare it with another tool, or keep the current parser.

## Why this decision

StatsChat's main weakness is not simply that PDFs are hard to read. It is that statistical PDFs contain structure that matters: headings, tables, footnotes, page references, captions, publication metadata and sometimes multi-column layouts. A plain text extractor can lose this structure, which then weakens retrieval and makes generated answers less reliable.

Docling is a good first candidate because it is:

- **Open source and locally runnable**, reducing dependency on a hosted API.
- Designed for **document conversion for AI/RAG workflows**.
- Able to process PDFs into a richer document representation rather than plain text only.
- Able to export to both **Markdown** and **JSON**.
- Relevant for common StatsChat needs such as layout, reading order, tables and OCR handling.

This makes Docling a strong fit for a maintainable StatsChat pipeline: it can improve extraction quality while still allowing the team to keep control over the processing logic.

The key point is that Docling should not be used as a magic black box. It should produce a better structured base output, and StatsChat should then apply project-specific rules to make that output suitable for retrieval.

## Why custom post-processing is needed

Even a better parser will not know what StatsChat needs from KNBS publications. Custom post-processing should turn Docling's general document output into a StatsChat-specific ingestion format.

This post-processing should aim to:

- remove repeated headers, footers and page furniture where they create retrieval noise;
- preserve page numbers and document-level metadata;
- keep section headings attached to the text and tables beneath them;
- identify tables, table titles, captions and notes;
- mark content type, such as `paragraph`, `table`, `figure_caption`, `metadata` or `appendix`;
- produce cleaner Markdown for chunking;
- store structured JSON for traceability and future evaluation;
- flag low-confidence or unusual pages for manual review.

For example, a useful StatsChat chunk should not just contain text. It should also know which PDF it came from, which page, which section, and whether it represents prose, a table or a figure caption.

## How to do this

### 1. Select a small test set

Choose around 15–25 representative KNBS PDFs, including:

- a recent CPI report;
- an Economic Survey report;
- a Statistical Abstract or equivalent large report;
- a PDF with complex tables;
- a PDF with multi-column layout;
- one or two older or lower-quality PDFs;
- any documents already known to cause StatsChat retrieval or answer errors.

The goal is to test realistic difficulty, not just easy examples.

### 2. Run Docling on the test PDFs

For each PDF, produce:

- Docling JSON output;
- Markdown output;
- any extracted table structures;
- page-level metadata where available.

Keep these outputs in a test directory so they can be inspected and compared with the current pipeline.

### 3. Define a simple StatsChat ingestion schema

Create a small JSON schema for processed content. For example:

```json
{
  "document_id": "economic-survey-2025.pdf",
  "title": "Economic Survey 2025",
  "page": 42,
  "section": "Prices",
  "content_type": "table",
  "text_markdown": "...",
  "table_json": {},
  "source": "KNBS",
  "processing_method": "docling_trial"
}
```

This schema does not need to be perfect at first. It just needs to be consistent enough for chunking, retrieval and evaluation.

### 4. Add custom post-processing

Implement a small post-processing script that takes Docling output and creates StatsChat-ready JSON and Markdown.

The first version should focus on:

- cleaning obvious repeated headers and footers;
- preserving section hierarchy;
- preserving page references;
- converting tables into both Markdown and structured JSON where possible;
- creating retrieval chunks with useful metadata.

Avoid over-engineering this stage initially. The first aim is to prove whether Docling materially improves the quality of retrieved evidence.

### 5. Compare against the current pipeline

Run the same PDFs through:

1. the current extraction pipeline;
2. Docling only;
3. Docling plus StatsChat post-processing.

Compare outputs manually and through a small retrieval test.

Useful checks include:

- Are headings and paragraphs in the right order?
- Are tables readable and complete?
- Are page references preserved?
- Are repeated headers and footers reduced?
- Does retrieval find better evidence for known benchmark questions?
- Are fewer irrelevant chunks retrieved?
- Are answers easier to cite back to the source PDF?

### 6. Decide whether to adopt

Adopt Docling as the default ingestion route only if it clearly improves retrieval evidence quality without creating unacceptable complexity.

A reasonable adoption rule would be:

> Use Docling if Docling plus light post-processing improves table/section preservation and retrieval quality on the test set, while remaining easy for maintainers to run and debug.

If the results are mixed, Docling could still be used selectively for difficult PDFs while the existing pipeline remains available as a fallback.

## Expected outcome

The expected benefit is a more reliable ingestion layer for StatsChat. Better structured PDF extraction should lead to:

- cleaner chunks;
- better retrieval;
- stronger citations;
- fewer hallucination risks caused by missing or scrambled evidence;
- easier debugging when answers are wrong;
- a clearer path to future evaluation of ingestion quality.

## Recommendation in one sentence

StatsChat should trial **Docling plus light StatsChat-specific post-processing** as the preferred next step for improving PDF ingestion, because it offers a practical, open-source route from messy statistical PDFs to structured, retrievable Markdown and JSON.

## References

- Docling homepage: https://www.docling.ai/
- Docling documentation: https://docling-project.github.io/docling/
- Docling supported formats: https://docling-project.github.io/docling/usage/supported_formats/
- Docling document converter reference: https://docling-project.github.io/docling/reference/document_converter/

---

## Suggested location in the pipeline

Docling should initially be added as an experimental alternative to the current `pdf_to_json` route, not as a direct replacement. A useful first implementation would be:

```text
statschat/pdf_processing/
├── pdf_to_json.py                 # current baseline
├── docling_to_json_trial.py        # experimental converter
├── postprocess_docling_output.py   # StatsChat-specific normalisation
└── extraction_quality_report.py    # parser comparison / warnings
```

The output should be compatible with downstream chunking only after the post-processing layer has added the StatsChat fields needed for retrieval and citation.
