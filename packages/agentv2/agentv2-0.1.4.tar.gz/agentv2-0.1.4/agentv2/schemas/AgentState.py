from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Represents a single step/action proposed by the LLM.

    The agent outputs this structure at each step to indicate
    what it's thinking and what action it wants to take.
    """

    thoughts: str = Field(min_length=5, description="Reasoning for this step")

    action: Literal["think", "tool", "complete_todo", "fail_todo", "none"] = Field(
        description="Proposed action for the next step"
    )

    tool_name: Optional[str] = Field(
        default=None, description="Name of tool to call (required if action='tool')"
    )
    tool_input: Optional[dict] = Field(
        default=None, description="Arguments for the tool (required if action='tool')"
    )

    reply: Optional[str] = Field(
        default=None,
        description="Response/answer to provide when completing a todo. Use this to capture the result or answer.",
    )
