# Embedding Pipeline

This document details the second stage of the StatsChat-KE data pipeline: transforming structured JSON documents into vector embeddings stored in a FAISS index. This enables semantic search capabilities for the RAG system.

## Conceptual Overview

Once PDF reports are converted to JSON, they must be prepared for the Large Language Model (LLM). This involves:
1.  **Splitting**: Breaking down large reports into smaller, manageable sections.
2.  **Chunking**: Further dividing sections into text chunks that fit within model context windows.
3.  **Embedding**: Converting text chunks into numerical vectors using a pre-trained model.
4.  **Indexing**: Storing these vectors in a FAISS (Facebook AI Similarity Search) index for fast retrieval.

## Data Flow

```ascii
[data/json_conversions/]
      |
      v
+-------------------+
|   preprocess.py   |
|  (JSON Splitter)  |
+-------------------+
      |
      v
[data/json_split/] (Section-level JSONs)
      |
      v
+-------------------+
|   preprocess.py   |
| (Loader & Chunker)|
+-------------------+
      |
      v
[Document Chunks]
      |
      v
+-------------------+
|   preprocess.py   |
| (Embedding Model) |
+-------------------+
      |
      v
[data/db_langchain/] (FAISS Index)
```

## Pipeline Components

### 1. Preprocessor (`preprocess.py`)

This is the core script for the embedding pipeline. It uses LangChain to orchestrate the transformation from JSON to Vector Store.

-   **Entry Point**: `statschat/embedding/preprocess.py`
-   **Class**: `PrepareVectorStore`
-   **Key Steps**:

    1.  **JSON Splitting (`_json_splitter`)**:
        -   Reads the "full report" JSON files from `json_conversions/`.
        -   Splits them into individual files for each section (e.g., `1042902_0.json`, `1042902_1.json`).
        -   **Why?** This ensures that metadata (Title, Date) is preserved for *each section*, allowing the retriever to cite specific parts of a report.

    2.  **Loading (`_load_json_to_memory`)**:
        -   Uses `DirectoryLoader` and `JSONLoader` to read the split JSON files.
        -   Extracts `page_text` as the content and preserves other fields as metadata.

    3.  **Chunking (`_split_documents`)**:
        -   Uses `RecursiveCharacterTextSplitter`.
        -   **Config**: `split_length` (default 1000 chars) and `split_overlap` (default 200 chars).
        -   Ensures text chunks are small enough for the embedding model but retain context.

    4.  **Embedding (`_embed_documents`)**:
        -   **Model**: `sentence-transformers/all-mpnet-base-v2` (via HuggingFace).
        -   Converts text chunks into dense vector representations.
        -   Saves the vectors and metadata to a local FAISS index.

### 2. Database Merger (`merge_database_files.py`)

This script is a utility used specifically in **UPDATE** mode to clean up and consolidate files after the pipeline runs.

-   **Entry Point**: `statschat/pdf_processing/merge_database_files.py`
-   **Function**:
    -   Moves files from `latest_pdf_downloads/` → `pdf_downloads/`.
    -   Moves files from `latest_json_conversions/` → `json_conversions/`.
    -   Moves files from `latest_json_split/` → `json_split/`.
    -   Merges the new entries from `latest_pdf_downloads/url_dict.json` into the main `url_dict.json`.

## Execution Modes: SETUP vs UPDATE

The `preprocess.py` script adapts its behavior based on the pipeline mode.

| Feature | SETUP Mode | UPDATE Mode |
| :--- | :--- | :--- |
| **Input Directory** | `data/json_conversions/` | `data/latest_json_conversions/` |
| **Split Directory** | `data/json_split/` | `data/latest_json_split/` |
| **Target FAISS DB** | `data/db_langchain/` | `data/db_langchain_latest/` (Temporary) |
| **Merging Logic** | None. Creates fresh DB. | Merges `db_langchain_latest` into `db_langchain`. |

### The Update Process
In **UPDATE** mode, the pipeline performs a "Merge-and-Move" strategy:
1.  **Process New Data**: New JSONs are split and embedded into a *temporary* FAISS index (`db_langchain_latest`).
2.  **Merge Indices**: `preprocess.py` loads the main index (`db_langchain`), merges the temporary index into it, and saves the result.
3.  **Cleanup**: `merge_database_files.py` moves the source files (PDFs, JSONs) into the main data directories, ensuring the file system reflects the state of the vector store.
