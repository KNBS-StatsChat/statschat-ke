# 2026-01-29 — Cloud API answer formatting and references contract

## Summary

When running the cloud retrieval + generation path (either via the `/search` endpoint in the cloud API or directly by executing `statschat/generative/cloud_llm.py`), the returned `answer` was formatted as an HTML snippet prefixed with a quote-oriented string, and the "no suitable PDFs" branch replaced `references` with placeholder strings.

For a KNBS website/chat UI, the desired behaviour is:

- `answer`: human-readable plain text (safe to render directly)
- `references`: always a list of retrieved chunk objects (or an empty list)

This investigation documents what was happening, what was changed (cloud only), and why.

## Context

User-visible output comes from the cloud API endpoint:

- Cloud API entry point: [fast-api/main_api_cloud.py](../../fast-api/main_api_cloud.py)
- Cloud generator/retriever: [statschat/generative/cloud_llm.py](../../statschat/generative/cloud_llm.py)

The API essentially returns whatever the generator produces:

- `answer` is whatever `Inquirer.make_query(...)` returns as `answer_str`
- `references` is whatever `Inquirer.make_query(...)` returns as `docs`

## What was happening before

### 1) `answer` returned HTML and quote-oriented framing

In the cloud generator, when an answer was provided (`answer_provided=True`), the code constructed `answer_str` like:

- Literal prefix: `"Most relevant quote from publications below: "`
- Followed by HTML wrapper: `<h4 ...><div id="answer">{most_likely_answer}</div></h4>`

This meant that API consumers (including a future website/chat client) received HTML inside the `answer` field.

In practice, for the GDP question:

- `most_likely_answer` was often just the short value (e.g., `"4.7%"`)
- the full human-readable sentence existed in retrieved chunk text and/or the response highlights

### 2) `references` was sometimes replaced with placeholder strings

When the top retrieved score was worse than `document_threshold`, the cloud generator:

- Overwrote the answer with a "No suitable PDFs" message
- Cleared the retrieved list of dicts
- Replaced it with two strings:
  - `"No suitable PDFs found. Please refer to context"`
  - `"No context available. Please refer to response"`

That broke a stable schema expectation for clients because `references` changed type from:

- `list[dict]` (normal case)
- to `list[str]` (no-PDFs case)

## Goal

For a KNBS web/chat UI, the contract should be stable and safe:

- `answer` should be plain text and directly displayable
- `references` should always be a list of chunk objects (or an empty list)
- threshold messaging can remain as-is (the text is fine), but types should not change

## Changes made (cloud only)

### 1) `answer` is now plain text

File: [statschat/generative/cloud_llm.py](../../statschat/generative/cloud_llm.py)

Changed `answer_str` construction to:

- Prefer `validated_response.highlighting1[0]` if available (this is typically a complete sentence grounded in the retrieved context)
- Strip simple HTML tags from that highlight (and from `most_likely_answer` as a fallback)
- Add a trailing period if the highlight does not already end with punctuation

Result: for the GDP question, the answer becomes something like:

- `"In 2024, Kenya’s real Gross Domestic Product (GDP) grew by 4.7 per cent."`

This is suitable for a website/chat UI without relying on HTML rendering.

### 2) `references` is empty on "no suitable PDFs"

File: [statschat/generative/cloud_llm.py](../../statschat/generative/cloud_llm.py)

Changed the `document_threshold` branch to:

- Keep the existing user-facing message in `answer`
- Return `references: []` (empty list)

This avoids placeholder strings and maintains a stable `references` schema.

### 3) Documentation updated

File: [docs/architecture/pipeline-input-output.md](../architecture/pipeline-input-output.md)

Updated the I/O doc to reflect the target/implemented contract:

- `answer` is plain text
- `references` is always a list of chunk objects (or empty)
- `document_threshold` now results in `references: []` (not placeholder strings)

## Verification

Verified via a direct call to the cloud `Inquirer.make_query(...)` for:

- Question: "By how much did Kenya's GDP grow in 2024?"

Observed:

- `answer` is plain text (human-readable sentence)
- `references` is a Python list of dicts (chunk objects) when retrieval succeeds

Also verified the `document_threshold` no-PDFs case returns:

- `references == []`

## Notes and future work

- This work intentionally changes **cloud only**.
- The local API path ([fast-api/main_api_local.py](../../fast-api/main_api_local.py)) still has a different output shape (`references` as a single URL string plus additional context fields). If we want full consistency across cloud/local, we can later:
  - make local return `references: list[chunk]` as well
  - make local `answer` follow the same plain-text policy
  - standardize threshold handling and response schema in one place

## Rationale

These changes are intentionally minimal and focused:

- They do not alter retrieval logic, thresholds, chunking, or embeddings.
- They make the API contract safer for direct web rendering.
- They eliminate type-instability in `references`, which is a common source of frontend bugs.
