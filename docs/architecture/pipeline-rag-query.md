# RAG Query Pipeline

This document details the final stage of the StatsChat-KE pipeline: the Retrieval-Augmented Generation (RAG) process that answers user queries using the indexed data.

## Conceptual Overview

The RAG pipeline connects the user's question to the vector store created in the previous stage. It retrieves relevant document chunks, prioritizes them based on relevance and recency, and uses a Large Language Model (LLM) to synthesize an answer.

The process follows these steps:
1.  **Retrieval**: Search the FAISS index for content similar to the user's query.
2.  **Reranking**: Adjust scores to favor more recent publications (Time Decay).
3.  **Context Selection**: Filter and format the top results for the LLM.
4.  **Generation**: Ask the LLM to answer the question using *only* the provided context.
5.  **Post-Processing**: Parse the structured response and highlight relevant text in the source documents.

## Data Flow

```ascii
[User Query]
      |
      v
+-----------------------+
|   FastAPI Endpoint    |
| (main_api_cloud.py)   |
+-----------------------+
      |
      v
+-----------------------+
|    Inquirer Class     |
|    (cloud_llm.py)     |
+-----------------------+
      |
      | 1. Similarity Search
      v
[FAISS Vector Store]
      |
      | 2. Retrieved Chunks
      v
[Inquirer: Reranking & Filtering]
      |
      | 3. Prompt + Context
      v
[LLM (OpenAI / OpenRouter)]
      |
      | 4. Structured JSON Response
      v
[Inquirer: Highlighting]
      |
      v
[Final JSON Response]
```

## Pipeline Components

### 1. API Layer (`main_api_cloud.py`)

The entry point for the application. It exposes a `/search` endpoint.

-   **Inputs**:
    -   `q`: The user's question.
    -   `content_type`: "latest" (default) or "all".
    -   `debug`: Boolean to return full LLM debug info.
-   **Logic**:
    -   Calculates a `latest_weight` using `get_latest_flag`. If the query implies a need for recent data (e.g., "current inflation"), the weight is increased.
    -   Delegates the core logic to the `Inquirer` class.

### 2. The Inquirer (`cloud_llm.py`)

This class orchestrates the entire RAG flow.

#### A. Retrieval (`similarity_search`)
-   Queries the FAISS index using the embedding model (`sentence-transformers/all-MiniLM-L6-v2`).
-   **Latest Filter**: If `content_type="latest"`, it queries `db_langchain_latest` (if available/configured) or applies logic to favor recent docs. *Note: The code currently loads two separate DBs: `db` and `db_latest`.*

#### B. Reranking (Time Decay)
-   **Function**: `make_query` -> `time_decay`
-   **Logic**: If `latest_weight > 0`, the similarity score (L2 distance) is divided by a decay factor based on the document's publication date.
-   **Effect**: Older documents effectively become "further away" (higher score), pushing recent documents up the rank.

#### C. Context Selection (`query_texts`)
-   **Filtering**: It takes the top `k_contexts` (default 3) documents.
-   **Threshold**: It further filters out documents that are significantly less relevant than the top match (score > 1.5 * top_score).
-   **Formatting**: Formats chunks into a string using `STUFF_DOCUMENT_PROMPT`:
    ```xml
    <Doc1 published_date=2023-05-01 title=Economic Survey> ...content... </Doc1>
    ```

#### D. Generation & Parsing
-   **Prompt**: Uses `EXTRACTIVE_PROMPT_PYDANTIC` from `prompts_cloud.py`.
-   **Constraint**: The prompt explicitly instructs the LLM to answer *only* based on the provided context and to be impartial.
-   **Structured Output**: The LLM is forced to return a JSON object (via Pydantic) containing:
    -   `answer_provided`: Boolean.
    -   `answer`: The synthesized text.
    -   `highlighting`: Exact phrases from the source text used to derive the answer.

### 3. Highlighting (`utils.py`)

After the LLM responds, the `highlighter` function scans the original retrieved documents for the "highlighting" phrases returned by the LLM. It marks these sections, allowing the UI to show exactly where the information came from.

## Key Concepts

### Time Decay
To ensure users get the most relevant statistics, the system doesn't rely solely on semantic similarity. A "decay" function penalizes older documents. This is crucial for queries like "What is the GDP?", where the 2024 report is far more relevant than the 2018 report, even if the 2018 text is semantically identical.

### Structured Output (Pydantic)
Instead of free-text output, we force the LLM to adhere to a schema (`LlmResponse`). This is vital for:
1.  **Reliability**: Ensuring we know if the LLM actually found an answer (`answer_provided`).
2.  **Citations**: Extracting exact quotes for the highlighting feature.
