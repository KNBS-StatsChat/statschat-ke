# %%
from pydantic import BaseModel, Field
from typing import Union, Optional

# %%
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import logging
import os
from datetime import datetime
from markupsafe import escape

from statschat import load_config
from statschat.api_common import (
    build_health_payload,
    configure_api_logging,
    configure_cors,
    configure_request_logging,
    protected_endpoint_dependencies,
)
from statschat.generative.cloud_llm import Inquirer, has_temporal_constraint
from statschat.embedding.latest_flag_helpers import get_latest_flag

# %%

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_api_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
configure_api_logging(logger, SESSION_NAME)

# %%
# Config file to load
CONFIG = load_config(name="main")
# %%

# initiate Statschat AI and start the app
SEARCH_CONFIG = dict(CONFIG.get("search", {}))
SEARCH_CONFIG["generative_model_name"] = str(
    SEARCH_CONFIG.get("generative_model_name_cloud")
    or SEARCH_CONFIG.get("generative_model_name")
    or "mistralai/mistral-small-3.1-24b-instruct:free"
)
# Keep cloud runtime model selection anchored to main.toml.
# The shared Inquirer still reads STATSCHAT_GENERATIVE_MODEL from the
# environment, so we mirror the configured cloud model here to avoid any
# stale shell/.env override taking precedence over project config.
os.environ["STATSCHAT_GENERATIVE_MODEL"] = SEARCH_CONFIG["generative_model_name"]
provider = SEARCH_CONFIG.get("provider", "openrouter")

inquirer = Inquirer(
    **CONFIG["db"],
    **SEARCH_CONFIG,
    logger=logger,
)

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
configure_request_logging(app, logger, api_mode="cloud")


@app.get("/", tags=["Principle Endpoints"])
async def about():
    """Access the API documentation in json format.

    Returns:
        Redirect to /openapi.json
    """
    response = RedirectResponse(url="/openapi.json")
    return response


@app.get(
    "/health",
    tags=["Principle Endpoints"],
)
async def health():
    """Return API liveness and non-secret runtime status."""

    return build_health_payload(
        api_mode="cloud",
        config=CONFIG,
        model_name=SEARCH_CONFIG.get("generative_model_name"),
        provider=str(provider),
        model_loaded=True,
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
    latest_weight = get_latest_flag({"q": question}, CONFIG["app"]["latest_max"])

    # Safeguard: when the question carries an explicit year/month/quarter,
    # force a search across the full corpus regardless of the requested
    # content_type. The latest-only FAISS store excludes historical reports
    # and would silently drop the ground-truth document for date-specific
    # queries.
    effective_latest_filter = content_type == "latest"
    if effective_latest_filter and has_temporal_constraint(question):
        logger.info(
            "Detected explicit temporal tokens in query; overriding "
            "latest_filter to False so historical reports remain searchable."
        )
        effective_latest_filter = False

    docs, answer, response = inquirer.make_query(
        question,
        latest_filter=effective_latest_filter,
        latest_weight=latest_weight,
    )
    results = {
        "question": question,
        "content_type": content_type,
        "answer": answer,
        "references": docs,
    }
    if debug:
        results["debug_response"] = response.__dict__
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
