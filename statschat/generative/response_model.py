from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import BaseModel, field_validator

class LlmResponse(BaseModel):
    answer_provided: bool = Field(
        description=(
            "True if enough information is provided in the context to answer "
            "the question, False otherwise."
        )
    )

    most_likely_answer: Optional[str] = Field(
        default=None,
        description=(
            "Answer to the question, quoting or only minimally rephrasing "
            "the provided text. Must be null if answer_provided=False."
        ),
    )

    highlighting1: List[str] = Field(
        default_factory=list,
        description=(
            "List of short exact subphrases from the first context document "
            "that are most relevant to the question."
        ),
    )

    highlighting2: List[str] = Field(
        default_factory=list,
        description=(
            "List of short exact subphrases from the second context document "
            "that are most relevant to the question."
        ),
    )

    highlighting3: List[str] = Field(
        default_factory=list,
        description=(
            "List of short exact subphrases from the third and any further "
            "context documents that are most relevant to the question."
        ),
    )

    reasoning: Optional[str] = Field(
        default=None,
        description=(
            "Step by step reasoning why an answer has been selected or could "
            "not be provided."
        ),
    )

    @field_validator("most_likely_answer")
    @classmethod
    def require_answer_when_provided(cls, v, info):
        if info.data.get("answer_provided") and not v:
            raise ValueError(
                "most_likely_answer must be provided when answer_provided is true"
            )
        return v
