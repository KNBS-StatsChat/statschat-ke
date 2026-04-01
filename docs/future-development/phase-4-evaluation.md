# Phase 4: Evaluation

Future improvements to the accuracy evaluation system (`tests/accuracy/evaluate_accuracy.py`).

## Candidate Improvements

### Summary metrics CSV
- `summary_metrics.csv` is now generated per run — consider tooling to diff or trend these across timestamped runs automatically.

### Cross-run comparison
- Build a script that reads `summary_metrics.csv` from multiple run folders and produces a comparison table or chart.
- Could live in `scripts/` or as a `--compare` flag on the evaluator itself.

### Retrieval metrics from API references
- Currently retrieval metrics (Precision@k, Recall@k, MRR, nDCG) use `similarity_search()` as a proxy rather than the actual ranked list in the API response.
- A future enhancement could compare API-returned references directly against golden doc IDs for a more faithful retrieval quality measure.

### CI integration
- Run evaluation automatically in GitHub Actions against a cloud API endpoint after merges to main.
- Would require a QA sheet committed to the repo and a cloud API key as a repository secret.

## Notes

- The evaluation system currently works for both local and cloud modes using the same QA data, metrics, and output format.
- Run outputs are timestamped and gitignored under `tests/accuracy/runs/`.
