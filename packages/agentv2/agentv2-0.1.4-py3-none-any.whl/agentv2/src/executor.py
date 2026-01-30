"""
Executor: Deterministic execution of validated todos produced by a planner.

Architectural Invariants:
- Planner decides todos, Executor NEVER does
- LLM can ONLY propose actions via AgentState
- Executor enforces all invariants
- No silent failures
- No unbounded loops
- Deterministic execution
- Tools are sandboxed and validated
- AgentState is NEVER authoritative — memory is
"""

import json
from typing import Callable, Dict, List

from agentv2.schemas.AgentMemory import AgentMemory
from agentv2.schemas.AgentState import AgentState
from agentv2.schemas.TodoSchema import Todo
from agentv2.utils.llm import LLM
from agentv2.utils.logger import get_logger
from agentv2.utils.Prompts import get_prompt


MAX_STEPS_PER_TODO: int = 25
RECENT_HISTORY_SIZE: int = 5

ALLOWED_ACTIONS = frozenset({"think", "tool", "complete_todo", "fail_todo", "none"})


class Executor:
    """
    Deterministic executor for validated todo lists.

    Responsibilities:
    1. Iterate through todos until all completed or failed
    2. Execute exactly ONE todo at a time
    3. For each todo: ask LLM for AgentState, validate, apply deterministically
    4. Enforce MAX_STEPS_PER_TODO bound
    5. Fail todo if no progress is made
    6. Never allow LLM to choose different todo, mutate memory, mark implicit completion
    """

    def __init__(
        self,
        llm: LLM,
        memory: AgentMemory,
        tools: Dict[str, Callable],
        session_context: str = "",
        verbose: bool = True,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._tools = tools
        self._tool_names = frozenset(tools.keys())
        self._session_context = session_context
        self._verbose = verbose
        self.logger = get_logger(verbose=verbose)

    def run(self) -> AgentMemory:
        """
        Execute all todos in memory sequentially.

        Returns:
            AgentMemory with updated state after execution

        Raises:
            RuntimeError: On unrecoverable execution errors
        """
        pending_todos = self._get_pending_todos()

        if not pending_todos:
            self.logger.info("executor_no_pending_todos")
            return self._memory

        self.logger.divider("EXECUTOR RUN STARTED")
        self.logger.info("executor_run_started", pending_todos_count=len(pending_todos))

        for i, todo in enumerate(pending_todos, 1):
            self.logger.divider(f"TODO {i}/{len(pending_todos)}")
            self.logger.info(
                "executor_todo_started",
                todo_id=todo.id,
                todo_text=todo.todo,
                todo_number=f"{i}/{len(pending_todos)}",
            )
            try:
                self._execute_single_todo(todo)
            except Exception as e:
                self.self.logger.error("executor_todo_failed", todo_id=todo.id, exc=e)
                raise

        self.logger.divider("EXECUTOR RUN COMPLETED")
        self.logger.success(
            "executor_run_completed",
            total_todos=len(pending_todos),
            total_steps=len(self._memory.state_history),
        )
        return self._memory

    def _get_pending_todos(self) -> List[Todo]:
        """Return todos that are neither completed nor failed."""
        return [todo for todo in self._memory.todos if not todo.is_completed]

    def _execute_single_todo(self, todo: Todo) -> None:
        """
        Execute a single todo with bounded steps.

        Args:
            todo: The todo to execute

        Raises:
            RuntimeError: On validation or execution errors
        """
        self._set_current_todo(todo.id)
        todo.is_in_progress = True

        steps_taken = 0
        consecutive_noops = 0
        max_consecutive_noops = 3

        while steps_taken < MAX_STEPS_PER_TODO:
            steps_taken += 1

            try:
                state = self._get_agent_state(todo)
                self._append_state(state)

                action = state.action

                if action == "complete_todo":
                    self.logger.divider("TODO COMPLETED", style="green")
                    # Use reply if provided, otherwise fall back to thoughts
                    completion_notes = state.reply if state.reply else state.thoughts
                    self.logger.success(
                        "executor_todo_completed",
                        todo_id=todo.id,
                        steps=steps_taken,
                        reply=state.reply[:100] if state.reply else None,
                        notes=completion_notes[:100] if completion_notes else "",
                    )
                    self._complete_current_todo(completion_notes)
                    return

                if action == "fail_todo":
                    self.logger.divider("TODO FAILED", style="yellow")
                    self.logger.warning(
                        "executor_todo_failed",
                        todo_id=todo.id,
                        steps=steps_taken,
                        reason=state.thoughts[:100] if state.thoughts else "",
                    )
                    self._fail_current_todo(state.thoughts)
                    return

                if action == "none":
                    consecutive_noops += 1
                    if consecutive_noops >= max_consecutive_noops:
                        reason = f"No progress: {consecutive_noops} consecutive noops"
                        self.logger.divider("TODO FAILED - NO PROGRESS", style="yellow")
                        self.logger.warning(
                            "executor_todo_failed_no_progress",
                            todo_id=todo.id,
                            consecutive_noops=consecutive_noops,
                        )
                        self._fail_current_todo(reason)
                        return
                    continue

                consecutive_noops = 0

                if action == "think":
                    self.logger.debug(
                        "executor_action_think",
                        step=steps_taken,
                        thought=state.thoughts[:50],
                    )
                    continue

                if action == "tool":
                    self._apply_tool_action(state)
                    continue

                raise RuntimeError(f"Unknown action: {action}")
            except Exception as e:
                self.logger.error(
                    "executor_step_failed", todo_id=todo.id, step=steps_taken, exc=e
                )
                raise

        reason = f"Step limit exceeded: {MAX_STEPS_PER_TODO} steps without completion"
        self.logger.divider("TODO FAILED - STEP LIMIT", style="yellow")
        self.logger.warning(
            "executor_todo_failed_step_limit",
            todo_id=todo.id,
            max_steps=MAX_STEPS_PER_TODO,
        )
        self._fail_current_todo(reason)

    def _get_agent_state(self, todo: Todo) -> AgentState:
        """
        Get validated AgentState proposal from LLM.

        Args:
            todo: Current todo being executed

        Returns:
            Validated AgentState

        Raises:
            RuntimeError: If LLM response fails validation
        """
        prompt = self._build_execution_prompt(todo)

        try:
            raw_response = self._llm.invoke(prompt)
            state = AgentState.model_validate_json(raw_response, strict=True)
        except Exception as e:
            self.logger.error("executor_llm_response_invalid", todo_id=todo.id, exc=e)
            raise RuntimeError(f"Invalid AgentState from LLM: {e}") from e

        try:
            self._validate_state(state)
        except Exception as e:
            self.logger.error(
                "executor_state_validation_failed",
                todo_id=todo.id,
                action=state.action,
                exc=e,
            )
            raise

        return state

    def _validate_state(self, state: AgentState) -> None:
        """
        Enforce invariants on the proposed state.

        Args:
            state: The AgentState to validate

        Raises:
            RuntimeError: If state violates any invariant
        """
        if state.action not in ALLOWED_ACTIONS:
            raise RuntimeError(f"Unknown action: {state.action}")

        if state.action == "tool":
            if not state.tool_name:
                raise RuntimeError("Tool action requires tool_name")

            if state.tool_name not in self._tool_names:
                raise RuntimeError(
                    f"Unknown tool: {state.tool_name}. "
                    f"Available: {sorted(self._tool_names)}"
                )

            if state.tool_input is not None and not isinstance(state.tool_input, dict):
                raise RuntimeError(
                    f"Tool input must be a dict, got: {type(state.tool_input).__name__}"
                )

    def _apply_tool_action(self, state: AgentState) -> None:
        """
        Execute a tool action and store result in memory.

        Args:
            state: AgentState with tool action

        Raises:
            RuntimeError: On tool execution failure
        """
        tool_name = state.tool_name
        tool_input = state.tool_input or {}

        self.logger.divider(f"TOOL CALL: {tool_name.upper()}", style="cyan")
        self.logger.info("executor_tool_calling", tool_name=tool_name, tool_input=tool_input)
        result = self._execute_tool(tool_name, tool_input)
        self.logger.success(
            "executor_tool_completed", tool_name=tool_name, result=str(result)[:100]
        )

        self._memory.last_tool = tool_name
        self._memory.last_result = result

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a tool with validated arguments.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Arguments to pass to the tool

        Returns:
            String result from tool execution

        Raises:
            RuntimeError: If tool doesn't exist or execution fails
        """
        if tool_name not in self._tools:
            self.logger.error(
                "executor_tool_not_found",
                tool_name=tool_name,
                available_tools=list(self._tool_names),
            )
            raise RuntimeError(f"Tool not found: {tool_name}")

        tool_fn = self._tools[tool_name]

        try:
            result = tool_fn(**tool_input)
        except TypeError as e:
            self.logger.error(
                "executor_tool_invalid_args",
                tool_name=tool_name,
                tool_input=tool_input,
                exc=e,
            )
            raise RuntimeError(f"Invalid arguments for tool '{tool_name}': {e}") from e
        except Exception as e:
            self.logger.error("executor_tool_execution_failed", tool_name=tool_name, exc=e)
            raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}") from e

        if result is None:
            return ""

        return str(result)

    def _build_execution_prompt(self, todo: Todo) -> str:
        """
        Build the execution prompt for the LLM using external template.

        Args:
            todo: Current todo being executed

        Returns:
            Formatted prompt string
        """
        return get_prompt(
            "Agent",
            task=self._format_task_list(),
            current_todo=self._format_current_todo(todo),
            recent_history=self._format_recent_history(),
            available_tools=self._format_tools(),
            session_context=(
                self._session_context
                if self._session_context
                else "No session context available."
            ),
        )

    def _format_task_list(self) -> str:
        """Format the complete todo list for the prompt."""
        lines = []

        for i, todo in enumerate(self._memory.todos, 1):
            status = "✓" if todo.is_completed else "→" if todo.is_in_progress else "○"
            lines.append(f"{i}. [{status}] {todo.todo}")
            if todo.notes:
                lines.append(f"   Notes: {todo.notes}")

        return "\n".join(lines) if lines else "No todos."

    def _format_current_todo(self, todo: Todo) -> str:
        """Format the current todo details for the prompt."""
        lines = [
            f"ID: {todo.id}",
            f"Task: {todo.todo}",
        ]

        if todo.notes:
            lines.append(f"Notes: {todo.notes}")

        if self._memory.last_tool:
            lines.extend(
                [
                    "",
                    f"Last Tool: {self._memory.last_tool}",
                    f"Last Result: {self._memory.last_result or '(empty)'}",
                ]
            )

        return "\n".join(lines)

    def _format_recent_history(self) -> str:
        """Format recent execution history for the prompt."""
        recent_states = self._memory.state_history[-RECENT_HISTORY_SIZE:]

        if not recent_states:
            return "No previous actions."

        lines = []
        for i, state in enumerate(recent_states, 1):
            lines.append(f"Step {i}:")
            lines.append(f"  Thought: {state.thoughts}")
            lines.append(f"  Action: {state.action}")

            if state.action == "tool" and state.tool_name:
                lines.append(f"  Tool: {state.tool_name}")
                if state.tool_input:
                    lines.append(f"  Input: {json.dumps(state.tool_input)}")
                # Include tool result if available (from memory.last_result for the most recent)
                if (
                    i == len(recent_states)
                    and self._memory.last_tool == state.tool_name
                ):
                    if self._memory.last_result:
                        lines.append(f"  Result: {self._memory.last_result}")

            lines.append("")

        return "\n".join(lines)

    def _format_tools(self) -> str:
        """Format available tools for the prompt."""
        if not self._tools:
            return "No tools available."

        lines = []
        for name, fn in self._tools.items():
            doc = fn.__doc__ or "No description"
            doc_first_line = doc.strip().split("\n")[0]
            lines.append(f"- {name}: {doc_first_line}")

        return "\n".join(lines)

    def _set_current_todo(self, todo_id: str) -> None:
        """
        Set the current todo in memory.

        Args:
            todo_id: ID of the todo to set as current
        """
        self._memory.current_todo = todo_id

    def _complete_current_todo(self, notes: str) -> None:
        """
        Mark the current todo as completed.

        Args:
            notes: Completion notes
        """
        for todo in self._memory.todos:
            if todo.id == self._memory.current_todo:
                todo.is_completed = True
                todo.is_in_progress = False
                if notes:
                    todo.notes = notes
                break

        self._memory.current_todo = None

    def _fail_current_todo(self, reason: str) -> None:
        """
        Mark the current todo as failed.

        Args:
            reason: Reason for failure
        """
        for todo in self._memory.todos:
            if todo.id == self._memory.current_todo:
                todo.is_completed = True
                todo.is_in_progress = False
                todo.notes = f"FAILED: {reason}"
                break

        self._memory.current_todo = None

    def _append_state(self, state: AgentState) -> None:
        """
        Append state to history with bounded size.

        Args:
            state: AgentState to append
        """
        self._memory.state_history.append(state)

        max_history = self._memory.max_history
        if len(self._memory.state_history) > max_history:
            self._memory.state_history = self._memory.state_history[-max_history:]
