# PDF-to-JSON/Markdown tool options for StatsChat

> **Role of this file**: This is supporting background, not a prerequisite for starting work. It sits alongside `01-data-preparation-and-pdf-processing.md` and provides a broader tool comparison if Docling needs alternatives or fallback options. Start with [`01b-docling-trial-for-ingestion.md`](01b-docling-trial-for-ingestion.md) for the immediate practical first step.

## Purpose

This note supports the data-preparation recommendation in this folder. It explains why StatsChat should move toward a structured PDF conversion layer and lists candidate tools for a small evidence-led bake-off.

The immediate recommendation is to start with Docling as the first structured-conversion trial, while keeping the current parser as the baseline and using other tools as comparisons or fallbacks.

## Executive summary

For a StatsChat-style retrieval-augmented generation (RAG) system, the goal should not simply be to convert PDFs into plain text. The better goal is to create a **structured, auditable representation of each document** that preserves the things needed for retrieval and answer verification: reading order, sections, tables, captions, page references, document metadata, and ideally coordinates or bounding boxes.

A good practical approach would be to test several modern PDF parsing/document-understanding tools on a representative set of difficult statistical PDFs, then choose a pipeline based on measured performance rather than marketing claims.

For the current StatsChat use case — approximately **1,000 historical PDFs**, then perhaps **1–2 new PDFs per month** — the most promising approach is likely:

```text
Default open-source candidate: Docling or Marker
Cloud/RAG-oriented benchmark: LlamaParse, Mistral OCR, or similar
Enterprise benchmark: Azure AI Document Intelligence or Google Document AI
Exploration/manual QA: NotebookLM
```

NotebookLM may be useful for inspecting and understanding individual PDFs, but it should probably not be treated as the main ingestion pipeline for StatsChat.

---

## 1. Reframing the problem

The core problem is not just:

> “How do we convert PDFs into text?”

It is more like:

> “How do we convert statistical PDFs into structured, retrievable, citable evidence for a RAG system?”

This matters because many statistical PDFs contain:

- multi-column layouts;
- tables split across pages;
- table titles and notes;
- charts and figure captions;
- headers and footers;
- footnotes and caveats;
- scanned or semi-scanned pages;
- publication metadata;
- page numbers that need to be preserved for citations.

A simple text extractor may capture the words while losing the structure that makes those words useful.

---

## 2. Recommended target format

It is worth producing **both JSON and Markdown**, rather than choosing only one.

Markdown is useful because it is readable, easy to inspect, and convenient for LLM context. JSON is useful because it can preserve structure, provenance, metadata, tables, page references, and extraction confidence.

A useful pipeline might look like this:

```text
PDF
 ├── raw extracted assets
 │    ├── page images
 │    ├── embedded images
 │    └── OCR text, where needed
 ├── structured JSON
 │    ├── document metadata
 │    ├── pages
 │    ├── sections/headings
 │    ├── paragraphs
 │    ├── tables
 │    ├── figures/captions
 │    └── bounding boxes/page references
 └── derived Markdown
      ├── clean reading version
      ├── table markdown or HTML
      └── chunk-ready text
```

For RAG, the JSON should be treated as the more canonical representation. Markdown can then be generated from that JSON for chunking, inspection, and LLM context.

---

## 3. Candidate tools to test

