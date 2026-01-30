from typing import Optional

from agentv2.schemas.TodoSchema import TodoList, TodoListInput
from agentv2.utils.llm import LLM
from agentv2.utils.logger import get_logger
from agentv2.utils.Prompts import get_prompt
from agentv2.utils.validators import (MIN_TODO_SCORE, DomainTodoValidator,
                              score_todo_list, validate_and_rewrite_todos,
                              validate_and_rewrite_with_domain,
                              validate_score_and_rewrite, validate_todo_list)


class Planner(LLM):
    """
    Planner generates validated, agent-safe todo lists from user tasks.

    Flow:
    1. Generate todos from task using LLM
    2. Validate todos against strict rules
    3. Score todos for quality
    4. Auto-rewrite invalid/low-quality todos (bounded retries)
    5. Return validated TodoList with generated UUIDs

    Guarantees:
    - Invalid todos never reach executor
    - Low-quality todos are auto-repaired
    - Rewrite attempts are bounded
    - Domain rules remain enforced
    - Planner quality is measurable
    """
    
    def __init__(self, model: str, system_prompt: str, api_base: Optional[str] = None, verbose: bool = True):
        super().__init__(model=model, system_prompt=system_prompt, api_base=api_base)
        self.verbose = verbose
        self.logger = get_logger(verbose=verbose)

    def _generate_todos(
        self,
        task: str,
        auto_rewrite: bool = True,
        domain_validator: Optional[DomainTodoValidator] = None,
        min_score: float = MIN_TODO_SCORE,
        use_scoring: bool = True,
        session_context: str = "",
    ) -> TodoList:
        """
        Generate a validated todo list from a task description.

        Args:
            task: The user's task description
            auto_rewrite: If True, attempt to rewrite invalid todos (default: True)
            domain_validator: Optional domain-specific validator (e.g., BackendTodoValidator)
            min_score: Minimum quality score threshold (default: 0.75)
            use_scoring: If True, enforce quality scoring (default: True)
            session_context: Optional session context for the planner

        Returns:
            TodoList with validated todos and generated UUIDs

        Raises:
            ValueError: If todos cannot be validated/repaired
        """
        self.logger.info(
            "planner_generating_todos",
            task_preview=task[:80] + "..." if len(task) > 80 else task,
        )
        prompt = get_prompt(
            "Todo",
            task=task,
            session_context=(
                session_context if session_context else "No session context available."
            ),
        )

        # Get LLM response as TodoListInput (without ids)
        input_response = self.invoke(prompt, TodoListInput)
        self.logger.debug(
            "planner_llm_response_received", todos_count=len(input_response.todos)
        )

        if auto_rewrite:
            if use_scoring:
                # Full pipeline: validate + score + domain + rewrite
                self.logger.info("planner_validating_with_scoring", min_score=min_score)
                validated_todos = validate_score_and_rewrite(
                    llm=self,
                    todos=input_response.todos,
                    min_score=min_score,
                    domain_validator=domain_validator,
                )
            elif domain_validator:
                # Validate with domain rules + rewrite (no scoring)
                self.logger.info("planner_validating_with_domain")
                validated_todos = validate_and_rewrite_with_domain(
                    llm=self,
                    todos=input_response.todos,
                    domain_validator=domain_validator,
                )
            else:
                # Base validation + rewrite only
                self.logger.info("planner_validating_base")
                validated_todos = validate_and_rewrite_todos(self, input_response.todos)

            input_response = TodoListInput(todos=validated_todos)
        else:
            # Strict validation only - no rewriting
            self.logger.info("planner_validating_strict")
            validate_todo_list(input_response.todos)

        # Convert to TodoList with generated UUID4 ids
        todo_list = TodoList.from_input(input_response)

        # Log quality score for observability
        avg_score = score_todo_list(input_response.todos)
        self.logger.success(
            "planner_todos_generated",
            todos_count=len(todo_list.todos),
            avg_score=avg_score,
        )

        return todo_list

    # Legacy method name for backwards compatibility
    def _genrate_todos(self, task: str) -> TodoList:
        """Deprecated: Use _generate_todos instead."""
        return self._generate_todos(task, auto_rewrite=True, use_scoring=True)
