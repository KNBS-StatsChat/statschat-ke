# Guide: How "latest" works in StatsChat

StatsChat has two independent mechanisms for prioritising recent publications. They operate at different stages of the retrieval pipeline.

> **Current status (March 2026):**
>
> - **Hard filter** — disabled.

With `latest_only = false` in config, both FAISS indexes contain all documents, so the query-time index switch has no effect. We don't anticipate needing this; the soft bias is a better approach for our corpus.

> - **Soft bias** — active and recently fixed.

Two bugs previously rendered it non-functional: a wrong operator (`/` instead of `*`) and a date format mismatch that caused silent parse failures. See [2026-03-13-time-decay-reweighting-bug.md](../investigations/2026-03-13-time-decay-reweighting-bug.md) and [2026-03-21-time-decay-date-format-mismatch.md](../investigations/2026-03-21-time-decay-date-format-mismatch.md) for details.

---

## 1. Hard filter — the `latest` flag

A **binary gate** that restricts which documents are searched at all.

### How it works

Every JSON document has a `"latest": true | false` field.

- **New documents** are ingested with `"latest": true` ([pdf_to_json.py](../architecture/pipeline-pdf-ingestion.md)).
- **When a newer edition arrives** (`mode = "UPDATE"`), `latest_updates.py` fuzzy-matches filenames to detect superseded publications and sets their flag to `false`.
- **At embedding time**, a separate FAISS index (`db_langchain_latest`) is built containing only flagged documents.
- **At query time**, `similarity_search()` chooses which index to query:

```
latest_filter = True  →  search db_langchain_latest  (latest docs only)
latest_filter = False →  search db_langchain          (all docs)
```

### Config

| Key | File | Effect |
|-----|------|--------|
| `latest_only` | `statschat/config/main.toml` `[preprocess]` | Controls whether only `latest=true` docs enter the latest FAISS index at build time |

### Key files

| File | Role |
|------|------|
| `statschat/pdf_processing/pdf_to_json.py` | Sets `"latest": true` on new docs |
| `statschat/embedding/latest_updates.py` | Manages flag lifecycle (`find_latest`, `compare_latest`, `unflag_former_latest`, `update_split_documents`) |
| `statschat/embedding/preprocess.py` | Filters on the flag when building the FAISS index |
| `statschat/generative/cloud_llm.py` | Loads both FAISS indexes; `similarity_search()` picks which to query |

---

## 2. Soft bias — recency reweighting (`latest_weight`)

A **post-retrieval reranker** that adjusts similarity scores to favour newer documents, without excluding older ones.

### How it works

After FAISS returns results (as L2 distances — lower = more relevant), each score is multiplied by a time-decay factor:

```python
doc["score"] = doc["score"] * time_decay(doc["date"], latest=latest_weight)
```

`time_decay()` returns:

```
decay = 1 + (days_old / 365) * latest_weight
```

| Document age | `latest_weight=1` | `latest_weight=2` |
|---|---|---|
| Brand new | 1.0 (no change) | 1.0 (no change) |
| 1 year old | 2.0 (score doubled) | 3.0 (score tripled) |
| 5 years old | 6.0 (score × 6) | 11.0 (score × 11) |

Higher decay → larger L2 distance → ranks lower. Recent documents keep their original scores; older documents are penalised.

### How `latest_weight` is determined

The numeric value comes from `get_latest_flag()` in `latest_flag_helpers.py`, driven by the `latest_max` config:

| Condition | `latest_weight` value |
|---|---|
| Query contains "recent" or "latest" | `latest_max` (default: **2**) |
| API request explicitly sets `latest_weight` to on/true | `latest_max` (default: **2**) |
| Default (no signal) | `latest_max / 2` (default: **1**) |
| Direct script call (no API) | `1` (hardcoded default in `ask()`) |

### Config

| Key | File | Effect |
|-----|------|--------|
| `latest_max` | `statschat/config/main.toml` `[app]` | Upper bound for the recency weight. `0` = no recency bias, `1` = moderate, `2` = aggressive |

### Key files

| File | Role |
|------|------|
| `statschat/generative/utils.py` | `time_decay()` — computes the decay multiplier |
| `statschat/generative/cloud_llm.py` | `ask()` — applies the reweighting after retrieval |
| `statschat/embedding/latest_flag_helpers.py` | `get_latest_flag()` — resolves query/request into a numeric weight |

---

## How the two mechanisms interact

They are **independent and composable**:

```
User query
  │
  ├─ Hard filter (latest_filter) ──► Selects FAISS index (latest-only vs all)
  │                                          │
  │                                    FAISS search
  │                                          │
  └─ Soft bias (latest_weight) ────► Reweights returned scores by age
                                             │
                                       Final ranked results
```

A typical API query with `content_type="latest"` uses **both**: it searches the latest-only index *and* applies recency reweighting to the results. Setting `content_type="all"` uses the full index but still applies the soft bias.

Setting `latest_weight=0` disables the soft bias entirely (useful for queries asking about a specific historical date).
