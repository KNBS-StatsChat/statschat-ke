# Investigation: `time_decay` date format mismatch — soft bias was a no-op

**Date:** 2026-03-21

## Summary

The `time_decay()` function in `statschat/generative/utils.py` expected ISO-format dates (e.g. `"2024-03-01"`) but FAISS metadata stores dates in `"%d %B %Y"` format (e.g. `"01 March 2024"`). Every call silently failed and returned a neutral `1.0`, meaning **the recency soft bias has never been applied to any query**.

This was discovered while investigating the separate `/ vs *` operator bug (see [2026-03-13-time-decay-reweighting-bug.md](2026-03-13-time-decay-reweighting-bug.md)).

## Root cause

Two components disagreed on the date format:

| Component | Format | Example |
|---|---|---|
| `preprocess.py` (embedding time) | `datetime.strptime(release_date, "%Y-%m-%d").__format__("%d %B %Y")` | `"01 March 2024"` |
| `time_decay()` in `utils.py` (query time) | `datetime.fromisoformat(date_str)` | expects `"2024-03-01"` |

When `fromisoformat("01 March 2024")` was called, it raised `ValueError`. The bare `except Exception` caught it and returned `1.0` (neutral — no decay). This happened on every document, every query.

## Verification

```python
from datetime import datetime
datetime.fromisoformat("01 March 2024")
# ValueError: Invalid isoformat string: '01 March 2024'
```

Confirmed the soft bias was a no-op:
- `time_decay("01 March 2024", latest=1.0)` → `1.0` (failed silently)
- `time_decay("2024-03-01", latest=1.0)` → `3.05` (would have worked)

## Fix

Updated `time_decay()` in `statschat/generative/utils.py`:

1. **Primary parse**: `datetime.strptime(date_str, "%d %B %Y")` — matches FAISS metadata format.
2. **Fallback**: `datetime.fromisoformat(date_str)` — for any code paths that supply ISO dates.
3. **Warning on failure**: `logger.warning(...)` instead of a bare `except` returning `1.0` silently.

```python
def time_decay(date_str: str, latest: float = 1.0) -> float:
    try:
        doc_date = datetime.strptime(date_str, "%d %B %Y")
    except (ValueError, TypeError):
        try:
            doc_date = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            logger.warning("time_decay: unparseable date '%s', returning neutral 1.0", date_str)
            return 1.0
    days_old = (datetime.now() - doc_date).days
    decay = 1 + (days_old / 365.0) * latest
    return decay
```

## Related changes in this commit

- **Operator fix** (`cloud_llm.py`): `/ time_decay(...)` → `* time_decay(...)` — documented separately in [2026-03-13-time-decay-reweighting-bug.md](2026-03-13-time-decay-reweighting-bug.md). Both fixes needed to be in place for the soft bias to function correctly.
- **Narrowed exception handling**: replaced bare `except Exception` with specific `(ValueError, TypeError)` catches.
- **Added logging**: `import logging` and `logger = logging.getLogger(__name__)` added to `utils.py`.

## Impact

- The recency soft bias now actually functions for the first time.
- With `latest_max = 2` (config default) and the `*` operator fix, recent documents are now meaningfully favoured in result ranking.
- The `_extract_month_year` bypass (on g-dev) correctly sets `effective_latest_weight = 0` for date-specific queries, so historical queries remain unaffected.

## Files changed

- `statschat/generative/utils.py` — date parsing fix, logging, narrowed exceptions
