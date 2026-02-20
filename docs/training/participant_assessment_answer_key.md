# Participant Assessment — Answer Key (organiser-only)

This document provides **expected answers** for the objectively-gradable questions in the participant questionnaire, plus brief notes on how to interpret the self-report/free-text items.

Source questionnaire: [docs/training/participant_assessment.md](docs/training/participant_assessment.md)

---

## Quick scoring (suggested)

Use this only if you want a lightweight, consistent way to identify who might benefit from a short pre-course prep session.

- **Python/Data readiness**: C1–C4 (0–4 points)
  - 1 point per correct answer.
  - 0–1: recommend Python/pandas pre-session
  - 2–3: ok for core course, may need support
  - 4: can handle faster pace
- **RAG concepts**: E1–E5 (0–5 points)
  - 1 point per correct answer.
  - 0–2: spend time on RAG mental model early
  - 3–4: ok for core concepts
  - 5: can move quickly into implementation details
- **API basics**: F2 (0–1 point)

---

## Section C — Short skills check (Python + data)

### C1
**Question:** Output of:

```python
x = [1, 2, 3]
y = x
y.append(4)
print(x)
```

**Expected answer:** `[1, 2, 3, 4]`

**Explanation:** `y = x` does not create a copy; `x` and `y` reference the same list object. `append` mutates the list in place.

---

### C2
**Question:** Which line reads a JSON file robustly and cross-platform?

**Expected answer:** `data = json.loads(Path('file.json').read_text(encoding='utf-8'))`

**Explanation:** Cross-platform file paths are handled by `Path(...)`, and `encoding='utf-8'` avoids common decoding issues. (In production code, a very common alternative is `with open(..., encoding='utf-8') as f: json.load(f)`; it’s not one of the provided options.)

---

### C3
**Question:** Fix for `ModuleNotFoundError: No module named 'fastapi'`.

**Expected answer:** Install the missing package in the active environment (e.g., `pip install fastapi`).

**Explanation:** The error indicates the current Python environment cannot import the module. The fix is to install it into that environment (or switch to the correct environment).

---

### C4
**Question:** What does `groupby` help you do?

**Expected answer:** Split data into groups and compute summaries per group.

**Explanation:** Typical usage is aggregation/statistics by category (e.g., totals by county, average by month).

---

## Section E — RAG / StatsChat concepts

### E1
**Question:** Correct pipeline ordering.

**Expected answer:** Download PDFs → Convert to JSON → Chunk text → Create embeddings → Build FAISS index

**Explanation:** You need text extraction/structuring before chunking, and chunking before embedding/indexing.

---

### E2
**Question:** What is an embedding?

**Expected answer:** A compressed numeric representation of text meaning used for similarity search.

**Explanation:** Embeddings map text into vectors such that semantically similar text is close in vector space.

---

### E3
**Question:** What does a vector store (FAISS) do?

**Expected answer:** Stores and searches embeddings to retrieve relevant text chunks.

**Explanation:** FAISS is for efficient similarity search (nearest-neighbor lookup) over vectors.

---

### E4
**Question:** Purpose of retrieval in RAG.

**Expected answer:** Find relevant context passages to constrain the LLM.

**Explanation:** Retrieval narrows the evidence/context; generation should then be grounded in that retrieved context.

---

### E5
**Question:** Best description of hallucination risk.

**Expected answer:** The model may produce fluent but incorrect statements not supported by sources.

**Explanation:** Hallucination is a key operational risk; mitigations include retrieval grounding, prompt constraints, and evaluation.

---

### E6 (experience question; not “right/wrong”)
**Question:** Prior experience evaluating LLM/RAG responses.

**How to interpret:**
- **No / informal only**: plan to teach a simple evaluation rubric and “how to verify against sources” early.
- **Simple rubric**: good fit for structured exercises (accuracy, coverage, citation quality).
- **Structured evaluation**: can move faster; consider giving them deeper topics (evaluation datasets, failure analysis, calibration, monitoring).

---

## Section F — API & deployment

### F2
**Question:** What does `uvicorn` do?

**Expected answer:** Runs the API server process.

**Explanation:** `uvicorn` is an ASGI server commonly used to run FastAPI apps.

---

### F4 (experience question; not “right/wrong”)
**Question:** GPU / high-performance CPU experience for inference.

**How to interpret:**
- Low experience is common; don’t treat it as a blocker unless the course depends on running a local LLM.
- If many participants are low here, prefer cloud inference for demos, or provide a pre-configured environment.

---

## Self-report / free-text items (guidance)

These don’t have expected “correct answers”, but they are useful signals.

- **A3 / A4**: Use to tailor examples and exercises (user-focused vs builder/operator-focused).
- **B2 / B3**: Biggest practical risk indicators (permissions, ability to install Python deps, use `.env`, run `uvicorn`).
- **D1 / D2 / D3**: Predicts how much time will be spent on repo workflow, debugging, and test/lint friction.
- **G2**: Watch for low bandwidth, locked-down laptops, or restricted access to external APIs; these often determine the delivery model.
