# Guide: Flask Demo Frontend

This guide explains what the restored Flask frontend does, how to run it, and
how to interpret what it shows.

## Purpose

The Flask app in [`flask-app/`](../../flask-app)
is a lightweight browser frontend for demoing StatsChat-KE.

It is useful when you want:

- a simple search box instead of calling `/search` manually
- a stakeholder-friendly view of answers and references
- a quick way to demo the cloud or local FastAPI backend

It is **not** the benchmark source of truth. Accuracy evaluation still comes
from:

- the audited workbook in [`tests/accuracy/`](../../tests/accuracy)
- the evaluator in [`tests/accuracy/evaluate_accuracy.py`](../../tests/accuracy/evaluate_accuracy.py)

## What The Frontend Does

The frontend sends a query to a running StatsChat API and renders:

- the answer in a highlighted answer card
- an `Exact cited source` when a grounded page can be identified confidently
- a `Generation context source(s)` fallback when no single exact page can be shown safely
- the broader retrieved references list underneath
- a friendlier demo refusal message for unsupported questions

## Important Boundary

The Flask frontend includes **demo-only presentation logic**.

That means:

- benchmark semantics are unchanged
- API semantics are unchanged
- evaluator refusal handling is unchanged

Examples of demo-only behavior:

- a blank refusal is rendered as a human-readable sentence
- visible references can be preferred over a noisier backend citation when they clearly contain the answer-bearing fact

## Prerequisites

Before starting the Flask app, make sure:

1. your Python environment is active
2. the vector store already exists
3. the backend API you want to demo is running
4. required API credentials are configured if you are using cloud mode

Environment setup is documented in:

- [`docs/environment_setup.md`](./environment_setup.md)
- [`docs/setup_guide.md`](./setup_guide.md)

## Run The Backend

Choose one backend mode.

### Cloud API

```bash
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001
```

### Local API

```bash
uvicorn fast-api.main_api_local:app --host 127.0.0.1 --port 8000
```

You can confirm which model is active with:

```bash
curl http://127.0.0.1:8001/health
```

or:

```bash
curl http://127.0.0.1:8000/health
```

## Run The Flask Frontend

Point the frontend at the backend you want to use.

### Against the cloud API

```bash
STATSCHAT_FRONTEND_API_URL=http://127.0.0.1:8001 .venv/bin/python flask-app/app.py
```

### Against the local API

```bash
STATSCHAT_FRONTEND_API_URL=http://127.0.0.1:8000 .venv/bin/python flask-app/app.py
```

If API authentication is enabled on the backend, also pass:

```bash
STATSCHAT_API_KEY=your_key_here
```

The Flask app will then be available at:

```text
http://127.0.0.1:5000
```

> **macOS note:** If port 5000 is already in use (commonly by AirPlay Receiver),
> either disable AirPlay Receiver in **System Settings → General → AirDrop & Handoff**,
> or start the app on a different port:
>
> ```bash
> STATSCHAT_FRONTEND_API_URL=http://127.0.0.1:8001 FLASK_RUN_PORT=5001 .venv/bin/python flask-app/app.py
> ```

## Environment Variables

The frontend supports these runtime variables:

| Variable | Purpose |
|---|---|
| `STATSCHAT_FRONTEND_API_URL` | Backend API base URL, for example `http://127.0.0.1:8001` |
| `STATSCHAT_API_KEY` | Optional API key forwarded as `X-API-Key` |
| `STATSCHAT_FRONTEND_TIMEOUT` | Optional request timeout in seconds |
| `FLASK_SECRET_KEY` | Flask session signing key; set to a long random string in any shared or deployed environment |
| `FLASK_RUN_PORT` | Override the default port (5000); useful when AirPlay Receiver is active on macOS |

## How To Read The Page

### Answer

This is the answer returned by the backend. For unsupported questions, the
frontend may replace an empty backend answer with a clearer demo refusal
sentence.

### Exact cited source

This is the page the frontend believes best grounds the answer.

It may come from:

- the backend’s explicit citation metadata, or
- a demo-layer match against the visible reference pages when those pages more clearly contain the answer-bearing fact

### Generation context source(s)

This appears when the backend selected multiple pages for answer generation and
the frontend cannot safely collapse them into one exact source.

### Most relevant publication(s)

This is the broader retrieval list returned by the backend. These pages are
useful context, but they are not always identical to the exact answer-bearing
page shown in the answer card.

## Known Behaviors

### Cached queries can show `0.0 seconds`

The cloud query path uses caching. If you ask the exact same question again,
`Backend response time: 0.0 seconds` can appear. For demos, use a fresh
question if you want a more realistic latency.

### PDF page number vs printed report page number

Some documents have internal printed page numbers that differ from the PDF page
index shown in the UI. This is expected. The frontend displays the page number
carried through the retrieval metadata.

### Table-heavy pages can look noisy

Some retrieved contexts come from table-like PDF extractions. The answer can
still be correct even if a lower reference preview looks raw.

## Recommended Demo Queries

Good answerable examples:

- `What was Kenya's year on year inflation rate in January 2024?`
- `What was headline inflation for December 2019?`
- `What was Kenya's inflation rate in April 2025?`
- `How many births were registered in Kenya in 2023?`

Good unsupported example:

- `What is the salary of the KNBS Director General?`

## Tests

Focused tests for the demo frontend and its citation logic:

```bash
.venv/bin/python -m pytest tests/unit/test_flask_app.py tests/unit/generative/test_cloud_llm.py -q
```

## Related Files

- [`flask-app/app.py`](../../flask-app/app.py)
- [`flask-app/templates/statschat.html`](../../flask-app/templates/statschat.html)
- [`fast-api/main_api_cloud.py`](../../fast-api/main_api_cloud.py)
- [`fast-api/main_api_local.py`](../../fast-api/main_api_local.py)
- [`statschat/generative/cloud_llm.py`](../../statschat/generative/cloud_llm.py)
