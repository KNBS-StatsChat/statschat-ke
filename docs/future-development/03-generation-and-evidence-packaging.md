# Generation and evidence-packaging recommendations

> **When to use this file**: Use this after retrieval is returning cleaner evidence objects. The near-term generation goal is better evidence packaging, not switching models for its own sake.

## Current baseline

The current repo already includes:

- a cloud generation path as the practical primary option;
- a local generation path mainly for alternative/offline use;
- grounded prompts that instruct the model to use retrieved context;
- Pydantic response parsing through `LlmResponse`;
- answer/highlighting fields;
- post-processing that links highlighted phrases back to retrieved documents;
- guardrails for some out-of-scope questions.

Future work should not focus mainly on choosing a more powerful LLM. The bigger opportunity is to improve what the LLM receives and how answer sufficiency is represented.

## Core recommendation

Pass the LLM a compact, citation-ready evidence pack rather than loosely selected page text.

The generation stage should receive evidence that already contains the source structure needed for a statistical answer:

- publication title;
- report family;
- publication date;
- reference period;
- page number;
- table/section title;
- unit;
- geography;
- extracted evidence text or Markdown table;
- retrieval/reranking metadata for traceability.

## Evidence-pack format

A suggested evidence object for generation:

```json
{
  "context_id": "C1",
  "publication_title": "...",
  "report_family": "...",
  "publication_date": "...",
  "reference_period": "...",
  "page_number": 12,
  "page_url": "...#page=12",
  "evidence_type": "table",
  "table_title": "...",
  "unit": "percent",
  "geography": "Kenya",
  "markdown": "...",
  "notes": ["..."]
}
```

The prompt can then refer to context IDs and require the answer to cite them.

## Statistical answer rules

The prompt should continue to require grounded answers, but it should be explicit about statistical details.

For factual statistical answers, ask the model to include:

- the value;
- the unit;
- the geography;
- the reference period;
- the source publication;
- the page/table when available;
- any relevant caveat or footnote.

For “latest” questions, require the model to state what “latest” means in the answer, for example latest available reference period or latest publication in the indexed corpus.

## Refusal and weak-evidence behaviour

Standardise the difference between:

- answer found;
- insufficient evidence;
- ambiguous question;
- out-of-scope question;
- retrieval failure;
- parsing/generation error.

Suggested statuses:

```text
answered
insufficient_evidence
ambiguous
out_of_scope
retrieval_failure
generation_error
```

This would be more informative than treating every non-answer as the same kind of failure.

## Structured output extension

The current `LlmResponse` structure is useful. Future versions could add fields such as:

- `answer_status`;
- `assumptions`;
- `warnings`;
- `value`;
- `unit`;
- `geography`;
- `reference_period`;
- `supporting_context_ids`;
- `citation_confidence`;
- `reason_for_refusal`.

These fields can improve the UI and make evaluation easier. They should be introduced carefully, with tests for parser robustness.

## Token-use guidance

Do not minimise context tokens at the expense of evidence quality. Instead:

1. retrieve broadly enough to avoid missing the right source;
2. rerank/filter aggressively;
3. pass a small number of high-quality evidence packs;
4. include the surrounding metadata needed for interpretation;
5. avoid dumping many noisy page chunks into the prompt.

For tables, pass only the relevant table or table slice where possible, but include title, units, row/column labels and footnotes.

## Prompt and model governance

For any release-impacting change, log and retain:

- model name;
- provider;
- prompt version;
- parser/schema version;
- index version;
- retrieval configuration;
- generation parameters;
- benchmark run ID.

Model changes should be evaluated in staging before adoption. Provider/model availability can change over time, so the current best model should not be assumed to remain best indefinitely.

## Practical next steps

1. Review the current prompt and `LlmResponse` fields against common benchmark failures.
2. Add an `answer_status` field or equivalent status mapping.
3. Create an evidence-pack formatting function separate from the retrieval logic.
4. Add tests showing that source metadata survives from retrieval into generation output.
5. Benchmark the same retrieval contexts with the current model and any candidate model before switching.

## Links to existing repo material

- `statschat/generative/cloud_llm.py`
- `statschat/generative/prompts_cloud.py`
- `statschat/generative/response_model.py`
- `statschat/generative/utils.py`
- `statschat/generative/query_policy.py`
- `docs/architecture/pipeline-generation.md`
- `docs/architecture/token-usage-guide.md`
- `docs/decisions/002-openrouter-default-model-selection.md`
