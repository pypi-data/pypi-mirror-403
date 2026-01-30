from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# Schema for LLM response (LLM provides action text and context notes)
class TodoItemInput(BaseModel):
    todo: str
    notes: Optional[str] = (
        None  # Why we are doing this todo - provides context for execution
    )


class TodoListInput(BaseModel):
    todos: List[TodoItemInput] = Field(default_factory=list)


# Full schema with all fields (for internal use)
class Todo(BaseModel):
    id: str
    todo: str
    is_completed: bool = False
    is_in_progress: bool = False
    notes: Optional[str] = None  # Context/reasoning for this todo

    @classmethod
    def from_input(cls, input_data: TodoItemInput) -> "Todo":
        """Create Todo from TodoItemInput, generating UUID4 id and setting defaults"""
        return cls(
            id=str(uuid4()),
            todo=input_data.todo,
            is_completed=False,
            is_in_progress=False,
            notes=input_data.notes,
        )


class TodoList(BaseModel):
    todos: List[Todo] = Field(default_factory=list)

    @classmethod
    def from_input(cls, input_data: TodoListInput) -> "TodoList":
        """Create TodoList from TodoListInput, generating UUID4 ids for all todos"""
        return cls(todos=[Todo.from_input(todo) for todo in input_data.todos])
