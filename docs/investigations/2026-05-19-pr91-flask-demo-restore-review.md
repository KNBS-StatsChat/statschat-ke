# PR #91 Code Review — Flask Demo Frontend Restore

**Branch:** `demo-flask-restore`
**PR:** [Restore Flask demo frontend with grounded citation display](https://github.com/KNBS-StatsChat/statschat-ke/pull/91)
**Review date:** 2026-05-19
**Reviewer:** GitHub Copilot (automated review)

---

## Summary

PR #91 restores the `flask-app/` frontend subtree, improves citation grounding in
`statschat/generative/cloud_llm.py`, adds backend response timing to both API
files, and adds documentation and tests for the new demo behaviour. The scope
boundary (demo-only changes; benchmark semantics unchanged) is clearly stated
and appears to be respected in the code.

The fixes below were applied as part of reviewing this PR.

---

## Issues Fixed (Red — applied on 2026-05-19)

### 1. Hardcoded Flask `SECRET_KEY`

**File:** `flask-app/app.py`, line 43

**Before:**
```python
app.config["SECRET_KEY"] = "secret!"
```

**After:**
```python
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
```

**Why:** A hardcoded secret key is an OWASP A02 (Cryptographic Failures) violation.
Flask signs session cookies with this key. Any attacker who knows the key can
forge session cookies, which here carry the user's `question`, `content_type`,
and `answer`. The `flask-app/Dockerfile` shows this app is intended for
deployment, making the risk concrete. The fix reads the key from `FLASK_SECRET_KEY`
in the environment and falls back to a per-process random key (which invalidates
sessions on restart — acceptable for a demo). For persistent sessions across
restarts, operators should set `FLASK_SECRET_KEY` explicitly.

The `FLASK_SECRET_KEY` variable has also been added to the environment variables
table in `docs/guides/flask_demo_frontend.md`.

---

### 2. No error handling in `record_rating`

**File:** `flask-app/app.py`, `record_rating()` route

**Before:**
```python
requests.post(
    ENDPOINT.rstrip("/") + "/feedback",
    json=last_answer,
    headers=api_headers(),
    timeout=REQUEST_TIMEOUT,
)
```

**After:**
```python
try:
    requests.post(
        ENDPOINT.rstrip("/") + "/feedback",
        json=last_answer,
        headers=api_headers(),
        timeout=REQUEST_TIMEOUT,
    )
except requests.exceptions.RequestException as e:
    logger.warning("FEEDBACK-FAIL: %s", e)
```

**Why:** The `search` route already wraps its `requests.get` call in a
`try/except`. The `record_rating` route was missing equivalent protection.
If the backend is unreachable when a user submits feedback, the unhandled
`RequestException` would cause an unhandled 500 error instead of a graceful
no-op. The fix logs the failure and returns the normal 204 response.

---

### 3. Absolute machine-specific paths in documentation

**Files affected:**
- `README.md`
- `docs/guides/flask_demo_frontend.md`
- `docs/reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md`

All markdown links in the new and modified documentation used absolute paths
anchored to the author's local filesystem (`/Users/EjlliD/Developer/statschat-ke/...`).
These paths resolve only on the author's machine. They appear broken on GitHub,
in rendered docs viewers, and for every other developer.

All affected links have been replaced with repo-relative paths. For example:

| Before | After |
|---|---|
| `/Users/EjlliD/Developer/statschat-ke/docs/guides/flask_demo_frontend.md` | `docs/guides/flask_demo_frontend.md` |
| `/Users/EjlliD/Developer/statschat-ke/flask-app/app.py` | `../../flask-app/app.py` |
| `/Users/EjlliD/Developer/statschat-ke/tests/accuracy/README.md` | `../../tests/accuracy/README.md` |

A total of 16 broken links were corrected across the three files.

**Note:** One pre-existing broken absolute path was found in
`tests/accuracy/README.md` (line 910, pointing to
`docs/investigations/2026-04-09-evidence-span-evaluator-limitations.md`).
This was not introduced by PR #91 and is not fixed here, but it should be
addressed in a follow-up.

---

## Issues Not Fixed — Recommended Follow-Up (Amber)

### A. `__dict__` mutation on `LlmResponse`

**File:** `statschat/generative/cloud_llm.py`, `query_texts()` method

The citation metadata (`generation_context_sources`, `exact_cited_source`,
`where_context_from`, `context_reference`) is attached to the validated
response object by directly writing to `validated_answer.__dict__`. This is
fragile: it breaks if `LlmResponse` ever uses `__slots__`, becomes a Pydantic
model, or is frozen. It also makes the object's shape implicit rather than
declared.

**Recommended fix:** Add optional fields to `LlmResponse` for these keys, or
return the citation metadata separately from `query_texts()` as a second value
or a wrapper dataclass. This avoids the need for `__dict__` mutation and makes
the data contract explicit.

---

### B. `app.run(host="0.0.0.0")` in `flask-app/app.py`

**File:** `flask-app/app.py`, last line

The Flask dev server binds to all network interfaces by default. For a local
demo app this is unexpected — `"127.0.0.1"` is safer and makes the scope
explicit. Note that `gunicorn` in the Dockerfile uses `:$PORT` which also
binds to all interfaces; that is intentional for container deployment and does
not need changing, but the direct dev-server invocation should use loopback.

---

### C. `gpt-5.4-mini` model name in docs

**Files:**
- `docs/reports/2026-06-knbs-festival-demo-recommendations.md`
- `docs/reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md`

Both documents reference `openai/gpt-5.4-mini` as the recommended production
model. This model name does not correspond to any model available on OpenRouter
or directly from OpenAI as of May 2026. It is likely a hallucinated or
placeholder name. The current default model is visible in
`statschat/config/main.toml` and should be used as the reference in docs instead.

This is a documentation accuracy issue rather than a code defect, but it could
cause confusion for KNBS operators following the guidance.

---

### D. Bootstrap 3.3.7 CDN in `ons_layout.html`

**File:** `flask-app/templates/ons_layout.html`

The template loads Bootstrap 3.3.7 from the MaxCDN CDN. Bootstrap 3.3.7 is
from 2016, is end-of-life, and has known XSS-related vulnerabilities in
its JavaScript tooltip and popover components. For a demo app with
`<meta name="robots" content="noindex">` the practical risk is low, but it
should be upgraded if the app is ever opened beyond internal use.

---

### E. No CI status checks on the PR

PR #91 has no automated status checks. The "50 passed" claim in the PR
description comes from a local run only. Adding a GitHub Actions workflow
(even a minimal one running `pytest tests/unit/`) would give reviewers and
future contributors confidence that the test suite remains green on the branch.

---

## Test Coverage

The PR adds:
- `tests/unit/test_flask_app.py` — 6 focused tests for demo-layer citation
  logic and refusal rendering
- New test in `tests/unit/generative/test_cloud_llm.py` for the
  answer-bearing-page preference logic

Both test files focus correctly on the demo-only behaviour that differs from
the benchmark path. Coverage of the `record_rating` route and the
`normalise_references` helper would be a useful addition.

---

## Verdict

The PR is well-scoped and the citation grounding logic is sound. With the
three red-flag fixes applied (secret key, error handling, broken links), the
PR is safe to merge for demo use. The amber items (especially `__dict__`
mutation and the model name in docs) are worth addressing before any wider
rollout.
