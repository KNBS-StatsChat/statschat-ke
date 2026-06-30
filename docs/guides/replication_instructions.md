# Replicating the April 2026 StatsChat Accuracy Results

**Branch:** `test_infra` | **Commit:** `4a49039`

## Prerequisites

- Python virtual environment set up (`source .venv/bin/activate`)
- `.env` file with a valid `OPENROUTER_API_KEY`
- The 1,176 JSON files already present in `data/json_conversions/`

---

## Step 1 — Check you're on the right branch and commit

```bash
git switch test_infra
git pull
git rev-parse --short HEAD  # should show 4a49039
```

---

## Step 2 — Rebuild the FAISS index

The index files are not committed to the repo (they're too large). You need to build them locally before running any evaluations. This takes around 90 minutes on a MacBook.

The config in `statschat/config/main.toml` is already set correctly for this — do not change it. Just run:

```bash
python statschat/embedding/preprocess.py 2>&1 | tee log/rebuild_index.log
```

When it finishes you should see:

```
Vector store saved to data/db_langchain_rebuild_v1
setup of docstore should be complete.
```

And these two directories should now exist:

- `data/json_split_rebuild_v1/` (~66,000 files)
- `data/db_langchain_rebuild_v1/` (`index.faiss` ~776 MB, `index.pkl` ~283 MB)

---

## Step 3 — Run the test suite

```bash
python -m pytest -q
```

Expect: **231 passed, 1 failed**. The 1 failure (`test_validate_page_splitting`) is a known pre-existing issue with a corrupted PDF and is not a regression.

---

## Step 4 — Run the GPT-5.4-mini benchmark

Start the API in one terminal:

```bash
uvicorn fast-api.main_api_cloud:app --host 127.0.0.1 --port 8001
```

Wait for it to say `Application startup complete`, then in a second terminal verify the health check:

```bash
curl -s http://127.0.0.1:8001/health
# Check: "model": "openai/gpt-5.4-mini" and "exists": true for the faiss path
```

Then run the benchmark (takes ~5–6 minutes):

```bash
python tests/accuracy/evaluate_accuracy.py \
  --excel tests/accuracy/StatsChat_QA_Verified_Audited.xlsx \
  --host http://127.0.0.1:8001 \
  --api-mode cloud \
  --content-type all \
  --retrieval-k 8 \
  --timeout 420
```

**Expected results:** Answerable accuracy ~0.918–0.934, unanswerable 1.000, false answer rate 0.000.

Run outputs are saved automatically to `tests/accuracy/runs/cloud/<timestamp>/`.

---

## Step 5 — Run the Mistral Small benchmark (optional)

> **Model substitution required:** `mistralai/mistral-small-3.1-24b-instruct` has a confirmed OpenRouter serving bug as of May 2026 — it returns `finish_reason: None` after 9 tokens regardless of `max_tokens`. Use `mistralai/mistral-small-24b-instruct-2501` (same 24B family, January 2025 release) as a substitute.

Stop the API, then edit `statschat/config/main.toml` — comment out the GPT line and uncomment the Mistral line:

```toml
# generative_model_name_cloud = "openai/gpt-5.4-mini"
generative_model_name_cloud = "mistralai/mistral-small-24b-instruct-2501"
```

Restart the API and re-run the same benchmark command as Step 4. Verify the health check shows the Mistral model before starting.

**Expected results:** Answerable accuracy ~0.776, unanswerable 1.000, false answer rate 0.000. Results will differ from the April 2026 report's Mistral figures (0.820) because the original model is unavailable. Restore the GPT config line when done.

---

## Reference files

| File | What it contains |
|---|---|
| `docs/investigations/2026-04-replication-log.md` | Full step-by-step log with expected vs actual results |
| `docs/saved_runs/2026-04-24_103041/` | GPT reference run outputs |
| `docs/saved_runs/2026-04-24_103554/` | Mistral 3.1 April run (generation failed — retrieval metrics valid) |
| `docs/saved_runs/2026-05-06_145706/` | Mistral 2501 May run (generation working) |
| `statschat/config/main.toml` | All config settings used |
