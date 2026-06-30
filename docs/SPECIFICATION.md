# Project Specification: StatsChat-KE

## Purpose of This Document

This document provides a conceptual overview of the StatsChat-KE project: what it
is, what it is designed to do, what has been built, and how it should evolve. It
is intended as a starting point for anyone joining or taking over the project, and
as the reference for decisions about scope, direction, and acceptable quality.

For technical implementation detail, see the [architecture documentation](./architecture/README.md).
For operational instructions, see the [Operating Manual](./guides/OPERATING_MANUAL.md).

---

## 1. What Is StatsChat-KE?

StatsChat-KE is a retrieval-augmented generation (RAG) tool that helps users find
relevant evidence in official statistical publications. A user asks a
natural-language question — for example, "What was Kenya's inflation rate in
December 2023?" — and the system searches the KNBS publication corpus, retrieves
the most relevant pages and extracts, and uses a large language model to produce
a grounded answer with references back to the source material.

**The primary use case** is not to replace expert judgement, but to speed up the
existing process of searching through PDFs. Staff who currently spend time
manually scanning dozens of reports to find the right figure, table, or paragraph
can use StatsChat to locate the relevant document, page, and extract much faster
— and then inspect the source before relying on the answer.

### Guiding Principles

**Retrieval-first.** The answer is only as good as the documents retrieved.
Citations matter. Every answer should be traceable to a source page in the corpus.

**Grounded generation.** The LLM is instructed to answer using only the retrieved
context, not its general training knowledge. Questions that cannot be grounded in
the corpus should be refused rather than fabricated.

