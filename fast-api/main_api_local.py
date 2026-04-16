from pydantic import BaseModel, Field
from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import logging
import re
import torch
from datetime import datetime
from markupsafe import escape
from transformers import AutoModelForCausalLM, AutoTokenizer

from statschat import load_config
from statschat.api_common import (
    build_health_payload,
    configure_api_logging,
    configure_cors,
    configure_request_logging,
    protected_endpoint_dependencies,
)
from statschat.generative.query_policy import (
    guardrail_refusal_reason,
    has_temporal_constraint,
)
from statschat.generative.local_llm import (
    similarity_search,
    select_generation_contexts,
    generate_response,
    format_response,
)
from statschat.generative.prompts_local import (
    _extractive_prompt,
    _core_prompt,
    _format_instructions,
)

# Config file to load
CONFIG = load_config(name="main")
SEARCH_CONFIG = CONFIG.get("search", {})

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_api_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
configure_api_logging(logger, SESSION_NAME)


app = FastAPI(
    title="KNBS StatsChat API",
    description=(
        "Read more in [blog post]"
        + "(https://datasciencecampus.ons.gov.uk/using-large-language-models-llms-to-improve-website-search-experience-with-statschat/)"  # noqa: E501
        + " or see [the code repository]"
        + "(https://github.com/datasciencecampus/statschat-app). "
        + "Frontend UI available internally [here]"
        + "(http://localhost:5000)."
    ),
    summary="""Experimental search of Kenya National Bureau of Statistics publications.
        Using retrieval augmented generation (RAG).""",
    version="0.1.1",
    contact={
        "name": "Kenya National Bureau of Statistics",
        "email": "test@knbs.com",
    },
)
configure_cors(app)
configure_request_logging(app, logger, api_mode="local")


# Model configuration (loaded once at startup from shared config)
MODEL_ID = str(
    SEARCH_CONFIG.get("generative_model_name_local")
    or SEARCH_CONFIG.get("generative_model_name")
    or "mistralai/Mistral-7B-Instruct-v0.3"
)
MODEL: Optional[AutoModelForCausalLM] = None
TOKENIZER: Optional[AutoTokenizer] = None


@app.on_event("startup")
async def load_model() -> None:
    """Load the model and tokenizer once at startup for faster queries."""
    global MODEL, TOKENIZER
    if MODEL is not None and TOKENIZER is not None:
        return

    logger.info("Building the tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Loading the model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.float16,  # Use float16 for efficiency if using a GPU
        device_map="auto",  # Automatically selects GPU if available
    )

    TOKENIZER = tokenizer
    MODEL = model


@app.get("/", tags=["Principle Endpoints"])
async def about():
    """Access the API documentation in json format.

    Returns:
        Redirect to /openapi.json
    """
    response = RedirectResponse(url="/openapi.json")
    return response


@app.get("/health", tags=["Principle Endpoints"])
async def health():
    """Return API liveness and non-secret runtime status."""

    return build_health_payload(
        api_mode="local",
        config=CONFIG,
        model_name=MODEL_ID,
        provider="local",
        model_loaded=MODEL is not None and TOKENIZER is not None,
    )


