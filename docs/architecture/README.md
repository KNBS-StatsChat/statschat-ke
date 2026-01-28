# StatsChat-KE Architecture

This directory contains detailed documentation on the architecture and data pipelines of the StatsChat-KE project.

## Overview

StatsChat-KE is a Retrieval-Augmented Generation (RAG) application designed to allow users to query official Kenya National Bureau of Statistics (KNBS) reports using natural language.

The system is built on a four-stage pipeline:
1.  **Ingestion**: Scraping and converting PDFs.
2.  **Embedding**: Indexing content for search.
3.  **Retrieval**: Finding relevant context locally.
4.  **Generation**: Synthesizing answers using an LLM.

## Documentation Map

### 1. Data Pipelines (The Core)

These documents detail the journey of data from the KNBS website to the user's screen, organized into three conceptual phases.

#### Phase 1: Data Preparation
-   **[PDF Ingestion Pipeline](pipeline-pdf-ingestion.md)**
    -   *Scope*: Scraping PDFs, `url_dict.json` management, and PDF-to-JSON conversion.
    -   *Key Scripts*: `pdf_downloader.py`, `pdf_to_json.py`.
-   **[Embedding Pipeline](pipeline-embedding.md)**
    -   *Scope*: Splitting JSONs, chunking text, generating embeddings, and FAISS indexing.
    -   *Key Scripts*: `preprocess.py`.

#### Phase 2: Retrieval (Local)
-   **[Retrieval Pipeline](pipeline-retrieval.md)**
    -   *Scope*: Semantic search, time-decay reranking, and context selection.
    -   *Key Scripts*: `cloud_llm.py` (Inquirer class).

#### Phase 3: Generation (Cloud)
-   **[Generation Pipeline](pipeline-generation.md)**
    -   *Scope*: Prompt engineering, LLM interaction (Cloud vs Local), and response parsing.
    -   *Key Scripts*: `cloud_llm.py`, `local_llm.py`, `prompts_cloud.py`.

#### Cross-cutting
-   **[Input/Output (I/O) Overview](pipeline-input-output.md)**
    -   *Scope*: What goes in (PDFs, chunks, questions) and what comes out (answers, references) across both the pipeline and query-time API.


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
            | (Retrieval Pipeline)
            |
      [Context String]
            |
            | (Generation Pipeline)
            v
[User] <-> [API] <-> [LLM]
```

## Directory Structure

The `docs/architecture/` folder follows a "Hub and Spokes" model:
-   **Hub**: This `README.md` provides the context.
-   **Spokes**: The individual markdown files provide the deep technical details for each component.
