# Data preparation and PDF processing recommendations

## Immediate priority

The first development priority should be to trial **Docling plus light StatsChat-specific post-processing** as a route from KNBS PDFs to structured JSON and Markdown.

This is the simplest high-value improvement to test because it does not require replacing the retrieval or generation stack first. It asks a narrower question:

> Can we create better structured evidence from the same PDFs, then feed that evidence into the existing StatsChat pipeline?

If the answer is yes, later retrieval improvements will have better metadata and better chunks to work with. If the answer is no, the current parser remains the baseline and the team can test another structured converter.

See [`01b-docling-trial-for-ingestion.md`](01b-docling-trial-for-ingestion.md) for the practical trial plan.

## Current baseline

The current pipeline already has a functioning data-preparation flow:

1. crawl KNBS report pages;
2. download linked PDFs;
3. store source/report-page provenance in `url_dict.json`;
4. extract page text using PyMuPDF, with targeted `pdfplumber` fallback/preference for known problematic families;
5. scrape report-page metadata where available;
6. create JSON files containing document metadata and page-level text;
7. split JSON into page-level records for downstream chunking and indexing.

This is a solid baseline. The next improvement should not be “add PDF extraction”, but “make PDF extraction structured, auditable and table-aware”.

## Core recommendation

Move from **PDF → page text** toward **PDF → structured evidence**.

A suggested target flow is:

```text
PDF/report attachment
→ document/page classification
→ Docling structured conversion trial
→ StatsChat post-processing
→ canonical JSON
→ derived Markdown
→ evidence chunks
→ retrieval index
```

The canonical JSON should be the durable source of truth. Markdown should be derived from JSON for LLM-readable context and human inspection.

## Why Docling first?

Docling should be the first serious parser trial because it appears to match the project constraints well:

- open source and locally runnable;
- designed for document conversion and AI/RAG workflows;
- supports PDF input;
- exports Markdown and lossless JSON;
- represents documents in a unified structured format;
- has examples and integrations relevant to RAG workflows.

This does **not** mean Docling should be adopted without testing. Statistical PDFs are difficult: complex tables, repeated page furniture, footnotes, charts and cross-page layouts can still need custom handling. The recommendation is to test Docling against the current pipeline and adopt it only if it improves evidence quality on real KNBS examples.

## Why StatsChat-specific post-processing is still needed

A generic converter will not know what StatsChat needs from KNBS publications. Add a thin post-processing layer to transform Docling output into StatsChat-ready evidence.

The first version should focus on:

- preserving source URL, PDF URL, document title and page number;
- attaching section headings to the paragraphs/tables beneath them;
- converting tables into both Markdown and structured JSON where possible;
- attaching table titles, units, notes, geography and reference periods when available;
- removing repeated headers, footers and page furniture where they create retrieval noise;
- assigning stable evidence IDs;
- flagging pages with low text, OCR use, extraction errors or table-like content with no detected table;
- producing chunk-ready Markdown and metadata for the existing retrieval pipeline.

Avoid over-engineering the first version. The first aim is to prove whether structured conversion materially improves retrieved evidence.

## Recommended canonical JSON fields

The next schema should preserve more than `page_text`. Suggested fields include:

### Document-level fields

- `document_id`
- `report_page_url`
- `pdf_url`
- `local_filename`
- `title`
- `report_family`
- `theme`
- `release_type`
- `publication_date`
- `reference_period`
- `source_organisation`
- `ingestion_run_id`
- `parser_name`
- `parser_version`
- `parser_config`
- `extraction_quality_summary`

### Page-level fields

- `page_number`
- `page_url`
- `page_text`
- `markdown`
- `headings`
- `detected_tables`
- `detected_figures`
- `ocr_used`
- `text_char_count`
- `quality_flags`

### Evidence-object fields

Each page should be able to contain evidence objects such as prose blocks, tables, figures and footnotes:

- `evidence_id`
- `evidence_type`: `prose`, `table`, `figure`, `footnote`, `caption`, `heading`
- `page_number`
- `section_heading`
- `table_title`
- `table_number`
- `caption`
- `unit`
- `geography`
- `reference_period`
- `markdown`
- `plain_text`
- `table_json`, where applicable
- `bbox` if available
- `quality_flags`

