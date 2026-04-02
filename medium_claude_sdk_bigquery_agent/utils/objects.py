from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class AgentRequest(BaseModel):
    """
    Input request object for the chat endpoint
    """

    question: str = Field(..., description="The user question")
    session_id: str | None = Field(
        default=None,
        description="UUID for the session; generated server-side if not provided",
    )
    checkpoint_dir: str | None = Field(
        default=None, description="Whether to continue from the checkpoint directory"
    )

    @field_validator("question", mode="before")
    def validate_question(cls, v: str, info: ValidationInfo) -> str:
        """
        Validates that question is non-empty
        """
        if not v or v.strip() == "":
            raise ValueError(f"Field {info.field_name} cannot be empty or whitespace")
        return v


class AgentResponse(BaseModel):
    """
    Output response object for the chat endpoint
    """

    session_id: str
    result: str

    @field_validator("session_id", mode="before")
    def validate_valid_entries(cls, v: str, info: ValidationInfo) -> str:
        """
        Validates whether the inputs are valid
        """
        if not v or v.strip() == "":
            raise ValueError(
                f"Field {info.field_name} cannot be empty, whitespace or None"
            )
        return v


class ConversationMessage(BaseModel):
    """
    Claude Agent SDK messages object
    """

    type: str
    uuid: str
    session_id: str
    message: dict[str, Any]


class ConversationHistoryResponse(BaseModel):
    """
    Output response object for the get conversation history endpoint
    """

    session_id: str
    messages: list[ConversationMessage]