| Option | Best use | Typical output | Why it is worth testing |
|---|---|---|---|
| **Docling** | Strong open-source default | Markdown, JSON | Designed for document understanding and AI/RAG workflows. Worth testing for reading order, layout, tables, OCR and structured output. |
| **Marker** | Fast local conversion | Markdown, JSON, chunks, HTML | A modern local parser aimed at converting PDFs and other documents into LLM-friendly formats. Potentially useful because it can output chunks as well as Markdown/JSON. |
| **LlamaParse / LlamaExtract** | Hosted RAG-focused parsing | Markdown, JSON | Built around parsing complex PDFs for RAG. Useful as a high-quality cloud benchmark, even if not chosen as the final production tool. |
| **Azure AI Document Intelligence** | Enterprise/cloud layout extraction | JSON, Markdown | Strong option for layout, tables, forms, bounding boxes and enterprise support, especially if the project later moves into Azure. |
| **Google Document AI** | Cloud document extraction and custom extractors | JSON | The relevant Google production tool for document extraction. Better suited than NotebookLM for repeatable PDF processing. |
| **Mistral OCR / modern OCR APIs** | OCR-to-Markdown and difficult PDFs | Markdown, structured text | Worth testing on scans, figures, equations and complex tables. Could be useful as a fallback for difficult documents. |
| **Unstructured** | General enterprise ingestion | JSON-like elements | Mature document ingestion framework often used in RAG pipelines. Useful as a baseline/comparison option. |

The aim would not be to test every tool exhaustively. The aim would be to select a few promising candidates and compare them against a small, representative sample of real KNBS/statistical PDFs.

---

## 4. How the options compare

### 4.1 Docling

Docling is probably the first open-source option I would test. It is designed for AI-oriented document processing and can export structured representations rather than just plain text.

For StatsChat, the attraction is that it may provide a stronger local pipeline while keeping the process reproducible and inspectable.

**Good fit when:**

- the project wants an open-source/local parser;
- reproducibility matters;
- the team wants control over post-processing;
- documents are public but governance still favours local processing.

**Watch out for:**

- statistical tables may still need custom post-processing;
- cross-page tables may not always be reconstructed correctly;
- output needs to be evaluated, not just visually inspected.

### 4.2 Marker

Marker is another strong open-source/local candidate. It is particularly interesting because it is oriented toward Markdown, JSON and chunk outputs, which makes it relevant for RAG.

**Good fit when:**

- the team wants fast local conversion;
- Markdown quality is important;
- chunk-ready output is useful;
- optional LLM-enhanced parsing is acceptable.

**Watch out for:**

- visually plausible Markdown does not guarantee factual accuracy;
- table structure should be tested carefully;
- defaults may need tuning for statistical reports.

### 4.3 LlamaParse / LlamaExtract

LlamaParse is a useful cloud benchmark because it is designed specifically for RAG-style document parsing. LlamaExtract-style schema extraction may also be helpful for repeated indicators, tables or publication metadata.

**Good fit when:**

- the team wants a strong hosted benchmark;
- complex tables and layout are important;
- speed of experimentation matters;
- API use is acceptable for public PDFs.

**Watch out for:**

- cost at scale;
- dependency on a hosted service;
- reproducibility/versioning of parsing outputs;
- data governance and procurement constraints.

### 4.4 Azure AI Document Intelligence

Azure AI Document Intelligence is likely to be a serious enterprise option. It is especially relevant where the project needs structured layout data, table cells, row/column spans, page-level positions and bounding boxes.

**Good fit when:**

- enterprise support matters;
- the project is likely to use Azure infrastructure;
- structured layout and table metadata are important;
- integration with existing Microsoft governance is helpful.

**Watch out for:**

- output may need transformation into a StatsChat-specific schema;
- costs should be checked;
- it may be less RAG-native than tools like LlamaParse.

### 4.5 Google Document AI

Google Document AI is the relevant Google tool for production document extraction. It is distinct from NotebookLM. Document AI is designed for repeatable extraction; NotebookLM is designed more as a research and analysis interface over sources.

**Good fit when:**

- Google Cloud is already an option;
- custom extractors could be useful;
- the team wants structured Document JSON;
- batch processing and API access are required.

**Watch out for:**

- cloud dependency;
- cost and governance;
- output still needs mapping into a StatsChat schema.

### 4.6 Mistral OCR and other modern OCR APIs

Modern OCR-to-Markdown tools are worth testing, particularly for difficult PDFs, scanned pages, complex tables, figures and mathematical notation. They may not need to be the default parser, but they could be useful as a fallback for documents where local extraction performs badly.

