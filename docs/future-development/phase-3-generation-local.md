# Phase 3: Generation (Local)

Future improvements to local LLM generation in the StatsChat-KE pipeline.

## Known Issues

### Local API generation timeout
- The local API (`fast-api/main_api_local.py`) uses Mistral-7B-Instruct-v0.3 via `transformers` and runs `model.generate()` with no timeout or early stopping.
- On machines without a dedicated GPU, generation can take longer than the evaluator's HTTP timeout (420–600s), causing all queries to fail with read timeouts.
- The `debug` query parameter is accepted by the local `/search` endpoint but is currently ignored — the response is identical regardless of its value.

## Candidate Improvements


### Implement `debug` response for local
- The cloud API returns `debug_response` containing reasoning, highlighting, and context metadata when `debug=true`.
- The local API could return equivalent fields (`context_from`, `context_reference`, `relevant_publications` are already computed internally but only partially exposed in the response).

### GPU/MPS acceleration
- The model loads with `device_map="auto"` and `float16`, which should use MPS on Apple Silicon.
- Investigate whether MPS is actually being used for generation or if it falls back to CPU.
- Consider quantisation (4-bit via `bitsandbytes` or GGUF via `llama.cpp`) for faster local inference.

## Notes

- Current model: `mistralai/Mistral-7B-Instruct-v0.3`
- The local API is single-threaded (uvicorn default) — a hung generation blocks all subsequent requests.
