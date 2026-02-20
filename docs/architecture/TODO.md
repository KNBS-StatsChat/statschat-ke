# Architecture Documentation - TODO

Tracking planned documentation work and improvements in the Architecture folder.

---

## Planned Documents

### Hub Document
- [x] `README.md` - Architecture overview (2-3 pages, links to spokes)

### Pipeline Documents (Spokes)
- [x] `pipeline-pdf-ingestion.md` - PDF download → JSON conversion
- [x] `pipeline-embedding.md` - JSON → FAISS vector store
- [x] `pipeline-retrieval.md` - Semantic search & Reranking
- [x] `pipeline-generation.md` - LLM interaction & Response parsing
- [ ] `data-flow.md` - What data exists where, schemas, directory structure

### Completed
- [x] `token-usage-guide.md` - Token calculation and configuration tuning

---

## Diagram Opportunities

Places where a Mermaid or image diagram would improve understanding:

| Location | Diagram Type | Description |
|----------|--------------|-------------|
| Hub README | Flowchart | High-level architecture showing all 4 pipelines |
| `pipeline-pdf-ingestion.md` | Sequence diagram | KNBS website → download → JSON conversion flow |
| `pipeline-embedding.md` | Flowchart | JSON → splitting → embedding → FAISS merge |
| `pipeline-retrieval.md` | Sequence diagram | Query → search → rerank → context selection |
| `pipeline-generation.md` | Sequence diagram | Context → LLM → JSON → Highlighting |
| `token-usage-guide.md` | Bar chart | Token distribution visualization |

---

## Other Improvements

- [ ] Add cross-references between `docs/cost.md` and `docs/architecture/token-usage-guide.md`
- [ ] Consider consolidating `config_guide.md` and `search_config_paramaters.md`
- [ ] Add CHANGELOG.md for version history
- [ ] Document the JSON schema produced by `pdf_to_json.py`
- [ ] Add ADR for embedding model selection (`all-mpnet-base-v2`)

---

## Notes

_Add notes from documentation discussions here._

---

## Open Investigation TODOs (KNBS / StatsChat-KE)

### Vector store path normalization
- [ ] Normalize `faiss_db_root` handling so `data_dir="data/"` + `faiss_db_root="data/db_langchain"` does not write to `data/data/db_langchain`.
- [ ] Ensure query paths (local + cloud) read from the same canonical directory (`data/db_langchain`).

### "No text extracted" publications

31 publications produced JSON conversions with `total_chars=0` (no extracted text) and therefore generated no split JSON sections and no embeddings.

- [ ] Manually inspect a sample of these PDFs to determine whether they are image-only scans, protected/encrypted, or otherwise incompatible with current extraction.
- [ ] Decide on extraction strategy for these (e.g. pdfplumber fallback, alternative PyMuPDF text modes, or OCR pipeline).

Current list (internal `id` -> JSON filename):
- 1132500 -> 2002-Statistical-Abstract.json
- 2360006 -> 2008-Statistical-Abstract.json
- 2752257 -> Kenya-Construction-Input-Price-Index-Third-Quarter-2022.json
- 3015719 -> Quarterly-Labour-Force-Report-2021-Quarter-3.json
- 3098027 -> 2000-Statistical-Abstract.json
- 3855672 -> Kenya-Consumer-Price-Indices-and-Inflation-Rates-September-2023.json
- 3908189 -> 2013-Economic-Survey.json
- 4047991 -> Kenya-Producer-Price-Index-Second-Quarter-2020.json
- 4086536 -> 2012-Statistical-Abstract.json
- 4946465 -> 2004-Statistical-Abstract.json
- 5627601 -> 2003-Statistical-Abstract.json
- 5823475 -> 2006-Statistical-Abstract.json
- 6063256 -> Kenya-Producer-Price-Index-Second-Quarter-2022.json
- 6229249 -> Kenya-Construction-Input-Price-Index-Second-Quarter-2022.json
- 6272542 -> 2010-Statistical-Abstract.json
- 6388048 -> 2009-Statistical-Abstract.json
- 6391849 -> Kenya-Construction-Input-Price-Index-Fourth-Quarter-2021.json
- 6657596 -> 2011-Statistical-Abstract.json
- 6853782 -> Quarterly-Labour-Force-Report-2022-Quarter-3.json
- 7004466 -> Kenya-Construction-Input-Price-Index-Fourth-Quarter-2022.json
- 7161597 -> 2001-Statistical-Abstract.json
- 7574738 -> Kenya-Producer-Price-Index-Fourth-Quarter-2021.json
- 7615465 -> Kenya-Producer-Price-Index-Fourth-Quarter-2022.json
- 7679433 -> Quarterly-Labour-Force-Report-2021-Quarter-2.json
- 7765017 -> Kenya-Consumer-Price-Indices-and-Inflation-Rates-October-2023.json
- 8603354 -> Kenya-Producer-Price-Index-Third-Quarter-2022.json
- 8662638 -> Quarterly-Labour-Force-Report-2022-Quarter-1.json
- 8921591 -> Quarterly-Labour-Force-Report-2021-Quarter-4.json
- 9204525 -> 2007-Statistical-Abstract.json
- 9342195 -> Quarterly-Labour-Force-Report-2022-Quarter-2.json
- 9349701 -> 2005-Statistical-Abstract.json

### KNBS 404 link rot
- [ ] Manually review the 404 PDF URLs and their report pages to confirm whether PDFs moved/renamed and whether alternate mirrors exist.

### MuPDF warnings (shading/colorspace)
- [ ] Triage warnings for “suspiciously empty” extracted text on affected pages and determine whether warnings correlate with lost text.
