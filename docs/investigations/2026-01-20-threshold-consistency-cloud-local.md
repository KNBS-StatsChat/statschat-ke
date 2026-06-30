# 2026-01-20 — Threshold consistency (cloud vs local)

## Summary

We observed inconsistent user-facing responses when retrieval quality was low:

- The **cloud** path could say “Please check the link(s) provided” even when the system had replaced `references` with placeholder strings (no URLs).
- The **local** path could raise an exception when fewer than two retrieved chunks were returned (it indexed `[1]` unconditionally), and it did not have a clear “no suitable PDFs” behavior.

This investigation documents the changes made to make low-quality retrieval behavior more consistent and robust.

## What changed

### Cloud path (`Inquirer.make_query`)

- File: `statschat/generative/cloud_llm.py`
- Behavior: when `document_threshold` triggers (i.e., “no suitable PDFs found”), the code already replaced `references` with placeholder strings.
- Change: we also now adjust the returned `answer` string in the same branch so it no longer suggests checking links.

Rationale: keep response fields consistent (don’t tell users to check links if we are not returning link references).

### Local path (`/search` endpoint)

- File: `fast-api/main_api_local.py`
- Added safeguards and threshold handling:
  - Handle **no retrieval results** without throwing.
  - Handle **<2 retrieved chunks** without throwing (prompt now uses the second context only if present).
  - Respect `content_type` by passing `latest_filter=(content_type == "latest")` into retrieval.
  - Apply `answer_threshold` and `document_threshold` from config at the API layer:
    - If “no suitable PDFs”, return a consistent message and empty `references`.
    - If “context too weak for an answer”, return a generic “no suitable answer” message (but keep the first link when available).

Rationale: make local mode resilient (no index errors) and make “weak retrieval” behavior more aligned with cloud mode.

## Tests

- Integration test suite: `tests/integration/test_api_search.py`
- Result: all tests passed after changes.

## Open questions / future improvements

- The local and cloud endpoints still differ in response schema (cloud returns `references` as a list of dicts; local returns a single string URL plus extra fields). If we want one stable public API, we should standardize these schemas.
- Consider moving local retrieval and threshold logic into a shared helper to avoid divergence.