**Good fit when:**

- PDFs contain scans or embedded page images;
- tables and figures are not captured well by standard tools;
- Markdown output is useful for LLM context;
- the team is willing to use a hosted API.

**Watch out for:**

- cost;
- hallucinated or over-normalised structure;
- the need to preserve exact source provenance.

### 4.7 Unstructured

Unstructured is a mature ingestion framework and remains worth considering as a baseline or comparison option. It may not be the most exciting option, but it is commonly used in RAG pipelines and can help establish a practical benchmark.

**Good fit when:**

- the team wants a general document ingestion framework;
- integration with existing RAG tooling matters;
- element-level JSON-like output is sufficient.

**Watch out for:**

- table handling may still need careful evaluation;
- output quality can vary by PDF type;
- some advanced behaviour may require additional configuration.

---

## 5. Would NotebookLM be applicable?

Yes, but mainly as an **exploratory or human-review tool**, not as the main pipeline.

NotebookLM could help with:

- inspecting individual difficult PDFs;
- quickly understanding what a report contains;
- checking whether a parser has missed important tables or caveats;
- generating rough summaries for human review;
- supporting subject-matter experts who want to interrogate a small set of documents.

However, NotebookLM is probably not the right core tool for StatsChat ingestion because it is less suited to:

- batch conversion of around 1,000 PDFs;
- version-controlled extraction;
- repeatable JSON/Markdown generation;
- deterministic testing;
- custom chunking;
- page-level provenance and evaluation;
- integration into an automated RAG pipeline.

A useful distinction is:

```text
NotebookLM: useful for exploration, QA and human review
Google Document AI: relevant for production document extraction
```

---

## 6. Proposed StatsChat extraction architecture

A stronger StatsChat pipeline could be organised into four stages.

### Stage 1: Layout extraction

Convert each PDF into a structured representation of pages, blocks, headings, paragraphs, tables, figures, captions and coordinates.

```text
PDF → pages, headings, paragraphs, tables, figures, captions, coordinates
```

### Stage 2: Semantic normalisation

Map the raw extraction into a StatsChat-specific schema. This is where generic parser output becomes project-specific evidence.

Examples of normalisation decisions:

- remove repeated headers and footers;
- attach table titles and notes to the table;
- preserve page numbers;
- identify publication title and date;
- identify section hierarchy;
- handle cross-page tables;
- store figures and captions together;
- flag low-confidence extraction.

### Stage 3: RAG rendering

Generate Markdown chunks and metadata-rich retrieval records from the structured JSON.

This could include different chunk types:

- paragraph chunks;
- section chunks;
- table chunks;
- table row chunks;
- figure caption chunks;
- summary chunks;
- metadata-only records.

### Stage 4: Evaluation

Evaluate the parser using the same spirit as the existing StatsChat Q&A evaluation framework.

The key question should be:

> Did the parser preserve the evidence needed to answer known questions correctly?

This is better than simply asking whether the extracted Markdown “looks good”.

---

## 7. Example JSON schema

A useful output record might look something like this:

```json
{
  "document_id": "2025-economic-survey.pdf",
  "title": "Economic Survey 2025",
  "publication_date": "2025-05-01",
  "page": 42,
  "section_path": ["Prices", "Consumer Price Index"],
  "content_type": "table",
  "table_title": "Consumer Price Index by COICOP division",
  "text_markdown": "...",
  "table_json": {
    "columns": ["Division", "Index", "Annual change"],
    "rows": [
      ["Food and non-alcoholic beverages", "...", "..."]
    ]
  },
  "source_coordinates": [
    {
      "page": 42,
      "bbox": [72, 144, 520, 640]
    }
  ],
  "extraction_confidence": 0.87,
  "parser": {
    "name": "example-parser",
    "version": "x.y.z",
    "config_hash": "abc123"
  }
}
```

This kind of schema would make it easier to debug retrieval failures, compare parser versions, and trace answers back to source pages.

