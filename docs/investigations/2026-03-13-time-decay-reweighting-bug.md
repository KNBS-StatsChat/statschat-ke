# Investigation: `time_decay` reweighting favours old documents instead of new

**Date:** 2026-03-13

## Summary

The post-retrieval recency reweighting in `cloud_llm.py` divided L2 distance scores by `time_decay()` instead of multiplying. This had the effect of **boosting older documents** rather than penalising them, inverting the intended behaviour.

## Background

After FAISS retrieval, `Inquirer.ask()` optionally reweights results using `time_decay()` to bias toward recent publications. FAISS returns L2 distance scores where **lower = more relevant**.

`time_decay()` (in `statschat/generative/utils.py`) returns:

```
decay = 1 + (days_old / 365.0) * latest
```

- A brand-new document → decay ≈ 1.0
- A 5-year-old document with `latest=1` → decay ≈ 6.0

## The bug

The reweighting code was:

```python
doc["score"] = doc["score"] / time_decay(doc["date"], latest=latest_weight)
```

Dividing an L2 distance by a number > 1 makes it **smaller** (i.e. looks more relevant). Older documents have a larger decay divisor, so they received a larger reduction — the opposite of what was intended.

### Worked example (raw L2 score = 0.6 for both)

| Document       | Decay | Old code (`/ decay`) | Correct code (`* decay`) |
|----------------|-------|----------------------|--------------------------|
| New (0 days)   | 1.0   | 0.60 (rank 2)       | 0.60 (rank 1)           |
| Old (5 years)  | 6.0   | 0.10 (rank 1)       | 3.60 (rank 2)           |

With `sort ascending` (lower = better), the old code ranked the 5-year-old document first.

## Fix

Changed `/` to `*` in `statschat/generative/cloud_llm.py` (`ask()` method):

```python
doc["score"] = doc["score"] * time_decay(doc["date"], latest=latest_weight)
```

Updated the inline comment to accurately describe the operation.

## Impact

- All queries that use `latest_weight > 0` (the default path) now correctly favour recent publications.
- The hard filter (`latest` flag / separate FAISS index) was unaffected.

## Files changed

- `statschat/generative/cloud_llm.py` — one-line operator change + comment update
