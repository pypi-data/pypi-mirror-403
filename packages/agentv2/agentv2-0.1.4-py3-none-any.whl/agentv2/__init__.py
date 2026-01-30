"""AgentV2 - Production-Ready Python Agent Framework."""

__version__ = "0.1.4"

# Import main classes for convenience
from agentv2.src.agent import Agent
from agentv2.src.executor import Executor
from agentv2.src.planner import Planner
from agentv2.src.session_store import SessionStore, get_session_store

# Import schemas (using __init__ exports)
from agentv2.schemas import (
    AgentMemory,
    AgentState,
    CacheEntry,
    ConversationEntry,
    SessionMemory,
    Todo,
    TodoItemInput,
    TodoList,
    TodoListInput,
    normalize_task,
)

# Import utilities
from agentv2.utils.llm import LLM
from agentv2.utils.logger import get_logger
from agentv2.utils.Prompts import get_prompt
from agentv2.utils.validators import (
    BackendTodoValidator,
    DataTodoValidator,
    DomainTodoValidator,
    FrontendTodoValidator,
)

__all__ = [
    # Main classes
    "Agent",
    "Executor",
    "Planner",
    "SessionStore",
    "get_session_store",
    # Schemas
    "AgentMemory",
    "AgentState",
    "CacheEntry",
    "ConversationEntry",
    "SessionMemory",
    "Todo",
    "TodoItemInput",
    "TodoList",
    "TodoListInput",
    "normalize_task",
    # Utilities
    "LLM",
    "get_logger",
    "get_prompt",
    "BackendTodoValidator",
    "DataTodoValidator",
    "DomainTodoValidator",
    "FrontendTodoValidator",
]
