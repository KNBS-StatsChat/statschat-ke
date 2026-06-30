# Investigation: PDF Extraction vs Page Recall on Remaining Cloud Failures

## Goal

Determine whether the remaining cloud accuracy failures are caused mainly by:

1. poor PDF text extraction,
2. chunk construction / chunk ordering within a page, or
3. page retrieval / page reranking inside the correct document family.

This note focuses on the 11 rows still incorrect in the stable cloud baseline run:

- `QQ002`
- `QQ004`
- `QQ006`
- `QQ007`
- `QQ008`
- `QQ010`
- `QQ011`
- `QQ014`
- `QQ025`
- `QQ028`
- `QQ036`

Reference baseline run:

- `tests/accuracy/runs/cloud/2026-04-08_131854/accuracy_results.csv`

## Method

For each failing row:

1. read the gold source doc and page from the audited sheet
2. check whether the stored JSON page text contains the gold source text
3. compare the gold page extracted with:
   - `fitz` / PyMuPDF
   - `pdfplumber`
   - `pypdf`
4. split the page with the current chunking settings:
   - `split_length = 1000`
   - `split_overlap = 150`
5. inspect the raw FAISS ranks for:
   - first hit from the gold document
   - first hit for the exact gold page

## Summary

There is no single root cause.

- Some rows are mainly **page retrieval / page reranking** failures.
- Some rows are **mixed extraction + page-recall** failures.
- The evidence does **not** support a global switch away from PyMuPDF.
- The evidence also does **not** support a global chunk-size change as the next fix.

## Findings Table

| ID | Gold doc/page | Stored page contains gold text? | `fitz` / `pdfplumber` / `pypdf` on gold page | Raw FAISS first gold doc rank | Raw FAISS gold page rank | Primary diagnosis |
|---|---|---:|---|---:|---:|---|
| `QQ002` | `Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf p.2` | Yes, page `2`, chunk `1` | All three extractors surface the answer cleanly in chunk `1` | `33` | `38` | Retrieval / page-ranking |
| `QQ004` | `Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2025.pdf p.1` | Yes, page `1`, chunk `2` | All three extractors surface the answer cleanly | `129` | Not in top `300` | Retrieval / page-ranking |
| `QQ006` | `Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.4` | Yes, page `4`, chunk `1` | All three extractors surface the answer cleanly in chunk `1` | `16` | `151` | Retrieval / page-ranking |
| `QQ007` | `2023-24-Kenya-Housing-Survey-Basic-Report1.pdf p.81` | Yes, page `81`, chunk `2` | All three extractors surface the answer in chunk `2`; `pdfplumber` is cleaner at page start | `4` | Not in top `300` | Retrieval / page-ranking |
| `QQ008` | `2024-FinAccess-Household-Survey-Report.pdf p.6` | Yes, page `6`, chunk `3` | `fitz` and `pypdf` preserve the answer; `pdfplumber` is worse here | `2` | `242` | Mostly retrieval / page-ranking |
| `QQ010` | `2023-24-Kenya-Housing-Survey-Basic-Report1.pdf p.47` | Yes, page `47`, chunk `4` | `fitz`/`pypdf`: chunks `4-5`; `pdfplumber`: chunk `2` | `2` | Not in top `300` | Both extraction and retrieval |
| `QQ011` | `2025-Economic-Survey.pdf p.282` | Yes, page `282`, chunk `1` | All three extractors surface the answer in chunk `1` | `1` | `141` | Retrieval / page-ranking |
| `QQ014` | `National-Agriculture-Production-Report-2024.pdf p.14` | Yes, page `14`, chunk `2` | `fitz` and `pypdf` surface the answer; `pdfplumber` is worse | `3` | `49` | Retrieval / page-ranking |
| `QQ025` | `2023-Economic-Survey.pdf p.93` | Yes, page `93`, chunk `2` | `pdfplumber` slightly cleaner; all extractors preserve the evidence | `223` | Not in top `300` | Retrieval / page-ranking |
| `QQ028` | `Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.14` | No exact stored-string hit | `pdfplumber` surfaces the birth-certificate statement clearly; `fitz` and `pypdf` foreground unrelated school-attendance text | Not in top `300` | Not in top `300` | Both extraction and retrieval |
| `QQ036` | `2020-Economic-Survey.pdf p.413` | Yes, page `413`, chunk `1` | All three extractors surface the answer cleanly in chunk `1` | `246` | Not in top `300` | Retrieval / page-ranking |

## What This Means

### 1. PDF extraction is part of the problem, but only for a subset

The clearest extraction-sensitive rows are:

- `QQ010`
- `QQ028`

For these rows, `pdfplumber` surfaces the target statement earlier and more cleanly than `fitz`.

By contrast, `QQ008` shows the opposite pattern:

- `fitz` is better
- `pdfplumber` is worse

So the evidence does **not** support replacing PyMuPDF globally.

### 2. The dominant bottleneck is still page recall inside the right report family

Rows such as:

- `QQ004`
- `QQ006`
- `QQ011`
- `QQ014`
- `QQ025`
- `QQ036`

all have usable extraction on the gold page, but the exact gold page ranks very low or never appears in the top `300` raw FAISS hits.

That is a page retrieval problem, not a language-model problem.

### 3. Chunk size is not the best next global lever

On several gold pages, the answer is not in chunk `1` with the current settings. However, reducing chunk size did not reliably help:

- `QQ010` moved from chunks `4-5` to even later chunks as chunk size decreased
- `QQ008` and `QQ014` also did not show a stable “smaller chunks = earlier answer” pattern

This points more to **page text order** than to chunk size alone.

## Recommendations

### Recommendation 1: Do not replace PyMuPDF globally

Keep `fitz` / PyMuPDF as the production default.

Reason:

- it is better on some target rows (`QQ008`)
- worse on others (`QQ010`, `QQ028`)

### Recommendation 2: Add a targeted extraction-quality path for a small set of families/pages

Investigate a selective fallback or comparison step for:

- `2023-24-Kenya-Housing-Survey-Basic-Report1.pdf`
- `Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf`

These are the strongest candidates for family-level or page-level `pdfplumber` preference.

### Recommendation 3: Prioritize page-local retrieval improvements next

The next retrieval-side change should target page recall directly, for example:

- adjacent-page expansion around high-ranked pages in the correct document
- page-level lexical reranking inside the already matched document family
- document-family-local second-pass retrieval

This is especially important for:

- `QQ004`
- `QQ006`
- `QQ011`
- `QQ014`
- `QQ025`
- `QQ036`

### Recommendation 4: Do not change global chunk size yet

There is not enough evidence that a global `split_length` change will fix the current failures.

## Practical Next Step

The highest-value next experiment is:

1. keep the current committed family-aware retrieval baseline
2. run a targeted extraction comparison / fallback experiment for:
   - Housing Survey pages
   - KDHS 2022 pages
3. separately prototype page-local retrieval improvement for rows where extraction is already clean

That keeps the problem decomposed:

- extraction-sensitive rows
- page-recall-sensitive rows
