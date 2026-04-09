# Investigation: Evidence Span Evaluator Limitations on the Audited Benchmark

## Goal

Determine whether the standalone evidence-span evaluator in
`tests/accuracy/evaluate_ragas.py` is suitable as a tracked retrieval metric for
the audited KNBS benchmark, or whether it should remain a diagnostic-only tool.

Reference run:

- `tests/accuracy/runs/cloud/2026-04-09_162741/accuracy_results.csv`
- `tests/accuracy/runs/cloud/2026-04-09_162741/span_recall_results.csv`

## Metric Definition

The evaluator compares the audited `source_text` against retrieved `context_texts`
using:

1. exact normalized substring containment
2. `RapidFuzz partial_ratio >= 85`
3. a combined hit flag (`exact OR fuzzy`)

Rows are only evaluated when:

- `should_answer = TRUE`
- `predicted_answer` is non-empty
- `source_text` is non-empty
- at least one retrieved chunk is present

## Headline Results

On the `2026-04-09_162741` cloud run:

- Eligible rows: `32`
- Dropped rows: `5`
- Exact span hit rate: `15/32 = 0.46875`
- Fuzzy span hit rate: `20/32 = 0.625`
- Combined span hit rate: `20/32 = 0.625`
- Average best partial ratio: `87.47`

The dropped rows were all answer-missing rows:

- `QQ002`
- `QQ004`
- `QQ007`
- `QQ014`
- `QQ025`

For comparison, on the same 32 eligible rows:

- `Any Reference Page Hit = 22/32 = 0.6875`

So span hit is stricter than page hit, but not fully aligned with it.

## Key Finding

The span metric is **not predictive of answer correctness** on this benchmark.

Cross-tab on the 32 eligible rows:

| Span Hit | Incorrect | Correct | Total |
|---|---:|---:|---:|
| False | 1 | 11 | 12 |
| True | 1 | 19 | 20 |
| Total | 2 | 30 | 32 |

Interpretation:

- `11/12` span-miss rows were still answered correctly
- `19/20` span-hit rows were answered correctly

That means "did the exact audited quote appear in retrieved context?" is not a
strong discriminator for answer correctness in this dataset.

## Manual Inspection

Three representative rows were checked directly against retrieved
`context_texts` and audited `source_text`.

### `QQ016`

Audited source:

> The sugar production declined by 40.8 per cent to 473.9 thousand tonnes in 2023.

Retrieved context contained the same evidence region, but in table and
near-paraphrase form:

- `2023* ... Sugar Production ... 472,773`
- `sugar production declined ... to 472.8 thousand tonnes in 2023`

The answer was grounded, but not via the exact audited sentence.

### `QQ021`

Audited source:

> most real estate firms (95.1%) are private businesses

Retrieved context contained:

- `95.1 per cent were private businesses`
- `Majority (95.1%) ... were private businesses`

Again, the answer was grounded, but the quote wording did not match exactly.

### `QQ035`

Audited source:

> By county, demand satisfied by modern methods ranges from 4% in Mandera County to 89% in Embu County.

Retrieved context contained the same evidence, but broken across PDF layout
lines and neighboring text. The answer remained correct even though the exact
audited span was not matched.

## What This Means

The dominant issue is **granularity mismatch**, not obvious hallucination.

The audited `source_text` is often:

- one hand-selected sentence, or
- a short quote copied from a table or narrative paragraph

The retrieved contexts are often:

- page-sized chunks
- table blocks
- layout-broken narrative text
- nearby supporting text rather than the exact quoted sentence

So a span miss often means:

- the auditor quote is narrower than the retrieved support, or
- PDF extraction/layout changed the exact string shape

It does **not** usually mean the model answered without support.

## Useful Diagnostic Cases

Even though the metric is not suitable as a KPI, it still exposed useful cases:

### `QQ016`

- span miss
- correct answer
- benchmark gold and audited quote agree with each other
- but the same KNBS report also contains later detailed sugar figures of
  `472,772` / `472,773` and `472.8 thousand tonnes`

This is not a simple retrieval failure. It is a benchmark/source consistency
problem:

- the audited row points to a sentence that says `473.9 thousand tonnes`
- later detailed pages in the same indexed source report say `472.8 thousand tonnes`
  and table values `472,772` / `472,773`
- the model answered the later detailed figure from retrieved context

So `QQ016` is best treated as a source inconsistency or audit-anchor issue, not
evidence that the model answered ungrounded.

### `QQ011`

- span miss
- page miss
- wrong answer

This remains a clean retrieval-caused failure.

### `QQ028`

- span hit
- page miss
- wrong answer

This is the best false-positive case: text similar to the audited span was
present, but from the wrong survey/year.

### `QQ030`

- span hit
- page miss
- correct answer

This suggests the gold page annotation is narrower than where the textual
support actually appears.

## Recommendation

Keep `tests/accuracy/evaluate_ragas.py` as a **diagnostic case-work tool**, not
as a tracked benchmark KPI.

Use it for:

- inspecting suspicious rows
- spotting wrong-year near-duplicate evidence
- checking whether gold evidence-like text was present in retrieved chunks

Do **not** promote `span_hit_rate` into the main benchmark scoreboard alongside:

- `overall_accuracy`
- `pipeline_doc_hit_at_k`
- `pipeline_mrr`
- `any_reference_page_hit`

Those remain the more reliable tracked metrics for this audited benchmark.