**Accuracy discipline.** Changes to the system — model, retrieval configuration,
corpus, or code — should be validated against the audited benchmark before being
accepted. See [Section 5](#5-automated-evaluation-the-feedback-loop).

---

## 2. Project History and Current Status

StatsChat began as an ONS prototype in 2023. It was adapted for the Kenya National
Bureau of Statistics in 2025. The early KNBS version was a working prototype but
lacked rigorous testing or a stable evaluation framework.

In the 2025–2026 development phase, the system was substantially improved:

- Automated unit and integration tests were added.
- An audited benchmark workbook was created and reviewed (74 questions with known
  correct answers drawn directly from KNBS publications).
- Retrieval was redesigned: report-family routing, temporal candidate widening,
  cross-encoder reranking, and page-aware context selection were added.
- The local and cloud API paths were aligned to share the same retrieval
  architecture.
- An out-of-scope guardrail policy was added so the system correctly refuses
  questions it cannot answer from the corpus.

On the audited 74-question benchmark, the best cloud configuration
(GPT-5.4-mini) achieved:

| Metric | Result |
|---|---|
| Answerable accuracy | 57 / 61 = **93.4%** |
| Unanswerable accuracy | 13 / 13 = **100%** |
| Overall accuracy | 70 / 74 = **94.6%** |
| Pipeline document hit@8 | 56 / 61 = **91.8%** |

The system is now in a strong position for controlled internal testing.

---

## 3. Intended Scope and Constraints

- **Data source**: strictly KNBS publications. The system is not designed to
  answer general knowledge questions or draw on sources outside the indexed
  corpus.
- **Language**: English. KNBS reports are primarily in English; the system has
  not been tested on Swahili or other languages.
- **Accuracy**: this is an experimental AI system. The benchmark shows high
  accuracy on the audited question set, but real user questions will vary, and
  hallucinations remain a known risk — particularly for questions where the answer
  is not clearly present in the corpus.
- **Deployment**: designed for macOS-local development and cloud API deployment.
  The local inference path is slower and resource-intensive (~16 GB RAM); the
  cloud path via OpenRouter is recommended for general use.
- **Corpus currency**: the indexed corpus is a snapshot. New KNBS publications
  are not automatically ingested; an operator must run the update pipeline to keep
  the corpus current.

---

## 4. Known Limitations

**PDF processing quality** is the largest remaining bottleneck. Some publications
convert well; others — especially scanned documents or PDFs with complex table
layouts — are not processed reliably. This directly affects retrieval and answer
quality, because the system can only answer questions about text it has
successfully extracted. Improving PDF processing would have a large downstream
impact on accuracy.

**Evaluation coverage** is still limited. The current 74-question benchmark covers
a range of topics and publication types, but it cannot represent the full range
of questions real users will ask. The benchmark should be expanded over time,
particularly with questions that arise from real usage.

**External API dependency.** The cloud path depends on OpenRouter and the
configured LLM provider. Provider instability (model availability, response
quality changes) has caused evaluation failures in the past. The active model
configuration should be reviewed periodically and monitored for provider changes.

---

## 5. Automated Evaluation: The Feedback Loop

The evaluation system is not a passive test suite. It is the mechanism by which
any change to the system is validated against a known quality baseline.

The workflow is:

1. A curated benchmark workbook (`StatsChat_QA_Verified_Audited.xlsx`) contains
   questions with known correct answers, sourced and reviewed from actual KNBS
   publications.
2. The evaluator runs those questions against the live API and scores responses.
3. Results are archived with a timestamp, and a cross-run ledger tracks accuracy
   across models, configurations, and time.
4. Any drop in accuracy signals a regression. Any claimed improvement must be
   confirmed by the evaluator before being accepted.

**The rule**: before changing the model, the retrieval configuration, the FAISS
index, or deploying a new version, run the evaluator and compare against the
current baseline.

See [tests/accuracy/README.md](../tests/accuracy/README.md) for the full
technical workflow, and the
[maintenance and accuracy monitoring plan](./reports/2026-06-knbs-maintenance-public-launch-and-accuracy-monitoring.md)
for the recommended ongoing monitoring model.

---

## 6. Recommended Next Steps

**Internal pilot.** The most important next step is a controlled internal
deployment within KNBS. This would allow staff to test the tool in realistic
workflows, give feedback, and identify where it helps most. The tool should be
positioned as a retrieval-first assistant at this stage: it helps users find
relevant publications and extracts faster, while users still inspect the cited
sources before relying on an answer.

**Corpus maintenance.** Establish a routine update cadence (e.g. monthly) to
ingest new KNBS publications. Each corpus update should be followed by a
benchmark run to confirm no accuracy regression.

**Benchmark expansion.** As real usage generates new questions and failures,
those cases should be converted into new benchmark rows. This grows evaluation
coverage over time and makes the benchmark more representative of real use.

**User feedback loop.** Capture real user questions and outcomes. Failures or
low-confidence answers should be reviewed and used to improve the benchmark, the
retrieval configuration, or the PDF processing pipeline.

---

## 7. Future Development Directions

Detailed, prioritised recommendations are in [`docs/future-development/`](./future-development/). Start with the [README](./future-development/README.md) for the recommended reading order.

The immediate first priority is:

> **Trial Docling as a structured PDF-to-JSON/Markdown converter on a representative set of KNBS PDFs, compare it against the current parser, and use the result to decide the next ingestion changes.**

This is the highest-leverage improvement because the current retrieval pipeline is already relatively strong. The clearest remaining bottleneck is earlier: if PDF extraction loses table structure, page references, units or reference periods, retrieval cannot reliably recover them. Better structured ingestion should therefore come before major retrieval rewrites.

After the ingestion trial, the recommended priority order is:

1. **Structured PDF ingestion** — move from page-level plain text toward structured evidence objects with table-aware chunks, stable IDs, and preserved metadata (units, reference periods, page numbers, headings).
2. **Expanded evaluation data** — grow the benchmark with questions drawn from real usage; add ingestion and retrieval diagnostic metrics so failures can be assigned to the right pipeline stage.
3. **Targeted retrieval improvements** — using the better evidence objects from structured ingestion, test hybrid search, stronger metadata filtering, and table-aware retrieval as measured experiments against the existing baseline.
4. **Evidence packaging for generation** — pass the LLM compact, citation-ready evidence packs rather than loosely selected page text.
5. **Multi-format ingestion** — extending beyond PDFs to HTML, Word, Excel, or API-served data sources (longer-term).
6. **Adaptation to other contexts** — the architecture is not KNBS-specific and could be applied to other national statistics offices.

For detail on each area see [docs/future-development/](./future-development/).

---

## 8. Technical Reference

| Document | Purpose |
|---|---|
| [architecture/README.md](./architecture/README.md) | Technical overview of the four pipeline stages and evaluation feedback loop |
| [guides/OPERATING_MANUAL.md](./guides/OPERATING_MANUAL.md) | Running the data pipeline and API; configuration and troubleshooting |
| [tests/accuracy/README.md](../tests/accuracy/README.md) | Evaluation workflow, benchmark documentation, metric definitions |
| [reference/config_guide.md](./reference/config_guide.md) | Full `main.toml` configuration reference |
| [reports/](./reports/) | Accuracy evaluation reports and accuracy monitoring recommendations |
