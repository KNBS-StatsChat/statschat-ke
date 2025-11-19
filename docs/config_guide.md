# Configuration Guide for StatsChat

This guide explains the configuration options for StatsChat. The configuration file uses the [TOML](https://toml.io/en/) format and is divided into several sections:

## `[db]`

- **faiss_db_root**: Path to the root directory for the FAISS database.
- **embedding_model_name**: Name of the embedding model used for vector representations.

## `[preprocess]`

- **mode**: Set to `"UPDATE"` to update the database with new data.  Use `"SETUP"` to build the database from scratch.
- **data_dir**: Directory containing and used to store the source data.
- **download_dir**: Directory where downloaded PDFs are stored.
- **directory**: Directory for JSON conversions of the data.
- **split_directory**: Directory for storing split JSON files.
- **split_length**: Maximum number of characters per split document.
- **split_overlap**: Number of overlapping characters between splits.
- **latest_only**: If `true`, only process the latest files.
- **extractor**: Choose which PDF extractor is used for JSON conversion - `pypdf`,`fitz` or `pdfplumber`

## `[search]`

- **generative_model_name**: Name of the generative model used for answering queries.
- **k_docs**: Number of top documents to retrieve per search.
- **k_contexts**: Number of context passages to use.
- **similarity_threshold**: Minimum similarity score for a document to be considered relevant.
- **llm_temperature**: Temperature parameter for the language model (controls randomness).
- **answer_threshold**: Minimum score for an answer to be returned.
- **document_threshold**: Minimum score for a document to be included in results.

## `[app]`

- **latest_max**: Maximum number of latest documents to consider (commonly 0, 1, or 2).
- **page_start**: Sets where to start looking for downloads. Higher the number the older the publications.
- **page_end**: Sets where to stop looking for downloads. Higher the number the older the publications.

Adjust these settings to fit your data and use case. Save your changes and restart the application for them to take effect.