## Tables should be first-class evidence

Many KNBS questions depend on table values. Tables should not only be flattened into page text.

For each extracted table, try to preserve:

- table title and number;
- page number and source URL;
- surrounding heading/section;
- column labels;
- row labels;
- units and footnotes;
- reference period;
- geography;
- a Markdown rendering for LLM context;
- a structured representation for validation and future retrieval.

A table may need two retrieval representations:

1. a compact table summary for search and reranking;
2. a fuller table rendering for generation once selected.

## Page classification and extraction routing

Not every PDF page should be treated the same. Add a lightweight page/document classifier before extraction routing:

| Page/document type | Suggested handling |
|---|---|
| Born-digital prose | Current parser or Docling output may be sufficient. |
| Table-heavy pages | Prefer structured conversion and compare with targeted table extractors. |
| Scanned pages | OCR stage or Docling OCR configuration before indexing. |
| Image/chart-heavy pages | Extract captions and surrounding text; flag chart-only evidence where values are not machine-readable. |
| Problematic pages | Put in review queue with quality flags and keep parser diagnostics. |

## Candidate tool approach

Do not choose a new parser by reputation alone. Start with a narrow comparison:

| Role | Candidate tools |
|---|---|
| Current baseline | Existing PyMuPDF + targeted `pdfplumber`. |
| First structured-conversion trial | Docling. |
| Comparison candidate if time permits | Marker. |
| Targeted table repair | `pdfplumber`, Camelot, Tabula where appropriate. |
| Scan/OCR stage | OCRmyPDF, Tesseract-based workflows, or Docling OCR options. |
| Hosted benchmark/fallback | LlamaParse, Mistral OCR/Document AI, Azure AI Document Intelligence, Google Document AI. |
| Human QA/exploration only | NotebookLM or similar tools. |

The recommended starting point is to compare the current parser against Docling on the same PDFs. Marker and hosted tools can be added if Docling results are mixed or if a benchmark/fallback is needed for difficult reports.

## Bake-off evaluation criteria

Score each candidate on:

- reading order;
- page numbering and page URL preservation;
- heading and section detection;
- table title preservation;
- row/column label preservation;
- cross-page tables;
- footnotes and units;
- OCR handling;
- Markdown readability;
- JSON usefulness;
- reproducibility and batch reliability;
- speed and cost;
- improvement on existing benchmark failures.

A good parser is not just one that produces attractive Markdown. It must produce evidence that improves retrieval and answer accuracy.

## Extraction-quality checks

Add ingestion run reports that flag:

- PDFs that failed to download;
- non-PDF responses saved as PDFs;
- zero-byte or very small PDFs;
- pages with very low extracted text;
- pages with suspicious character noise;
- pages where OCR was used;
- pages with many numeric values but no detected table structure;
- documents missing publication date or source URL;
- documents whose extracted title/date conflicts with report-page metadata.

These checks should produce a review queue before re-indexing.

## Practical next steps

1. Choose 15–25 representative KNBS PDFs, including known extraction failures.
2. Define a minimal canonical JSON/evidence schema.
3. Run the current parser and Docling on the same sample set.
4. Add light StatsChat-specific post-processing to Docling output.
5. Manually review table-heavy and scanned cases.
6. Re-index a small test corpus from current output and Docling-derived output.
7. Run retrieval and answer evaluation using known benchmark questions.
8. Adopt Docling only if it improves evidence quality without unacceptable operational complexity.
9. Keep the current parser as a fallback until the new route has been tested on the full corpus.

## Links to existing repo material

- `statschat/pdf_processing/pdf_downloader.py`
- `statschat/pdf_processing/pdf_to_json.py`
- `statschat/embedding/preprocess.py`
- `docs/architecture/pipeline-pdf-ingestion.md`
- `docs/investigations/2026-02-04-missing-downloads-and-mupdf-extraction-errors.md`
- `docs/investigations/2026-04-08-pdf-extraction-vs-page-recall-on-cloud-failures.md`
- `tests/unit/pdf_processing/`
- `tests/integration/test_pdf_pipeline_e2e.py`
