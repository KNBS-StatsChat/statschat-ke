# 2026-01-21: Local/Cloud LLM run hardening

## Summary
Investigated local and cloud LLM execution paths. Cloud mode ran successfully for the configured question and returned a valid response. Local mode executed but produced non-JSON output, leading to parse errors. Implemented small guardrails to make both paths more robust when questions return few/no relevant documents and to reduce JSON parse failures in the local run.

## Changes applied
- Cloud mode: ensured `make_query()` always returns a consistent three-item tuple, even when zero documents are found. This prevents unpacking errors for questions that do not retrieve any matches.
- Cloud mode: added a guard in the CLI output block so placeholder string references (when no suitable PDFs are found) do not get treated as dicts.
- Local mode:
  - Added guards for empty or single-document retrieval results (fail fast or pad second context).
  - Switched to deterministic generation with explicit `attention_mask`, `pad_token_id`, and `do_sample=False`.
  - Extract the first JSON object from the model output before parsing to reduce JSON decode failures.
  - Set `tokenizer.pad_token` to `eos_token` if absent.

## Files updated
- statschat/generative/cloud_llm.py
- statschat/generative/local_llm.py

## Verification
- Cloud run executed successfully and returned a valid answer for the sample question.
- Local run executed successfully; JSON parsing is now more resilient, though output validity still depends on model adherence to the prompt.

## Notes
- Local LLM output can still be non-JSON; the extraction step improves recoverability but cannot guarantee perfect adherence.
- If zero documents are returned for a query, results now fail gracefully instead of throwing index or unpacking errors.
