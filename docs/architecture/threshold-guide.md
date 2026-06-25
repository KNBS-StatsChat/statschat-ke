# Answer & Document Thresholds

This guide explains how StatsChat uses two score thresholds to decide whether to
return an answer, return supporting documents, or refuse entirely.

For context on where scores come from, see the [Retrieval Pipeline](pipeline-retrieval.md).
For where these thresholds sit in the end-to-end flow, see the
[Input/Output Overview](pipeline-input-output.md).

## What are the scores?

FAISS returns an **L2 (Euclidean) distance** between the query embedding and each
document chunk embedding — not a percentage or probability. The scores are
produced by `similarity_search_with_score` in `statschat/generative/cloud_llm.py`.

Key properties:

| Value | Meaning |
|---|---|
| **0.0** | Query and document are identical |
| **~0.3 – 0.8** | Strong semantic match (typical good retrieval) |
| **~0.9 – 1.4** | Weak or partial match |
| **2.0** | Maximum possible distance (the `similarity_threshold` ceiling) |

Because `sentence-transformers/all-mpnet-base-v2` produces unit-normalised
embeddings, the theoretical maximum L2 distance is **2.0** (fully orthogonal
vectors). Scores are therefore **not** bounded between 0 and 1 — they can reach
up to 2.0. The config parameter `similarity_threshold = 2.0` is effectively
"include everything".

## The two thresholds

Both are configured in [`statschat/config/main.toml`](../../statschat/config/main.toml)
under `[search]`, and applied in `make_query` inside
`statschat/generative/cloud_llm.py`.

| Parameter | Role |
|---|---|
| `answer_threshold` | If the best document score **exceeds** this, suppress the LLM answer and return a "no suitable answer" message instead. |
| `document_threshold` | If the best document score **exceeds** this, also suppress the reference documents. |

## Intended three-zone behaviour

The design assumes `answer_threshold` **<** `document_threshold`:

```
Score (L2 distance)    →    increasing distance / worse match
──────────────────────────────────────────────────────────────
      0          answer_threshold     document_threshold    2.0
      |──── Zone A ──────|───── Zone B ──────|──── Zone C ───|

Zone A  (score ≤ answer_threshold)
        LLM answer returned  ✓   Reference docs returned ✓

Zone B  (answer_threshold < score ≤ document_threshold)
        LLM answer suppressed ✗   Reference docs returned ✓
        → "No suitable answer found. However relevant information
           may be found in a PDF."

Zone C  (score > document_threshold)
        LLM answer suppressed ✗   Reference docs suppressed ✗
        → "No suitable PDFs found for this question."
```

Zone B is the key feature: the system declines to synthesise an answer (the
context wasn't good enough) but still surfaces potentially relevant extracts so
the user can judge for themselves.

## Current configuration and the inverted-threshold problem

As of the current `main.toml`:

```toml
answer_threshold  = 1.1
document_threshold = 0.9
```

`answer_threshold` **>** `document_threshold`, which **inverts** the intended
logic:

- Documents are suppressed at scores > 0.9.
- Answers are only suppressed at scores > 1.1 — meaning an LLM answer can be
  returned *after* the supporting documents have already been hidden.
- Zone B (the "useful extracts, no answer" band) effectively vanishes.

For most genuine queries, relevant documents score well below 0.9, so the answer
threshold of 1.1 is rarely triggered. In practice the system almost always
answers, which was your colleague's intent. But the structural guarantee of Zone B
is broken.

To restore the original three-zone behaviour, set `answer_threshold` strictly
below `document_threshold`, for example:

```toml
answer_threshold  = 0.5
document_threshold = 0.9
```

These were the original default values in the `Inquirer.__init__` signature.

## Relationship to `similarity_threshold`

`similarity_threshold` is applied earlier, during FAISS retrieval:

```
similarity_search_with_score(...)
    → discard any chunk with score > similarity_threshold
    → pass survivors to make_query
```

`answer_threshold` and `document_threshold` are applied later, on the *best*
surviving score. So the pipeline is:

1. **`similarity_threshold`** — coarse filter; keep only plausible chunks.
2. **`answer_threshold`** — decide whether to show an LLM-synthesised answer.
3. **`document_threshold`** — decide whether to show reference documents at all.

## See also

- [Retrieval Pipeline](pipeline-retrieval.md) — similarity search, time decay, and
  how scores are computed.
- [Generation Pipeline](pipeline-generation.md) — where `make_query` applies the
  thresholds and formats the final response.
- [Input/Output Overview](pipeline-input-output.md) — full API response contract
  and threshold behaviour specification.
- [`docs/reference/config_guide.md`](../reference/config_guide.md) — parameter
  reference table.
