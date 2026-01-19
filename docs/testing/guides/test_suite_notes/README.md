# Test Suite Notes (Index)

This folder contains “why this test exists” documentation: short, maintainable explanations of what each important test module covers and why that coverage is sufficient for StatsChat-KE.

## Recommended Structure
This folder mirrors the structure under `tests/` so paths are stable and easy to map:
- `tests/unit/...` → `docs/testing/guides/test_suite_notes/unit/...`
- `tests/integration/...` → `docs/testing/guides/test_suite_notes/integration/...`
- `tests/e2e/...` → `docs/testing/guides/test_suite_notes/e2e/...`
- `tests/test_data/...` → `docs/testing/guides/test_suite_notes/test_data/...`

## Naming Convention
Prefer doc names that match the test module so it’s obvious what they describe:
- `test_pdf_to_json.py` → `pdf_to_json_unit_tests.md`

(Exact mirroring is optional; clarity is the goal.)

## Current Notes
- [docs/testing/guides/test_suite_notes/unit/pdf_processing/pdf_to_json_unit_tests.md](docs/testing/guides/test_suite_notes/unit/pdf_processing/pdf_to_json_unit_tests.md)

## How To Add a New Note
For each meaningful test module:
1. Summarize the production code contract it protects.
2. List each test and the behavior it asserts.
3. Call out what is intentionally not tested (and why).
4. Mention determinism choices (mocks, temp dirs, clock freezing).
5. Include a quick “how to run” command, e.g. `pytest tests/unit/... -q`.
