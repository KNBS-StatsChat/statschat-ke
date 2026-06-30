# Evaluation and monitoring recommendations

> **Use this alongside the Docling trial**: Evaluation is how to decide whether the new PDF-processing route is better than the current parser. Run extraction, retrieval and answer checks before accepting any pipeline change.

## Current baseline

Evaluation is one of the strongest parts of the current repo. The project already includes:

- an audited benchmark workbook;
- evaluation scripts;
- answerable and unanswerable accuracy metrics;
- document and page retrieval metrics;
- run outputs and history;
- guidance that release-impacting changes should be benchmarked.

Future work should build on this, not replace it.

## Core recommendation

Use evaluation as the control mechanism for every future improvement.

Any change to PDF processing, chunking, embeddings, retrieval, reranking, prompts, model choice, corpus contents or response schema can change answers. These changes should be tested against a known baseline before acceptance.

## Evaluation layers

Separate evaluation by pipeline stage so failures are diagnosable.

| Layer | Example question |
|---|---|
| Ingestion | Was the source PDF downloaded and converted correctly? |
| Extraction | Is the required table/value present in the JSON/Markdown? |
| Chunking | Did the value stay attached to its heading, unit and period? |
| Retrieval | Did the correct document/page/table appear in the candidate set? |
| Reranking | Did the best evidence rise near the top? |
| Generation | Did the model answer correctly from the selected evidence? |
| Citation | Did the answer point to the correct source? |
| Refusal | Did the system refuse unsupported questions? |

This avoids blaming the LLM for failures caused by missing extraction or weak retrieval.

## Recommended metrics

Continue tracking existing metrics, including:

- answerable accuracy;
- unanswerable accuracy;
- overall accuracy;
- answer missing rate;
- false answer rate;
- pipeline document hit@k;
- first/any reference document match;
- first/any reference page hit.

Add or strengthen:

- table hit@k;
- evidence-object hit@k;
- extraction coverage for benchmark source pages;
- OCR/scanned-page failure counts;
- missing metadata counts;
- answer status distribution;
- retrieval latency;
- generation latency;
- token usage per query;
- cost per benchmark run.

## Failure labels

Each failed benchmark row should receive one or more labels:

- `missing_pdf`
- `download_failure`
- `extraction_failure`
- `ocr_failure`
- `table_structure_lost`
- `bad_metadata`
- `chunk_split_evidence`
- `wrong_report_family`
- `wrong_edition_or_period`
- `right_doc_wrong_page`
- `right_context_wrong_answer`
- `citation_failure`
- `should_refuse`
- `false_refusal`
- `benchmark_issue`
- `ambiguous_question`

This will show whether the next improvement should happen in ingestion, retrieval, generation or evaluation data.

## PDF-processing evaluation

For the PDF-processing bake-off, use a fixed sample set of KNBS PDFs:

- clean born-digital reports;
- table-heavy reports;
- monthly bulletins;
- annual reports;
- county-level reports;
- scanned/problematic PDFs;
- reports linked to known benchmark failures.

For each parser, measure:

- page text coverage;
- table preservation;
- reading order;
- heading preservation;
- OCR behaviour;
- JSON/schema completeness;
- Markdown usefulness;
- downstream retrieval and answer performance.

## Retrieval evaluation

For retrieval experiments, compare against the current baseline:

- current dense + routing + reranking stack;
- dense-only ablation;
- lexical/BM25-only;
- hybrid dense+lexical;
- metadata-filtered retrieval;
- table-aware retrieval;
- reranker variants.

Use the same benchmark and same index version when possible. If a new extraction/indexing pipeline is tested, label the run clearly so results are not confused with retrieval-only changes.

## Live monitoring

During internal pilot use, collect:

- user question;
- answer status;
- retrieved references;
- model and index version;
- latency;
- user feedback;
- reviewer classification for sampled answers.

Repeated real-user failures should become new benchmark rows after review.

## Release gates

Before accepting a release-impacting change, check:

1. Has the current baseline been recorded?
2. Has the audited benchmark been run?
3. Are retrieval metrics at least as good, or is any drop justified?
4. Is unanswerable accuracy preserved?
5. Are false answers investigated?
6. Are new failures labelled by stage?
7. Are run artifacts retained?
8. Are docs/config updated if the behaviour changed?

## Practical next steps

1. Create a short evaluation checklist for pull requests that change retrieval, generation, indexing or PDF processing.
2. Add failure labels to benchmark review outputs.
3. Add ingestion-quality summaries to update runs.
4. Build a small “known hard PDFs” extraction test set.
5. Run baseline vs candidate parser/index comparisons before adopting a new PDF tool.
6. Expand the benchmark with questions from internal pilot sessions.

## Links to existing repo material

- `tests/accuracy/README.md`
- `tests/accuracy/evaluate_accuracy.py`
- `tests/accuracy/StatsChat_QA_Verified_Audited.xlsx`
- `docs/guides/replication_instructions.md`
- `docs/reports/2026-04-statschat-ke-testing-accuracy-report.md`
- `docs/reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md`
- `docs/CONTRIBUTING.md`
