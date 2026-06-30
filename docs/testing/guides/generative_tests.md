# Generative Tests

These tests document and protect the generation layer (prompt contracts, response formatting/parsing, and small utility helpers).

## Where the Tests Live

- `tests/unit/generative/test_prompts.py`
- `tests/unit/generative/test_local_llm_format.py`
- `tests/unit/generative/test_utils.py`

## What These Tests Protect

- **Prompt contracts**: required input variables remain consistent as prompts evolve
- **Formatting/parsing**: response formatting is robust to malformed outputs
- **Post-processing helpers**: deduplication, highlighting, and context trimming behave predictably

## Maintainership Notes

### Prompts as Contracts

Treat prompt templates as a public interface:
- adding/removing prompt variables can break callers
- formatting errors can silently degrade RAG quality

The prompt tests are intentionally “shallow”: they focus on variables and formatting outputs rather than model quality.

### Utilities

Utility tests should remain fast and deterministic.
If a helper starts depending on I/O (files, network, model calls), consider splitting responsibilities so the core logic remains unit-testable.

## How to Run

```bash
pytest tests/unit/generative/ -v

pytest tests/unit/generative/test_prompts.py -v
pytest tests/unit/generative/test_utils.py::test_deduplicator_removes_duplicates_preserving_first -v
```

## When to Update These Tests

Update/add generative tests when:
- prompt templates change (variables, markers, response schema)
- response schema changes (e.g., the `LlmResponse` model)
- formatting rules change (e.g., how errors are surfaced)
