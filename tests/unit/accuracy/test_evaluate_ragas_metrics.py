"""Sanity checks for deterministic evidence-span matching."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_evaluate_ragas():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "tests" / "accuracy" / "evaluate_ragas.py"
    spec = spec_from_file_location("evaluate_ragas_metrics_module", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_span_match_finds_short_quote_in_long_chunk():
    module = _load_evaluate_ragas()

    exact_hit, fuzzy_hit, span_hit, best_ratio = module.compute_span_match(
        "The most commonly found item in Kenyan households is a mobile phone (94%).",
        [
            (
                "Title: KDHS 2022\nRelease date: ...\n\n"
                "Household characteristics... The most commonly found item in "
                "Kenyan households is a mobile phone (94%). Other common items..."
            )
            * 3
        ],
        fuzzy_threshold=85.0,
    )

    assert exact_hit is True
    assert fuzzy_hit is True
    assert span_hit is True
    assert best_ratio >= 85.0
