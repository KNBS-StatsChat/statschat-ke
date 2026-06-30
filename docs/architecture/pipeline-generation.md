# Generation Pipeline

This document details the final stage of the StatsChat-KE pipeline: using a Large Language Model (LLM) to synthesize a human-readable answer from the retrieved context.

For an end-to-end view of what goes into StatsChat (PDFs, chunks, queries) and what comes out (answers and references), see [Input/Output (I/O) Overview](pipeline-input-output.md). For how the `answer_threshold` and `document_threshold` config values control what gets returned, see [Answer & Document Thresholds](threshold-guide.md).

## Conceptual Overview

Once the [Retrieval Pipeline](pipeline-retrieval.md) has identified the relevant facts, the Generation pipeline acts as the "reasoning engine." It sends the user's question and the retrieved context to an LLM, which generates a structured response.

This stage can be implemented in two ways:
1.  **Cloud-Hosted (Primary)**: Using an external API (e.g., OpenAI, OpenRouter).
2.  **Local (Alternative)**: Using a locally running open-source model.

## Data Flow

```ascii
[Context String] + [User Query]
      |
      v
+-----------------------+
|   Prompt Engineering  |
|  (prompts_cloud.py)   |
+-----------------------+
      |
      v
+-----------------------+
|          LLM          |
|   (Cloud or Local)    |
+-----------------------+
      |
      v
[Raw Text Response]
      |
      v
+-----------------------+
|   Response Parsing    |
|      (Pydantic)       |
+-----------------------+
      |
      v
+-----------------------+
|    Highlighting       |
|      (utils.py)       |
+-----------------------+
      |
      v
[Final JSON Response]
```

## Implementation Options

### 1. Cloud-Hosted LLM (Primary)
-   **File**: `statschat/generative/cloud_llm.py`
-   **Mechanism**: Uses `LangChain` to call external APIs.
-   **Providers**: Configurable via `.env` (e.g., `OPENAI_API_KEY`, `OPENROUTER_API_KEY`).
-   **Pros**: High quality, faster inference (no local GPU needed), maintenance-free.
-   **Cons**: Data leaves the premise (privacy), per-token cost.

### 2. Local LLM (Alternative)
-   **File**: `statschat/generative/local_llm.py`
-   **Mechanism**: Uses `HuggingFace Transformers` and `Torch` to run a model on the local server.
-   **Model**: Defaults to `mistralai/Mistral-7B-Instruct-v0.3` (configurable).
-   **Pros**: Complete data privacy, no API costs, works offline.
-   **Cons**: Requires significant hardware (GPU/RAM), slower inference, operational complexity.

*Note: The application defaults to the Cloud implementation (`main_api_cloud.py`).*

## Pipeline Components

### 1. Prompt Engineering (`prompts_cloud.py`)
The system constructs a strict prompt to guide the LLM.

-   **Role**: "You are an AI assistant... based only on specific officially published context."
-   **Task**: "Extract and write an answer... quote a part of the provided context closely."
-   **Constraint**: "If the question cannot be answered... do not provide an answer."

### 2. Structured Output (Pydantic)
Instead of free text, we force the LLM to return a JSON object adhering to a specific schema (`LlmResponse`).

-   **Schema**:
    -   `answer_provided` (bool): Did the LLM find the answer?
    -   `answer` (str): The synthesized response.
    -   `highlighting` (list): Exact phrases from the source text used to derive the answer.
-   **Benefit**: This ensures the UI can reliably display citations and handle "no answer" scenarios gracefully.

### 3. Highlighting (`utils.py`)
After the LLM responds, the system performs a post-processing step.

-   **Input**: The `highlighting` phrases returned by the LLM.
-   **Action**: Scans the original retrieved documents to find these exact phrases.
-   **Output**: Marks the character ranges in the source text.
-   **UI Effect**: Allows the user to see exactly which sentence in the PDF supports the AI's claim.
