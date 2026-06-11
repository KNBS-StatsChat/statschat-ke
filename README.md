# `KNBS StatsChat`

[![Stability](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental)
[![Shared under the MIT License](https://img.shields.io/badge/license-MIT-green)](https://github.com/datasciencecampus/Statschat/blob/main/LICENSE)
[![Mac-OS compatible](https://shields.io/badge/MacOS--9cf?logo=Apple&style=social)]()

## Code state

> [!WARNING]
> Please be aware that for development purposes, these experiments use
> experimental Large Language Models (LLM's) not intended for production. They
> can present inaccurate information, hallucinated statements and offensive
> text by random chance or through malevolent prompts.

- **Under development** / **Experimental**
- **Tested on macOS only**
- **Peer-reviewed**
- **Depends on external API's**

## Introduction

This is an experimental application for semantic search of KNBS [statistical publications](https://www.knbs.or.ke/all-reports/).
It uses LangChain to implement a fairly simple Retrieval Augmented Generation (RAG) using embedding search
and QA information retrieval process.

Upon receiving a query, documents are returned as search results
using embedding similarity to score relevance.
Next, the relevant text is passed to a Large Language Model (LLM),
which is prompted to write an answer to the original question, if it can,
using only the information contained within the documents.

PDFs are scraped from the KNBS website and stored locally. Text is extracted, chunked, and embedded into a FAISS vector store (paths configured in `statschat/config/main.toml`). The LLM is either run locally with `local_llm.py` or through the FastAPI backend (`main_api_local.py` or `main_api_cloud.py`).

## Overview
<img width="1661" height="580" alt="image" src="https://github.com/user-attachments/assets/34eb5fbd-0965-48f8-acd3-bcc7ee945de2" />


## Step 1: Environment Configuration
> [!IMPORTANT]
> **Before running the application, you must:**
> 1. **[Create a virtual or conda environment](./docs/guides/setup_guide.md)**
> 2. **[Set up your `.env` file with API credentials](./docs/guides/environment_setup.md)**

## Step 2: Vector store
> [!NOTE]
> **Ensure the environment has been configured before setting up or updating the vector store.**

Before running `pdf_runner.py`, ensure the `mode` key under `[preprocess]` in `statschat/config/main.toml` is set to the desired option. It can also be run from the command line:

```shell
python statschat/pdf_runner.py
```

This script scrapes PDF documents from the KNBS website, converts them to JSON files, and either populates or updates the vector store — depending on the `mode` setting.

`mode = "SETUP"` — Scrapes all PDFs from the KNBS website and builds the vector store from scratch. Only needed once for initial setup or a full rebuild.

`mode = "UPDATE"` — Scrapes only the latest pages of PDFs, compares them against existing files, and appends only new documents to the vector store. Use this for routine data refreshes when new reports are published.

## Step 3: Usage

#### Run the sample questions manually (backend)

This assumes the [vector store](./docs/guides/setup_guide.md) has already been created — see Step 2 if not.
Make sure your terminal is running from **`statschat-ke`**. Then use the **`cloud_llm.py`**
(requires configured cloud API credentials) or **`local_llm.py`** script and change the **question** parameter
with the desired question:

```shell
# Cloud LLM (faster, uses the provider/model configured in main.toml)
python statschat/generative/cloud_llm.py

# Local LLM (slower, runs Mistral-7B locally)
python statschat/generative/local_llm.py
```

> [!TIP]
> To keep the shared repo default on the free OpenRouter model but use a paid model locally,
> set `STATSCHAT_GENERATIVE_MODEL` in your `.env` file. Example:
> `STATSCHAT_GENERATIVE_MODEL=mistralai/mistral-nemo`
>
> To go back to the repository default model, remove `STATSCHAT_GENERATIVE_MODEL` from your `.env` file.

> [!NOTE]
> **Local LLM Performance:** Running Mistral-7B locally requires ~16GB RAM and takes 3-5 minutes per query.
> The model may occasionally fail to produce valid JSON output - in this case, the relevant documents
> found will still be displayed. For faster, more reliable responses, use `cloud_llm.py`.

![image](https://github.com/user-attachments/assets/36ec03e4-2d6a-4814-9220-8cc478196e52)

The answer, context and response will be output in the terminal.

#### Run interactive Statschat API
The `statschat` module can be deployed as a FastAPI backend. `fastapi` and `uvicorn` are included in the dev dependencies (`pip install -e ".[dev]"`). Ensure your terminal is in the **`statschat-ke`** folder, then start the server:

If you want the browser-based demo UI, use:

- [`docs/guides/flask_demo_frontend.md`](docs/guides/flask_demo_frontend.md)

That guide covers:

- what the Flask app is for
- how to run it against local or cloud API mode
- demo-only behavior such as refusal messaging and answer-card citations
- the focused tests for the restored frontend


```shell
uvicorn fast-api.main_api_local:app --reload
```

or

```shell
uvicorn fast-api.main_api_cloud:app --reload
```

For deployed API instances, configure access and browser origins with runtime
environment variables rather than committing secrets:

```shell
export OPENROUTER_API_KEY=...
export STATSCHAT_API_KEY=...
export STATSCHAT_CORS_ORIGINS=http://localhost:5000,https://your-frontend.example
export STATSCHAT_RATE_LIMIT_PER_MINUTE=10
```

When `STATSCHAT_API_KEY` is set, `/search` and `/feedback` require either an
`X-API-Key` header or an `Authorization: Bearer ...` header. `/health` remains
public and returns non-secret runtime status for monitoring.

The API listens on a local port. You will see the address in your terminal:

 ```shell
 Uvicorn running on http://127.0.0.1:8000
 ```

> [!NOTE]
> **Your port might be slightly different to 127.0.0.1:8000**

After a few seconds you should be able to go to your browser and ask questions.
On the search bar type something like:

```
http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023
```

This should produce a response text that is displayed on your browser.

The generic formula to ask a question is:

```
<API_URL>/search?q=<your_question>
```

# License

<!-- Unless stated otherwise, the codebase is released under [the MIT Licence][mit]. -->

The code, unless otherwise stated, is released under [the MIT License][mit].

[mit]: LICENSE
