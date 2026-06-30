# Token Usage Guide

> **Last analyzed:** December 2025 (13,738 documents in FAISS index)

This guide explains how tokens are calculated for LLM queries in StatsChat, what configuration parameters affect token usage, and how to tune them for cost vs quality trade-offs.

For pricing and deployment cost estimates, see [`cost.md`](../decisions/cost.md).

---

## Overview

When a user asks a question, StatsChat doesn't send entire PDFs or even full pages to the LLM. Instead, it sends **chunks** of text retrieved from a vector database. Understanding this pipeline helps explain where tokens come from.

```
PDF Pages (73 publications, ~8,600 pages)
         ↓
    Text Extraction (PyMuPDF)
         ↓
JSON Files (one per page, stored in data/json_split/)
         ↓
    Text Splitting (RecursiveCharacterTextSplitter)
    - chunk_size: 2000 characters
    - chunk_overlap: 200 characters
         ↓
FAISS Vector Store (13,738 chunks)
         ↓
    Similarity Search (returns k_docs chunks)
         ↓
LLM Context (1-5 chunks based on config)
         ↓
    Answer Generation
```

**Key insight:** Each "document" sent to the LLM is a **chunk** (≤2000 characters), not a full PDF or page.

---

## Current Token Distribution

The chunks stored in FAISS vary significantly in size:

| Metric | Tokens |
|--------|--------|
| **Minimum** | 2 |
| **Maximum** | 6,002 |
| **Mean** | 647 |
| **Median** | 564 |
| **Std Dev** | 464 |

### Distribution by Token Range

| Token Range | Chunks | % of Total |
|-------------|--------|------------|
| 0-100 | 1,155 | 8.4% |
| 100-200 | 1,140 | 8.3% |
| 200-300 | 1,160 | 8.4% |
| 300-400 | 1,194 | 8.7% |
| 400-500 | 1,469 | 10.7% |
| **500-750** | **2,906** | **21.2%** |
| 750-1000 | 1,789 | 13.0% |
| 1000-1500 | 2,215 | 16.1% |
| 1500-2000 | 677 | 4.9% |
| 2000+ | 33 | 0.2% |

Most chunks (55%) contain 300-1000 tokens. The median of 564 tokens is a good estimate for planning.

---

## Configuration Parameters

These settings in `statschat/config/main.toml` control how many chunks are retrieved and sent to the LLM:

### `[db]` Section

| Parameter | Default | Description | Token Impact |
|-----------|---------|-------------|--------------|
| `split_length` | 2000 | Max characters per chunk | Higher = fewer, larger chunks |
| `split_overlap` | 200 | Character overlap between chunks | Higher = more redundancy |

### `[search]` Section

| Parameter | Default | Description | Token Impact |
|-----------|---------|-------------|--------------|
| `k_docs` | 2 | Max chunks retrieved from FAISS | **Primary cost driver** |
| `k_contexts` | 5 | Max chunks sent to LLM | Caps context if k_docs is higher |
| `similarity_threshold` | 2.0 | Max similarity score to include | Lower = fewer, more relevant chunks |

### Current Configuration

```toml
[search]
k_docs = 2
k_contexts = 5
similarity_threshold = 2.0
```

With `k_docs=2`, at most **2 chunks** are retrieved per query, regardless of `k_contexts`.

---

## Estimating Tokens Per Query

### Formula

```
Input tokens ≈ system_prompt + question + (num_chunks × avg_chunk_tokens)
            ≈ 40 + 15 + (num_chunks × 600)

Output tokens ≈ 100-300 (structured JSON response)
```

### Scenarios (with current config: k_docs=2)

| Scenario | Chunks | Input Tokens | Output Tokens | Total |
|----------|--------|--------------|---------------|-------|
| Small chunks (2 × 200) | 2 | ~455 | ~200 | ~655 |
| Median chunks (2 × 564) | 2 | ~1,183 | ~200 | ~1,383 |
| Large chunks (2 × 1000) | 2 | ~2,055 | ~200 | ~2,255 |

**Typical query:** ~1,000-1,400 tokens total.

### If k_docs is Increased

| k_docs | Avg Input Tokens | Avg Total |
|--------|------------------|-----------|
| 1 | ~655 | ~855 |
| 2 | ~1,255 | ~1,455 |
| 3 | ~1,855 | ~2,055 |
| 5 | ~3,055 | ~3,255 |

---

## Tuning for Cost vs Quality

### To Reduce Cost

| Change | Trade-off |
|--------|-----------|
| Reduce `k_docs` to 1 | Fewer chunks = less context, may miss relevant info |
| Lower `similarity_threshold` | Only very relevant chunks, may return no results for vague queries |
| Reduce `split_length` | Smaller chunks, but more of them in FAISS |

### To Improve Answer Quality

| Change | Trade-off |
|--------|-----------|
| Increase `k_docs` to 3-5 | More context, higher cost, diminishing returns |
| Increase `similarity_threshold` | Include more marginally-relevant chunks |
| Increase `split_length` | Larger chunks preserve more context, but may include irrelevant text |

### Recommended Starting Point

The current defaults (`k_docs=2`, `similarity_threshold=2.0`) provide a good balance:
- ~1,000-1,400 tokens per query
- Sufficient context for most factual questions
- Low cost (~$0.003-0.01 per query on OpenRouter)

Consider increasing `k_docs` to 3 if users report incomplete answers, or reducing to 1 for high-volume, simple queries.

---

## Re-running the Analysis

Token statistics will change as more documents are added. Use this script to regenerate the analysis:

```python
import os
import statistics
os.chdir('/path/to/statschat-ke')  # Update this path

from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer

# Load components
print("Loading embeddings and FAISS...")
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')
db = FAISS.load_local('data/db_langchain', embeddings, allow_dangerous_deserialization=True)
tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.3')

# Analyze all documents
all_docs = list(db.docstore._dict.values())
token_counts = [len(tokenizer.encode(doc.page_content)) for doc in all_docs]

print(f"\n=== Token Distribution (as of {__import__('datetime').date.today()}) ===")
print(f"Total documents: {len(all_docs):,}")
print(f"Min:    {min(token_counts)}")
print(f"Max:    {max(token_counts)}")
print(f"Mean:   {statistics.mean(token_counts):.0f}")
print(f"Median: {statistics.median(token_counts):.0f}")
print(f"Std Dev: {statistics.stdev(token_counts):.0f}")

# Distribution buckets
buckets = [0, 100, 200, 300, 400, 500, 750, 1000, 1500, 2000]
print(f"\nDistribution:")
for i in range(len(buckets)-1):
    count = sum(1 for t in token_counts if buckets[i] <= t < buckets[i+1])
    pct = count / len(token_counts) * 100
    print(f"  {buckets[i]:4d}-{buckets[i+1]:4d}: {count:5d} ({pct:5.1f}%)")
count = sum(1 for t in token_counts if t >= buckets[-1])
print(f"  {buckets[-1]:4d}+   : {count:5d} ({count/len(token_counts)*100:5.1f}%)")
```

---

## See Also

- [`docs/decisions/cost.md`](../decisions/cost.md) - Deployment options and pricing estimates
- [`docs/reference/config_guide.md`](../reference/config_guide.md) - Full configuration reference
