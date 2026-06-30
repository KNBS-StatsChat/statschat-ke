# StatsChat-KE Architecture

This directory contains detailed documentation on the architecture and data pipelines of the StatsChat-KE project.

## Overview

StatsChat-KE is a Retrieval-Augmented Generation (RAG) application designed to allow users to query official Kenya National Bureau of Statistics (KNBS) reports using natural language.

The system is built on four operational pipeline stages, closed by an evaluation
feedback loop:

1.  **Ingestion**: Scraping and converting PDFs.
2.  **Embedding**: Indexing content for search.
3.  **Retrieval**: Finding relevant context.
4.  **Generation**: Synthesizing answers using an LLM.
5.  **Evaluation**: Measuring answer accuracy against an audited benchmark and feeding results back to inform changes to any of the stages above.

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
-   **[April 2026 Accuracy-Driven Architecture Changes](2026-04-accuracy-architecture-changes.md)**
    -   *Scope*: Exact retrieval, routing, guardrail, and local/cloud parity changes made during the April 2026 accuracy work, including where they were inserted in code and which benchmark examples they affected.

#### Phase 4: Evaluation (Feedback Loop)

The evaluation system closes the loop. It is not a passive test suite — it is
the control point that governs whether any change to the pipeline (retrieval
architecture, model, configuration, corpus) can be accepted.

The evaluator runs a curated benchmark workbook of questions with known correct
answers against the live API, scores responses, and writes results to a
cross-run ledger so that accuracy trends are visible over time.

The current audited reference baseline (April 2026, GPT-5.4-mini, 74 questions)
achieved overall accuracy of `70/74 = 0.946`. Any change to the system should
be validated against this baseline before deployment.

-   **[tests/accuracy/README.md](../../tests/accuracy/README.md)**
    -   *Scope*: Full evaluation workflow, script reference, metric definitions, local/cloud parity notes, and benchmark history.
-   **[docs/reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md](../reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md)**
    -   *Scope*: Recommended ongoing accuracy monitoring model for KNBS maintenance.


### 2. Configuration & Operations

-   **[Answer & Document Thresholds](threshold-guide.md)**
    -   *Scope*: How `answer_threshold` and `document_threshold` work, the three-zone response behaviour, FAISS score ranges, and a note on the current inverted-threshold configuration.
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
            |
            | (Evaluation)
            v
   [Benchmark Score / Ledger]
            |
            | (Feedback: informs changes to any stage above)
            +---------------------------------------------->
```

## Directory Structure

The `docs/architecture/` folder follows a "Hub and Spokes" model:
-   **Hub**: This `README.md` provides the context.
-   **Spokes**: The individual markdown files provide the deep technical details for each component.
