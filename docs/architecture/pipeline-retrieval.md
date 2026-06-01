# Retrieval Pipeline

This document details the third stage of the StatsChat-KE pipeline: retrieving relevant information from the vector store to answer a user's query. This process happens entirely **locally** on the application server.

## Conceptual Overview

Before an AI model can answer a question, the system must find the relevant facts. The Retrieval pipeline is responsible for scoring and filtering document chunks; for how those scores are then used to gate the answer and document output, see [Answer & Document Thresholds](threshold-guide.md).

The pipeline is responsible for:
1.  **Semantic Search**: Converting the user's question into a vector and finding similar content in the FAISS index (populated by the [Embedding Pipeline](pipeline-embedding.md)).
2.  **Reranking**: Adjusting the search results to favor more recent publications (Time Decay).
3.  **Context Selection**: Filtering and formatting the best results into a "prompt" context.

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
      | 2. Raw Document Chunks
      v
[Inquirer: Reranking (Time Decay)]
      |
      | 3. Top k Ranked Chunks
      v
[Inquirer: Context Formatting]
      |
      v
[Final Context String] -> (To Generation Pipeline)
```

## Pipeline Components

### 1. API Layer (`main_api_cloud.py`)

The entry point for the application. It exposes a `/search` endpoint.

-   **Inputs**:
    -   `q`: The user's question.
    -   `content_type`: "latest" (default) or "all".
-   **Logic**:
    -   **Intent Detection**: Uses `get_latest_flag` to check if the user is asking for "current", "latest", or "2024" data.
    -   **Weight Calculation**: Sets a `latest_weight` parameter based on the intent.
    -   **Delegation**: Passes the query and weight to the `Inquirer` class.

### 2. Retrieval Logic (`cloud_llm.py`)

The `Inquirer` class handles the retrieval mechanics.

#### A. Similarity Search (`similarity_search`)
-   **Embedding**: The user's query is embedded using the same model as the documents (`sentence-transformers/all-MiniLM-L6-v2`).
-   **Search**: It queries the local FAISS index (`data/db_langchain`).
-   **Latest Filter**: If `content_type="latest"`, it may query a specific `db_langchain_latest` index if configured, ensuring only the most recent batch of documents is searched.

#### B. Reranking: Time Decay
This is a critical feature for statistical data. A semantic search might find a 2015 report that matches the *words* "GDP Growth" perfectly, but the user likely wants the 2024 report.

-   **Function**: `time_decay` (imported from `statschat.embedding.latest_flag_helpers`)
-   **Logic**:
    -   The system calculates a "decay factor" based on the document's publication date.
    -   The original similarity score (L2 distance) is adjusted by this factor.
    -   **Result**: Older documents are penalized (their "distance" increases), pushing newer documents to the top of the list.

#### C. Context Selection (`query_texts`)
Once the documents are ranked, the system prepares them for the LLM.

-   **Top-K Selection**: It selects the top `k_contexts` (default 3) documents.
-   **Relevance Threshold**: It discards any document that is significantly less relevant than the top match (e.g., score > 1.5 * top_score). This prevents irrelevant noise from confusing the LLM.
-   **Formatting**: The selected chunks are formatted into XML-like tags for the prompt:
    ```xml
    <Doc1 published_date=2023-05-01 title=Economic Survey> ...content... </Doc1>
    ```

## Output

The output of this pipeline is a **Context String** containing the most relevant, up-to-date information available in the database. This string is then passed to the [Generation Pipeline](pipeline-generation.md).
