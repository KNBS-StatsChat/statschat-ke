# Input/Output (I/O) Overview

This document explains what *goes into* StatsChat-KE and what *comes out*, at two levels:

1. **Query-time I/O** (when a user calls the API with a question).
2. **Pipeline I/O** (how PDFs are ingested and transformed into a searchable index).

It also clarifies what “document output” means in StatsChat (spoiler: it is usually a **text chunk**, not a whole PDF).

## Contents

- [Terminology (important)](#terminology-important)
- [Query-Time I/O](#query-time-io)
- [Example API responses](#example-api-responses)
- [Pipeline I/O (PDF to Index to Query)](#pipeline-io-pdf-to-index-to-query)
- [Where to change I/O behavior](#where-to-change-io-behavior)
- [Recommended direction](#recommended-direction)

## Terminology (important)

- **PDF / Publication**: An original KNBS document file downloaded during ingestion.
- **JSON Conversion**: Extracted text + metadata from a PDF.
- **Chunk / Split**: A slice of text produced by splitting the converted content (used for embeddings/retrieval).
- **Vector Store (FAISS)**: The index of chunk embeddings that powers similarity search.
- **Reference**: What the API returns to explain “where the answer came from”. In practice this is metadata associated with retrieved chunks (often including a page URL).

## Query-Time I/O

### Inputs

Both API implementations accept:

- `q`: the user’s question (string)
- `content_type`: either `latest` or `all` (defaults to `latest`)
- `debug`: whether to include extra debugging detail in the response

### Outputs

At a minimum, the `/search` endpoint returns:

- `question`
- `content_type`
- `answer`
- `references` (this is the key “document output” field)

There are two implementations in this repo.

## Example API responses

The exact content varies per query, but the *shape* is stable.

### Cloud `/search` (preferred going forward)

`references` is typically a list of retrieved **chunks** (dicts with metadata + score).

```json
{
  "question": "By how much did Kenya's GDP grow in 2024?",
  "content_type": "latest",
  "answer": "Kenya's GDP grew by X% in 2024.",
  "references": [
    {
      "title": "Economic Survey 2025",
      "date": "2025-01-01",
      "page_url": "https://.../publication.pdf#page=12",
      "page_content": "...extracted text chunk...",
      "score": 0.23
    },
    {
      "title": "Gross Domestic Product Report",
      "date": "2024-01-01",
      "page_url": "https://.../gdp.pdf#page=5",
      "page_content": "...extracted text chunk...",
      "score": 0.31
    }
  ]
}
```

If `debug=true`, an additional `debug_response` field is included.

If the retrieved context is too weak (based on thresholds), StatsChat may return a fallback answer such as:

> "No suitable answer found. However relevant information may be found in a PDF. Please check the link(s) provided."

If the top match is worse than `document_threshold` (i.e., “no suitable PDFs found”), the cloud path replaces `references` with placeholder strings rather than returning chunk dicts.

Note: the cloud implementation also adjusts the answer text in this case so it does not suggest that links are available.

```json
{
  "question": "...",
  "content_type": "latest",
  "answer": "...",
  "references": [
    "No suitable PDFs found. Please refer to context",
    "No context available. Please refer to response"
  ]
}
```

### Local `/search` (legacy/alternative)

`references` is a single URL (string), and the response includes extra “context” fields.

```json
{
  "question": "By how much did Kenya's GDP grow in 2024?",
  "content_type": "latest",
  "answer": "...",
  "references": "https://.../publication.pdf#page=12",
  "context_from": "...",
  "context_reference": "...",
  "relevant_publication_one": "Economic Survey 2025",
  "relevant_publication_two": "Gross Domestic Product Report"
}
```

If the local path cannot find suitable PDFs (no results, or the top match is worse than `document_threshold`), it returns a consistent “no PDFs found” response and leaves `references` empty:

```json
{
  "question": "...",
  "content_type": "latest",
  "answer": "No suitable PDFs found for this question. Please try rephrasing.",
  "references": "",
  "context_from": "",
  "context_reference": "",
  "relevant_publication_one": "",
  "relevant_publication_two": ""
}
```

### Cloud API path (preferred going forward)

- **Entry point**: `fast-api/main_api_cloud.py`
- **Generator/retriever**: `statschat/generative/cloud_llm.py` (`Inquirer`)

**What gets retrieved?**

- The retriever pulls **up to `k_docs` chunks** from FAISS via `similarity_search_with_score(...)`.
- In your current config, `k_docs = 2` (see `statschat/config/main.toml`).
- Some results can be filtered out if they are above `similarity_threshold`, so the final count can be `< k_docs`.

**What does the LLM see as context?**

- The LLM is passed **up to `k_contexts` chunks**, further filtered by a score rule: only chunks with `score <= 1.5 * best_score` are included.
- In your current config, `k_contexts = 5`.

**What is returned in `references`?**

- The API returns `references` as a **list**.
- Each element is a dict representing a retrieved chunk and its metadata (e.g., `title`, `date`, `page_url`, `page_content`, `score`, plus highlighting fields).

**Edge case: “no suitable PDFs”**

If the best retrieved chunk’s score is worse than `document_threshold`, the code clears references and returns two placeholder strings instead.

### Local API path (legacy/alternative)

- **Entry point**: `fast-api/main_api_local.py`
- **Retriever**: `statschat/generative/local_llm.py` (`similarity_search`)

**Key differences**

- Retrieval is **hard-coded** to `k_docs = 3` in `local_llm.py`.
- The prompt uses **up to 2 chunks** as context (the script now pads or exits early if fewer than 2 chunks are retrieved).
- The API response returns:
  - `references`: a **single URL string** (the first match’s `page_url`)
  - `relevant_publication_one` and `relevant_publication_two`: titles for the top 2 matches

Local mode also includes a small JSON-recovery step when parsing model output and uses deterministic generation settings to reduce JSON parse failures.

Local mode also applies `answer_threshold` and `document_threshold` at the API layer to keep behavior consistent with the cloud path (e.g., avoid suggesting links exist when `references` is empty).

If you want “document outputs” to behave the same way across cloud/local, you’ll likely want to standardize these response formats.

## Pipeline I/O (PDF to Index to Query)

This section describes the offline pipeline that prepares data for query-time retrieval.

### Inputs (Pipeline)

- **PDF files** downloaded into:
  - `data/pdf_downloads/` (historical/all)
  - `data/latest_pdf_downloads/` (recent)

### Outputs (Pipeline stages)

1. **PDF -> JSON conversion**
   - Output directories:
     - `data/json_conversions/`
     - `data/latest_json_conversions/`
   - Each converted JSON generally corresponds to one publication and contains text + metadata.

2. **JSON -> chunked JSON**
   - Output directories:
     - `data/json_split/`
     - `data/latest_json_split/`
   - Splitting is controlled by:
     - `split_length = 2000`
     - `split_overlap = 200`

3. **Embeddings -> FAISS vector store**
   - Output directories:
     - `data/db_langchain/`
     - `data/db_langchain_latest/`

### How many PDFs go in vs how many “documents” come out?

- **PDFs in**: potentially hundreds/thousands over time (depends on what you download and ingest).
- **At query time, the system does *not* return PDFs**. It returns a *small* number of retrieved **chunks** (plus metadata that can link back to the PDF/page).

In practice, the query-time “document output count” is bounded by:

- Retrieved chunks returned: $\le k_{docs}$ (after threshold filtering and deduplication)
- Chunks passed to LLM: $\le k_{contexts}$ (and also filtered by a relative-score rule)

With your current config, that is typically:

- **Up to 2** retrieved chunk references returned (`k_docs = 2`)
- **Up to 5** chunks eligible to be passed to the LLM (`k_contexts = 5`), though it may pass fewer.

## Where to change I/O behavior

- Query-time retrieval knobs: `statschat/config/main.toml`
  - `k_docs`, `k_contexts`, `similarity_threshold`, `answer_threshold`, `document_threshold`
- Chunking knobs (pipeline): `statschat/config/main.toml`
  - `split_length`, `split_overlap`
- Cloud implementation behavior: `statschat/generative/cloud_llm.py`
- Local implementation behavior: `statschat/generative/local_llm.py` and `fast-api/main_api_local.py`

## Recommended direction

Because the cloud path is expected to become the preferred path, it’s a good target for standardizing:

- The meaning of `references`
- The number of retrieved items (`k_docs`)
- The metadata schema returned to clients
