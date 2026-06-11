# Configuration Guide for StatsChat

This guide explains the configuration options for StatsChat. The configuration file uses the [TOML](https://toml.io/en/) format and is divided into several sections:

## `[db]`

- **faiss_db_root**: Path to the root directory for the FAISS database.
- **embedding_model_name**: Name of the embedding model used for vector representations.

## Index Artifacts And Team Rebuilds

The repository does not normally carry the full `data/` directory or the FAISS
index files, because these are large, local build artifacts. Pulling the code
therefore updates the configured paths, but it does not guarantee that the
matching local index exists on each developer's machine.

The current configuration expects the April 2026 rebuilt index:

- **Split JSON directory**: `data/json_split_rebuild_v1`
- **FAISS index root**: `data/db_langchain_rebuild_v1`
- **Embedding model**: `sentence-transformers/all-mpnet-base-v2`
- **Split length**: `1000`
- **Split overlap**: `150`
- **Preprocess mode for full rebuild**: `SETUP`

If a colleague does not have `data/db_langchain_rebuild_v1` locally, the API
will not be using the same retrieval index as the accuracy report. They should
either obtain the April 2026 rebuilt `data/` artifacts from the shared project
artifact store, or rebuild the index using the settings above. Rebuilding with
different split sizes, overlap, source PDFs, or embedding model can change
retrieval behavior and make accuracy results non-comparable.

## `[preprocess]`

- **mode**: Set to `"UPDATE"` to update the database with new data.  Use `"SETUP"` to build the database from scratch.
- **data_dir**: Directory containing and used to store the source data.
- **download_dir**: Directory where downloaded PDFs are stored.
- **directory**: Directory for JSON conversions of the data.
- **split_directory**: Directory for storing split JSON files.
- **split_length**: Maximum number of characters per split document.
- **split_overlap**: Number of overlapping characters between splits.
- **latest_only**: If `true`, only process the latest files.

## `[search]`

- **generative_model_name**: Legacy fallback model id if a mode-specific model is not set.
- **generative_model_name_local**: Model id used by the local API/runtime.
- **generative_model_name_cloud**: Model id used by the cloud API/runtime.
- **k_docs**: Number of top documents to retrieve per search.
- **k_contexts**: Number of context passages to use.
- **similarity_threshold**: Minimum similarity score for a document to be considered relevant.
- **llm_temperature**: Temperature parameter for the language model (controls randomness).
- **llm_max_tokens**: Shared fallback output-token cap if mode-specific caps are not set.
- **llm_max_tokens_cloud**: Cloud-generation output-token cap. Keep this high enough for structured JSON responses. GPT-5.4-mini has fit comfortably under `1024` in audited runs. Historically, Mistral Small 3.1 needed `2048+` to avoid truncation, but by May 2026 the OpenRouter route for `mistralai/mistral-small-3.1-24b-instruct` appeared unstable for structured JSON even at that higher cap. For current Mistral-family comparisons, prefer `mistralai/mistral-small-24b-instruct-2501` or `mistralai/mistral-small-3.2-24b-instruct`.
- **llm_max_tokens_local**: Local-generation output-token cap for the Hugging Face path.
- **answer_threshold**: Minimum score for an answer to be returned.
- **document_threshold**: Minimum score for a document to be included in results.

## `[app]`

- **latest_max**: Maximum number of latest documents to consider (commonly 0, 1, or 2).
- **page_start**: Sets where to start looking for downloads. Higher the number the older the publications.
- **page_end**: Sets where to stop looking for downloads. Higher the number the older the publications.

Adjust these settings to fit your data and use case. Save your changes and restart the application for them to take effect.

---

## Current Parameter Values (Reference)

The table below shows the current values from `statschat/config/main.toml` and what each parameter does at runtime. These are the settings that produced the April 2026 audited benchmark results.

| Parameter | Current Value | Notes |
|---|---|---|
| `faiss_db_root` | `data/db_langchain_rebuild_v1` | FAISS index built in April 2026. See [Index Artifacts](#index-artifacts-and-team-rebuilds) above. |
| `embedding_model_name` | `sentence-transformers/all-mpnet-base-v2` | Must match the model used to build the index. Do not change without rebuilding. |
| `mode` | `SETUP` | Set to `UPDATE` for incremental runs. |
| `split_length` | `1000` | Characters per chunk. |
| `split_overlap` | `150` | Overlap between adjacent chunks. |
| `generative_model_name_cloud` | `openai/gpt-5.4-mini` | Cloud API model. |
| `generative_model_name_local` | `mistralai/Mistral-7B-Instruct-v0.3` | Local API model (loaded via Hugging Face). |
| `k_docs` | `8` | Documents retrieved from FAISS per query. |
| `k_contexts` | `5` | Documents passed to the LLM for answer generation. |
| `similarity_threshold` | `2.0` | L2 distance cap; lower is stricter. |
| `llm_temperature` | `0.0` | Deterministic generation. |
| `llm_max_tokens` | `2048` | Fallback output-token cap. |
| `answer_threshold` | `1.1` | Minimum reranker score to return an answer. Scores below this return an empty answer. |
| `document_threshold` | `0.9` | Minimum reranker score to include a document in references. |
| `latest_max` | `2` | Number of publications treated as "latest" for `content_type=latest` queries. |
| `page_start` / `page_end` | `1` / `5` | KNBS website page range to scrape. |

> **Note on thresholds**: `answer_threshold` and `document_threshold` are applied to the cross-encoder reranker score. These scores are not probabilities; their absolute range depends on the reranker model. See [docs/architecture/threshold-guide.md](./architecture/threshold-guide.md) for detail on how the three-zone response behaviour works.