---

## 8. Suggested bake-off evaluation

I would test around 20 PDFs before changing the full pipeline. The sample should include deliberately awkward cases.

### Suggested sample

Include documents with:

- clean born-digital text;
- multi-column pages;
- many statistical tables;
- cross-page tables;
- charts and figure captions;
- footnotes and caveats;
- scanned or partially scanned pages;
- long reports;
- short bulletins;
- recent KNBS publications;
- older legacy PDFs.

### Candidate tools

A practical bake-off might compare:

1. current PyMuPDF baseline;
2. Docling;
3. Marker;
4. LlamaParse or Mistral OCR;
5. Azure AI Document Intelligence or Google Document AI, if cloud testing is acceptable.

### Scoring criteria

| Criterion | Why it matters |
|---|---|
| Reading order | Prevents columns, sidebars and footnotes being mixed into nonsense. |
| Table reconstruction | Critical for statistical PDFs. |
| Cross-page table handling | Common in statistical publications. |
| Page-level citation fidelity | Needed for source traceability. |
| Header/footer removal | Reduces retrieval noise. |
| Figure caption extraction | Important for charts, caveats and interpretation. |
| Section hierarchy | Improves chunking and retrieval. |
| Speed | Matters for the initial batch. |
| Cost | Matters for hosted APIs. |
| JSON/Markdown export quality | Determines how easy the output is to use downstream. |
| Reproducibility | Important for testing and future maintenance. |
| Ease of integration | Determines practical maintainability. |

---

## 9. Possible scoring template

For each tool and PDF, score each category from 1 to 5.

| Category | Score | Notes |
|---|---:|---|
| Reading order |  |  |
| Section headings |  |  |
| Tables |  |  |
| Cross-page tables |  |  |
| Figure captions |  |  |
| Page references |  |  |
| Header/footer removal |  |  |
| Markdown readability |  |  |
| JSON usefulness |  |  |
| RAG chunkability |  |  |
| Speed |  |  |
| Cost |  |  |
| Overall |  |  |

Then add a small number of parser-specific diagnostic questions, for example:

- Was the CPI value on page X preserved correctly?
- Was the table title attached to the right table?
- Did the parser merge unrelated columns?
- Did the parser remove repeated headers and footers?
- Can the extracted text support the existing verified Q&A item?
- Can the output identify the page used for the answer?

---

## 10. Likely recommendation

For StatsChat, I would probably begin with:

```text
Primary open-source test: Docling
Secondary open-source test: Marker
Cloud benchmark: LlamaParse or Mistral OCR
Enterprise benchmark: Azure AI Document Intelligence or Google Document AI
Manual exploration / QA: NotebookLM
```

The final choice should depend on evidence from the bake-off, especially table quality and page-level traceability.

My current hunch is that **Docling or Marker plus custom StatsChat post-processing** is likely to be the best open-source route. A hosted tool such as LlamaParse, Mistral OCR, Azure Document Intelligence or Google Document AI could be useful either as a benchmark or as a fallback for difficult PDFs.

---

## 11. Key design principle

The most important design principle is to make PDF processing an **evaluated component** of the StatsChat pipeline.

The project already has a Q&A evaluation framework. A similar approach can be applied one step earlier:

> For each known answer, did the parser preserve the source evidence, table, page and caveat needed to answer correctly?

This would make parser selection much more rigorous. It would also help separate three different failure modes:

1. the evidence was lost during PDF extraction;
2. the evidence was extracted but not retrieved;
3. the evidence was retrieved but not used correctly by the generation step.

That distinction is essential for improving StatsChat systematically.

---

## Repo-facing recommendation

For the next development cycle, do not test every option exhaustively. Start with:

1. current parser output;
2. Docling output;
3. Docling plus StatsChat-specific post-processing.

Add Marker or a hosted benchmark only if the initial Docling trial shows mixed results or if difficult PDFs need a fallback route.
