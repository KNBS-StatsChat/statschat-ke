"""Prompt-contract tests.

Validates required input variables and basic formatting for local/cloud prompts.
"""

from statschat.generative.prompts_local import (
    EXTRACTIVE_PROMPT_PYDANTIC as LOCAL_PROMPT,
    STUFF_DOCUMENT_PROMPT as LOCAL_DOC_PROMPT,
)
from statschat.generative.prompts_cloud import (
    EXTRACTIVE_PROMPT_PYDANTIC as CLOUD_PROMPT,
    STUFF_DOCUMENT_PROMPT as CLOUD_DOC_PROMPT,
)


def test_local_prompt_structure():
    """
    Verify that the LOCAL prompt template requests the necessary input variables.
    """
    expected_vars = {
        "QuestionPlaceholder",
        "ContextsPlaceholder",
    }
    assert set(LOCAL_PROMPT.input_variables) == expected_vars


def test_cloud_prompt_structure():
    """
    Verify that the CLOUD prompt template requests the necessary input variables.
    """
    expected_vars = {
        "question",
        "summaries",
    }
    assert set(CLOUD_PROMPT.input_variables) == expected_vars


def test_local_prompt_formatting():
    """
    Verify that we can successfully format the local prompt.
    """
    formatted_prompt = LOCAL_PROMPT.format(
        QuestionPlaceholder="What is the GDP?",
        ContextsPlaceholder="Context1: GDP is High.\n\nContext2: Inflation is Low.",
    )

    assert "What is the GDP?" in formatted_prompt
    assert "GDP is High." in formatted_prompt
    assert "Inflation is Low." in formatted_prompt
    assert "==RESPONSE FORMAT==" in formatted_prompt
    assert "answer_provided" in formatted_prompt


def test_cloud_prompt_formatting():
    """
    Verify that we can successfully format the cloud prompt.
    """
    formatted_prompt = CLOUD_PROMPT.format(
        question="What is the GDP?", summaries="GDP is High."
    )

    assert "What is the GDP?" in formatted_prompt
    assert "GDP is High." in formatted_prompt
    assert "==RESPONSE FORMAT==" in formatted_prompt
    assert "answer_provided" in formatted_prompt


def test_cloud_prompt_contains_guardrail_boundaries():
    formatted_prompt = CLOUD_PROMPT.format(
        question="Compare Kenya and Nigeria inflation.", summaries="Kenya CPI was 3%."
    )

    assert "statistics for other countries" in formatted_prompt
    assert "Do not provide policy advice" in formatted_prompt
    assert "set answer_provided to false" in formatted_prompt


def test_document_prompts():
    """
    Verify the document formatting templates used for RAG context.
    """
    # Both use the same structure: <Doc{doc_num} published_date={date} title={title}>{page_content}</Doc{doc_num}>
    for name, doc_prompt in [("Local", LOCAL_DOC_PROMPT), ("Cloud", CLOUD_DOC_PROMPT)]:
        formatted = doc_prompt.format(
            doc_num=1,
            date="2023-01-01",
            title="Economic Survey",
            page_content="The economy grew.",
        )

        expected = "<Doc1 published_date=2023-01-01 title=Economic Survey>The economy grew.</Doc1>"
        assert formatted == expected