@app.get(
    "/search",
    tags=["Principle Endpoints"],
    dependencies=protected_endpoint_dependencies(),
)
async def search(
    q: str,
    content_type: Union[str, None] = "latest",
    debug: bool = True,
):
    """Search KNBS publications and bulletins for a question.

    Args:
        q (str): Question to be answered based on KNBS publications and bulletins.
        content_type (Union[str, None], optional): Type of content to be searched.
            Currently accepted values: 'latest' to search the latest bulletins only
            or 'all' to search any publications and bulletins.
            Optional, defaults to 'latest'.
        debug (bool, optional): Flag to return debug information (full LLM response).
            Optional, defaults to True.

    Raises:
        HTTPException: 422 Validation error.

    Returns:
        HTTPresponse: 200 JSON with fields: question, content_type, answer, references
            and optionally debug_response.
    """
    question = escape(q).strip()
    if question in [None, "None", ""]:
        raise HTTPException(status_code=422, detail="Empty question")

    if content_type not in ["latest", "all"]:
        logger.warning('Unknown content type. Fallback to "latest".')
        content_type = "latest"

    guardrail_reason = guardrail_refusal_reason(question)
    if guardrail_reason:
        logger.info("Guardrail refusal: %s", guardrail_reason)
        return {
            "question": question,
            "content_type": content_type,
            "answer": "",
            "references": "",
            "context_from": "",
            "context_reference": "",
            "relevant_publication_one": "",
            "relevant_publication_two": "",
        }

    answer_threshold = float(CONFIG.get("search", {}).get("answer_threshold", 0.5))
    document_threshold = float(CONFIG.get("search", {}).get("document_threshold", 0.9))
    k_contexts = int(CONFIG.get("search", {}).get("k_contexts", 2))
    if k_contexts < 1:
        k_contexts = 1

    if MODEL is None or TOKENIZER is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    effective_latest_filter = content_type == "latest"
    if effective_latest_filter and has_temporal_constraint(question):
        logger.info(
            "Detected explicit temporal tokens in query; overriding "
            "latest_filter to False so historical reports remain searchable."
        )
        effective_latest_filter = False

    # Get the most relevant text chunks
    relevant_texts = similarity_search(question, latest_filter=effective_latest_filter)

    # Handle: no search results
    if not relevant_texts:
        results = {
            "question": question,
            "content_type": content_type,
            "answer": "No suitable PDFs found for this question. Please try rephrasing.",
            "references": "",
            "context_from": "",
            "context_reference": "",
            "relevant_publication_one": "",
            "relevant_publication_two": "",
        }
        logger.info(f"Sending following response: {results}")
        return results

    # Local retrieval normally provides a numeric similarity score. In tests/mocks it may be absent.
    # Defaulting to 0.0 avoids incorrectly treating results as "no suitable PDFs".
    top_score = float(relevant_texts[0].get("score", 0.0))

    # Handle: "no suitable PDFs" (keep answer consistent with references)
    if top_score > document_threshold:
        results = {
            "question": question,
            "content_type": content_type,
            "answer": "No suitable PDFs found for this question. Please try rephrasing.",
            "references": "",
            "context_from": "",
            "context_reference": "",
            "relevant_publication_one": "",
            "relevant_publication_two": "",
        }
        logger.info(f"Sending following response: {results}")
        return results

    # Select top contexts for generation (configurable via search.k_contexts).
    selected_matches = select_generation_contexts(relevant_texts, k_contexts=k_contexts)
    selected_contexts = [
        str(match.get("page_content", "")).strip()
        for match in selected_matches
        if str(match.get("page_content", "")).strip()
    ]
    if not selected_contexts:
        selected_matches = relevant_texts[:1]
        selected_contexts = [str(relevant_texts[0].get("page_content", ""))]
    contexts_block = "\n\n".join(
        f"Context{i}: {text}" for i, text in enumerate(selected_contexts, start=1)
    )

    specific_prompt = _extractive_prompt.format(
        QuestionPlaceholder=question,
        ContextsPlaceholder=contexts_block,
    )
    user_input = _core_prompt + specific_prompt + _format_instructions

    max_new_tokens = int(CONFIG.get("search", {}).get("llm_max_tokens", 512))
    # Keep generation bounds reasonable for local runtime.
    max_new_tokens = max(64, min(max_new_tokens, 800))
    raw_response = generate_response(
        user_input,
        MODEL,
        TOKENIZER,
        max_new_tokens=max_new_tokens,
    )
    formatted_response = format_response(raw_response)

    pub_one = selected_matches[0].get("title", "") if selected_matches else ""
    pub_two = selected_matches[1].get("title", "") if len(selected_matches) > 1 else ""

    context_from = str(formatted_response.get("where_context_from", "")).strip()
    context_index_match = re.search(
        r"context\s*(\d+)", context_from, flags=re.IGNORECASE
    )
    if context_index_match and selected_matches:
        context_index = int(context_index_match.group(1)) - 1
        if 0 <= context_index < len(selected_matches):
            reference_url = str(selected_matches[context_index].get("page_url", ""))
        else:
            reference_url = str(selected_matches[0].get("page_url", ""))
    else:
        reference_url = (
            str(selected_matches[0].get("page_url", "")) if selected_matches else ""
        )

    # If context is weak, avoid pretending we have a grounded answer.
    if top_score > answer_threshold:
        answer = (
            "No suitable answer found. "
            "However relevant information may be found in a PDF. "
            "Please check the link(s) provided."
        )
    else:
        answer = formatted_response.get("most_likely_answer")
        if not answer:
            answer = "No suitable answer found."

    results = {
        "question": question,
        "content_type": content_type,
        "answer": answer,
        "references": reference_url,
        "context_from": context_from,
        "context_reference": formatted_response.get("context_reference", ""),
        "relevant_publication_one": pub_one,
        "relevant_publication_two": pub_two,
    }

    logger.info(f"Sending following response: {results}")
    return results


class Feedback(BaseModel):
    rating: Union[str, int] = Field(
        description="""Recorded rating of the last answer.
        If thumbs are used then values are '1' for thumbs up
        and '0' for thumbs down."""
    )
    rating_comment: Optional[str] = Field(
        default=None, description="""Recorded comment on the last answer. Optional."""
    )
    question: Optional[str] = Field(
        default=None, description="""Last question. Optional."""
    )
    content_type: Optional[str] = Field(
        default=None, description="""Last content type. Optional."""
    )
    answer: Optional[str] = Field(
        default=None, description="""Last answer. Optional."""
    )


@app.post(
    "/feedback",
    status_code=202,
    tags=["Principle Endpoints"],
    dependencies=protected_endpoint_dependencies(),
)
async def record_rating(feedback: Feedback):
    """Records feedback on a previous answer.

    Args:
        feedback (Feedback): Recorded rating of the last answer.
            Required fields: rating (str or int).
            Optional fields: question, content_type, answer.

    Raises:
        HTTPException: 422 Validation error.

    Returns:
        HTTPResponse: 202 with empty body to indicate successfully added feedback.
    """
    logger.info(f"Recorded answer feedback: {feedback}")
    return ""
