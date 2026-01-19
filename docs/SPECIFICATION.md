# Project Specification: StatsChat-KE

## 1. Executive Summary
StatsChat-KE is a semantic search engine and chatbot designed to unlock the data trapped in PDF reports published by the Kenya National Bureau of Statistics (KNBS). It allows users (researchers, policy makers, public) to ask natural language questions and receive sourced answers derived directly from official government documents.

## 2. Core Functionality

### 2.1 Data Ingestion (The ETL Pipeline)
The system must autonomously build its own knowledge base:
1.  **Crawl**: Iterate through the KNBS website to discover Economic Surveys and Statistical Abstracts.
2.  **Download**: Securely download PDF files to local storage.
3.  **Extract**: Convert unstructured PDF content into structured JSON, preserving:
    *   Text content (per page).
    *   Metadata (Publication Date, Theme, Title).
    *   Page-level granular citation links.
4.  **Embed**: Transform text chunks into vector embeddings using `sentence-transformers`.
5.  **Index**: Store vectors in a FAISS index for efficient similarity search.

### 2.2 Search & Retrieval
1.  **Semantics over Keywords**: The system uses vector similarity to find *meanings*, not just matching words.
2.  **Time-Aware**: (Planned/Experimental) The system should prioritize more recent data or understand temporal contexts (e.g., "in 2020").

### 2.3 Answer Generation (RAG)
1.  **Context Construction**: Retrieve the top $K$ most relevant document chunks based on the user's query.
2.  **Synthesis**: Pass these chunks to a Large Language Model (LLM) with a strict prompt: "Answer the user using *only* this context."
3.  **Citation**: The final answer must implicitly or explicitly reference the source document.


## 3. System Constraints & Assumptions
*   **Data Source**: Limited strictly to KNBS documents to maintain authority.
*   **Deployment**: Originally designed for macOS/Local runtime but includes FastAPI for cloud deployment.
*   **Connectivity**: Requires internet access for the initial scrape and for calling cloud-based LLM APIs (if configured).
*   **Accuracy**: As an experimental AI system, 100% accuracy is not guaranteed. Hallucinations are a known risk.
