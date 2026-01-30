from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from agentv2.schemas.AgentState import AgentState
from agentv2.schemas.TodoSchema import Todo


class AgentMemory(BaseModel):
    """
    Authoritative memory for the agent's execution state.

    Stores tool results, todos, execution history, and the final reply.
    """

    last_tool: Optional[str] = None
    last_result: Optional[str] = None

    todos: List[Todo] = Field(default_factory=list)
    current_todo: Optional[str] = None

    state_history: List[AgentState] = Field(default_factory=list)

    # Final response to return to the user after all todos complete
    final_reply: Optional[str] = Field(
        default=None,
        description="The final summarized response/answer to return to the user",
    )

    created_at: datetime = Field(default_factory=datetime.now)

    max_history: int = Field(default=10, exclude=True)
