from statschat.generative.response_model import LlmResponse


def test_llmresponse_defaults_and_fields():
    # Provide required fields explicitly per model definition
    r = LlmResponse(answer_provided=True, most_likely_answer=None, highlighting1=[], highlighting2=[], highlighting3=[], reasoning=None)
    assert r.answer_provided is True
    # highlighting lists should be empty lists
    assert isinstance(r.highlighting1, list) and r.highlighting1 == []
    assert isinstance(r.highlighting2, list) and r.highlighting2 == []
    assert isinstance(r.highlighting3, list) and r.highlighting3 == []


def test_llmresponse_accepts_full_payload():
    r = LlmResponse(
        answer_provided=False,
        most_likely_answer=None,
        highlighting1=["a"],
        highlighting2=["b"],
        highlighting3=[],
        reasoning="explain",
    )
    assert r.answer_provided is False
    assert r.reasoning == "explain"
    assert r.highlighting1 == ["a"]
