# 2026-02-16 — Date-specific retrieval: April 2025 CPI Highlights

## Summary

A query for a specific month/year (e.g. "What is the consumer price index in April 2025?") did not reliably retrieve the expected KNBS bulletin:

- `Kenya-Consumer-Price-Indices-and-Inflation-Rates-Highlights-April-2025.pdf`

The document was present locally and indexed, but it was ranked outside the default `k_docs` retrieval window and could be further de-prioritized by the default recency reweighting (`latest_weight`).

This investigation documents what was happening, why, and the minimal changes made to improve retrieval for explicit month/year questions.

## Context

Relevant components:

- Cloud retriever/generator: [statschat/generative/cloud_llm.py](../../statschat/generative/cloud_llm.py)
- Cloud API entrypoint: [fast-api/main_api_cloud.py](../../fast-api/main_api_cloud.py)

Data pipeline artifacts involved:

- Downloaded PDF: `data/pdf_downloads/Kenya-Consumer-Price-Indices-and-Inflation-Rates-Highlights-April-2025.pdf`
- Converted JSON: `data/json_conversions/Kenya-Consumer-Price-Indices-and-Inflation-Rates-Highlights-April-2025.json`
- Split JSON chunks: `data/json_split/9538847_*.json`
- FAISS vector store (observed on disk): `data/data/db_langchain/index.faiss`

## What was happening before

### 1) The correct bulletin was present, but not in the top-`k_docs` results

The April 2025 Highlights bulletin existed in the vector store (two chunks under `source == 9538847`), but for the exact question:

- "What is the consumer price index in April 2025?"

it ranked around ~36th in the similarity results, while the retriever only requested `k_docs=10`. As a result, it never reached downstream steps (deduplication, optional reweighting, LLM answer synthesis).

### 2) Recency reweighting can work against an explicit date request

`Inquirer.make_query(...)` supports a `latest_weight` option which reweights similarity scores toward more recent publications. This is helpful for "latest"/"recent" queries, but it can reduce recall for questions that explicitly ask for a specific month/year.

## Diagnosis

We verified:

- The PDF was downloaded.
- The PDF was successfully converted into JSON.
- The conversion was split into chunk-level JSONs.
- The FAISS index used by the app was located under `data/data/db_langchain`.
- The April 2025 Highlights bulletin was indexed but not within the default top-10 search window for the exact question.

## Changes made

### 1) Improve recall for explicit month/year questions (cloud retriever)

File: [statschat/generative/cloud_llm.py](../../statschat/generative/cloud_llm.py)

Changes:

- Added a lightweight month/year extractor (`_extract_month_year`) that detects strings like "April 2025".
- If a month/year is detected:
  - Increase retrieval depth: request `k_docs = max(k_docs, 50)`.
  - Promote matches whose metadata `date` contains the requested month/year (e.g. metadata date "01 April 2025" contains "April 2025").
  - Disable recency reweighting for that query by setting `effective_latest_weight = 0`.

Rationale:

- Date-specific questions are often answered by a single bulletin that may not be in the top-10 due to embedding similarity quirks.
- Promotion based on document metadata date is a cheap and robust bias that stays within the RAG paradigm.
- Disabling recency reweighting avoids pushing the explicitly-requested month out of the final ranked list.

### 2) Align cloud API behavior with date-specific retrieval intent

File: [fast-api/main_api_cloud.py](../../fast-api/main_api_cloud.py)

Change:

- If the incoming question contains an explicit month/year, force `latest_weight = 0` before calling `inquirer.make_query(...)`.

Rationale:

- Avoids applying recency bias in the API layer for date-specific questions.
- Also avoids fragmenting `Inquirer.make_query()`’s `lru_cache` keys (same question + multiple `latest_weight` values).

### 3) Add unit tests

File: [tests/unit/generative/test_cloud_llm.py](../../tests/unit/generative/test_cloud_llm.py)

Added coverage for:

- Month/year queries increasing `k` to 50 and promoting date-matching docs.
- `make_query` not calling `time_decay` when month/year is explicit.

## Verification

Verified locally by running:

- `python statschat/generative/cloud_llm.py`

With:

- `question = "What is the consumer price index in April 2025?"`

Observed:

- Retrieval now surfaces the April 2025 Highlights bulletin.
- The answer is grounded in the April 2025 CPI table (e.g. Overall CPI value for April 2025).
- Unit tests for `cloud_llm` pass.

## Notes / follow-ups

- This change intentionally targets *explicit month/year* queries only, leaving the default behavior unchanged for general questions.
- If we want this behavior in the local (non-cloud) API path, it likely needs separate work: [fast-api/main_api_local.py](../../fast-api/main_api_local.py) uses a different retrieval implementation (`statschat/generative/local_llm.py`).
