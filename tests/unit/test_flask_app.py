"""Focused tests for the restored Flask demo frontend.

These tests intentionally cover the demo-only behavior that differs from the
benchmark/evaluator path:
- user-friendly refusal messaging
- answer-card citation selection from visible references
- fallback to backend-provided citation metadata
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_flask_app_module():
    module_path = Path(__file__).resolve().parents[2] / "flask-app" / "app.py"
    spec = importlib.util.spec_from_file_location(
        "statschat_demo_flask_app", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_infer_exact_cited_source_prefers_visible_reference_over_backend_citation():
    flask_app = _load_flask_app_module()
    references = [
        {
            "title": "2023 Kenya Vital Statistics Report",
            "page_number": 61,
            "page_url": "https://example.com/vital-2023.pdf#page=61",
            "page_content": (
                "Kenya between 2019 and 2023. The expected births in 2023 were "
                "1,547,260. The registered number of births during the same year "
                "was 1,192,884, representing a coverage of 77.1 percent."
            ),
        },
        {
            "title": "2024 Economic Survey",
            "page_number": 432,
            "page_url": "https://example.com/econ-2024.pdf#page=432",
            "page_content": (
                "A total of 1,192,884 births were registered in Kenya in 2023 "
                "while expected births were 1,557,370."
            ),
        },
    ]
    payload = {
        "answer": "A total of 1,192,884 births were registered in Kenya in 2023.",
        "debug_response": {
            "most_likely_answer": (
                "A total of 1,192,884 births were registered in Kenya in 2023."
            ),
            "highlighting1": [],
            "highlighting2": [],
            "highlighting3": [],
            "exact_cited_source": {
                "label": "2024 Economic Survey, page 432",
                "page_url": "https://example.com/econ-2024.pdf#page=432",
                "quote": "A total of 1,192,884 births were registered in Kenya in 2023.",
            },
        },
    }

    source = flask_app.infer_exact_cited_source(references, payload)

    assert source is not None
    assert source["label"] == "2023 Kenya Vital Statistics Report, page 61"


def test_infer_exact_cited_source_falls_back_to_backend_when_visible_reference_is_weak():
    flask_app = _load_flask_app_module()
    references = [
        {
            "title": "2023 Kenya Vital Statistics Report",
            "page_number": 61,
            "page_url": "https://example.com/vital-2023.pdf#page=61",
            "page_content": "This page discusses birth registration generally.",
        }
    ]
    payload = {
        "answer": "A total of 1,192,884 births were registered in Kenya in 2023.",
        "debug_response": {
            "most_likely_answer": (
                "A total of 1,192,884 births were registered in Kenya in 2023."
            ),
            "highlighting1": [],
            "highlighting2": [],
            "highlighting3": [],
            "exact_cited_source": {
                "label": "2024 Economic Survey, page 432",
                "page_url": "https://example.com/econ-2024.pdf#page=432",
                "quote": "A total of 1,192,884 births were registered in Kenya in 2023.",
            },
        },
    }

    source = flask_app.infer_exact_cited_source(references, payload)

    assert source is not None
    assert source["label"] == "2024 Economic Survey, page 432"


def test_search_route_renders_demo_refusal_message(monkeypatch):
    flask_app = _load_flask_app_module()

    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {
                "answer": "",
                "references": [],
                "response_time_seconds": 1.25,
                "debug_response": {},
            }

    monkeypatch.setattr(
        flask_app.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )
    monkeypatch.setattr(
        flask_app,
        "render_template",
        lambda template_name, **context: (
            f"{context['results']['display_answer']}|"
            f"{'No supporting KNBS publication was returned for this question.' if not context['results']['references'] and context['results']['is_demo_refusal'] else ''}"
        ),
    )

    with flask_app.app.test_request_context(
        "/search",
        query_string={"q": "What is the salary of the KNBS Director General?"},
    ):
        response = flask_app.search()

    assert flask_app.DEMO_UNSUPPORTED_MESSAGE in response
    assert "No supporting KNBS publication was returned for this question." in response


def test_search_route_sends_raw_question_and_defaults_to_all_publications(monkeypatch):
    flask_app = _load_flask_app_module()
    captured: dict[str, object] = {}

    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {
                "answer": "5.9 per cent",
                "references": [],
                "debug_response": {},
            }

    def fake_get(*args, **kwargs):
        captured["params"] = kwargs["params"]
        return FakeResponse()

    monkeypatch.setattr(flask_app.requests, "get", fake_get)
    monkeypatch.setattr(
        flask_app,
        "render_template",
        lambda template_name, **context: context["results"],
    )

    with flask_app.app.test_request_context(
        "/search",
        query_string={"q": "What was Kenya's GDP growth rate in Quarter 3 of 2023?"},
    ):
        results = flask_app.search()

    assert (
        captured["params"]["q"]
        == "What was Kenya's GDP growth rate in Quarter 3 of 2023?"
    )
    assert captured["params"]["content_type"] == "all"
    assert results["display_answer"] == "5.9 per cent"


def test_search_route_hides_citations_and_references_for_demo_refusal(monkeypatch):
    flask_app = _load_flask_app_module()

    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {
                "answer": "No suitable PDFs found for this question. Please try rephrasing.",
                "references": [
                    {
                        "title": "Kenya Quarterly Gross Domestic Product Third Quarter 2022",
                        "page_number": 2,
                        "page_url": "https://example.com/gdp-2022.pdf#page=2",
                        "page_content": "The country's real GDP expanded by 4.7 per cent.",
                    }
                ],
                "debug_response": {
                    "exact_cited_source": {
                        "label": "Kenya Quarterly Gross Domestic Product Third Quarter 2016, page 3",
                        "page_url": "https://example.com/gdp-2016.pdf#page=3",
                        "quote": "The country's real GDP expanded...",
                    },
                    "generation_context_sources": [
                        {
                            "label": "Kenya Quarterly Gross Domestic Product Third Quarter 2016, page 3",
                            "page_url": "https://example.com/gdp-2016.pdf#page=3",
                        }
                    ],
                },
                "response_time_seconds": 1.0,
            }

    monkeypatch.setattr(
        flask_app.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )
    monkeypatch.setattr(
        flask_app,
        "render_template",
        lambda template_name, **context: context["results"],
    )

    with flask_app.app.test_request_context(
        "/search",
        query_string={"q": "What was Kenya's GDP growth rate in Quarter 3 of 2023?"},
    ):
        results = flask_app.search()

    assert results["display_answer"] == flask_app.DEMO_UNSUPPORTED_MESSAGE
    assert results["is_demo_refusal"] is True
    assert results["references"] == []
    assert results["exact_cited_source"] is None
    assert results["generation_context_sources"] == []
