# StatsChat-KE Architecture

This directory contains detailed documentation on the architecture and data pipelines of the StatsChat-KE project.

## Overview

StatsChat-KE is a Retrieval-Augmented Generation (RAG) application designed to allow users to query official Kenya National Bureau of Statistics (KNBS) reports using natural language.

The system is built on a three-stage pipeline:
1.  **Ingestion**: Scraping and converting PDFs.
2.  **Embedding**: Indexing content for search.
3.  **Querying**: Retrieving and synthesizing answers.

## Documentation Map

### 1. Data Pipelines (The Core)

These documents detail the journey of data from the KNBS website to the user's screen.

-   **[PDF Ingestion Pipeline](pipeline-pdf-ingestion.md)**
    -   *Scope*: Scraping PDFs, `url_dict.json` management, and PDF-to-JSON conversion.
    -   *Key Scripts*: `pdf_downloader.py`, `pdf_to_json.py`.

-   **[Embedding Pipeline](pipeline-embedding.md)**
    -   *Scope*: Splitting JSONs, chunking text, generating embeddings, and FAISS indexing.
    -   *Key Scripts*: `preprocess.py`.

-   **[RAG Query Pipeline](pipeline-rag-query.md)**
    -   *Scope*: API endpoints, similarity search, time-decay reranking, and LLM generation.
    -   *Key Scripts*: `main_api_cloud.py`, `cloud_llm.py`.

### 2. Configuration & Operations

-   **[Token Usage & Cost Guide](token-usage-guide.md)**
    -   Explains how tokens are calculated, how to estimate costs, and how to tune configuration parameters (`k_docs`, `chunk_size`) to balance performance and budget.

## High-Level Architecture

```ascii
[KNBS Website]
      |
      | (Ingestion Pipeline)
      v
[PDFs] -> [JSONs]
            |
            | (Embedding Pipeline)
            v
      [FAISS Vector Store]
            ^
            | (Retrieval)
            |
[User] -> [API] -> [RAG Logic] -> [LLM]
```

## Directory Structure

The `docs/architecture/` folder follows a "Hub and Spokes" model:
-   **Hub**: This `README.md` provides the context.
-   **Spokes**: The individual markdown files provide the deep technical details for each component.
