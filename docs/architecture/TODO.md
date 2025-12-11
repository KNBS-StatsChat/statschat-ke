# Architecture Documentation - TODO

Tracking planned documentation work and improvements.

---

## Planned Documents

### Hub Document
- [ ] `README.md` - Architecture overview (2-3 pages, links to spokes)

### Pipeline Documents (Spokes)
- [ ] `pipeline-pdf-ingestion.md` - PDF download → JSON conversion
- [ ] `pipeline-embedding.md` - JSON → FAISS vector store  
- [ ] `pipeline-rag-query.md` - Query → LLM response
- [ ] `data-flow.md` - What data exists where, schemas, directory structure

### Completed
- [x] `token-usage-guide.md` - Token calculation and configuration tuning

---

## Diagram Opportunities

Places where a Mermaid or image diagram would improve understanding:

| Location | Diagram Type | Description |
|----------|--------------|-------------|
| Hub README | Flowchart | High-level architecture showing all 3 pipelines |
| `pipeline-pdf-ingestion.md` | Sequence diagram | KNBS website → download → JSON conversion flow |
| `pipeline-embedding.md` | Flowchart | JSON → splitting → embedding → FAISS merge |
| `pipeline-rag-query.md` | Sequence diagram | Query → search → context selection → LLM → response |
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
