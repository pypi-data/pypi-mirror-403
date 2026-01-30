import json
import re
from typing import Callable, Dict, Optional

from agentv2.schemas.AgentMemory import AgentMemory
from agentv2.schemas.SessionMemory import SessionMemory, normalize_task
from agentv2.schemas.TodoSchema import TodoList
from agentv2.src.executor import Executor
from agentv2.src.planner import Planner
from agentv2.src.session_store import SessionStore, get_session_store
from agentv2.utils.llm import LLM
from agentv2.utils.logger import get_logger
from agentv2.utils.Prompts import get_prompt
from agentv2.utils.validators import BackendTodoValidator, DomainTodoValidator

# Sentinel to distinguish "not provided" from "explicitly None"
_DEFAULT_DOMAIN_VALIDATOR = object()


# -----------------------------------------------------------------------------
# Session Facts Extraction Patterns (Deterministic - No LLM Tokens)
# -----------------------------------------------------------------------------

# Patterns to extract user name from common phrases
NAME_PATTERNS = [
    r"(?:i'?m|i am|my name is|call me|this is)\s+([A-Z][a-z]+)",  # "I'm Varun", "my name is Varun"
    r"(?:hi|hello|hey)[,!]?\s+(?:i'?m|i am)\s+([A-Z][a-z]+)",  # "Hi, I'm Varun"
]


class Agent:
    """
    High-level orchestrator with session-based memory.

    Responsibilities:
    - Own task lifecycle
    - Coordinate planner → validator → executor
    - Generate final reply after execution
    - Maintain session memory for caching and context
    - Never reason or execute directly
    """

    def __init__(
        self,
        model: str,
        system_prompt: str,
        session_id: str,
        api_base: Optional[str] = None,
        tools: Optional[Dict[str, Callable]] = None,
        session_store: Optional[SessionStore] = None,
        domain_validator: Optional[DomainTodoValidator] = _DEFAULT_DOMAIN_VALIDATOR,
        verbose: bool = True,
    ):
        self.verbose = verbose
        # Create a logger instance with verbose control
        self.logger = get_logger(verbose=verbose)
        
        self.logger.info(
            "agent_initializing",
            model=model,
            session_id=session_id,
            tools_count=len(tools or {}),
        )

        self.model = model
        self.system_prompt = system_prompt
        self.api_base = api_base
        self.session_id = session_id

        # Get or create session from store
        self._session_store = session_store or get_session_store()
        self._session: SessionMemory = self._session_store.get(session_id)

        self.llm = LLM(
            model=model,
            system_prompt=system_prompt,
            api_base=api_base,
        )

        self.planner = Planner(
            model=model,
            system_prompt=system_prompt,
            api_base=api_base,
            verbose=self.verbose,
        )
        self.tools = tools or {}
        # Store domain validator (can be None to disable domain validation)
        # Default to BackendTodoValidator only if not explicitly provided
        if domain_validator is _DEFAULT_DOMAIN_VALIDATOR:
            # Not provided, use default
            self.domain_validator = BackendTodoValidator()
        else:
            # Explicitly provided (could be None or a validator)
            self.domain_validator = domain_validator

        # Lightweight session facts (persists across chat turns)
        # This is stored in session memory for future use
        self.session_facts: Dict[str, str] = {}

        self.logger.success("agent_initialized", session_id=session_id)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def chat(self, user_text: str) -> str:
        """
        Chat-oriented API that maintains session facts across turns.

        This is the recommended entry point for conversational use cases.
        It extracts facts (like user_name) from the user's message,
        injects them as context, runs the agent, and returns the reply.

        Args:
            user_text: The user's message

        Returns:
            The agent's reply as a string
        """
        # 1. Extract facts from user message (deterministic, no LLM)
        self._update_session_facts(user_text)

        # 2. Build task with session facts prefix (minimal tokens)
        if self.session_facts:
            facts_header = f"SessionFacts: {json.dumps(self.session_facts)}\n\n"
        else:
            facts_header = ""

        task = f"""{facts_header}User Message: {user_text}

Instructions:
1. If the question requires current information, facts, or data you're unsure about, use the web_search tool.
2. If the user asks about something in SessionFacts (like their name), use that information.
3. Provide a clear, helpful answer.
4. If the question is simple and doesn't require web search, answer directly.
5. Always be helpful, accurate, and concise."""

        # 3. Run the agent
        result = self.run(task)

        # 4. Get the final reply (or fallback)
        final_reply = result.final_reply or self._build_fallback_reply(result)
        
        # 5. Store conversation history (user question + agent reply)
        if final_reply:
            self._session.add_conversation_entry(user_text, final_reply)
        
        # 6. Return the final reply
        return final_reply

    def run(self, task: str) -> AgentMemory:
        """
        Execute a task end-to-end with session-based caching.

        Flow:
        Task
          → Normalize + Cache Check
          → (if cache hit) Return cached reply
          → (if cache miss) Add session header
          → Planner → Executor → Summarization
          → Cache reply
          → Return
        """
        # 1. Check cache - if exact match, return immediately (no LLM calls)
        # Note: get_cached_reply normalizes the task internally
        cached_reply = self._session.get_cached_reply(task)
        if cached_reply is not None:
            self.logger.divider("CACHE HIT", style="green")
            normalized_task_str = normalize_task(task)
            self.logger.success(
                "agent_cache_hit",
                session_id=self.session_id,
                task_preview=(
                    normalized_task_str[:50] + "..."
                    if len(normalized_task_str) > 50
                    else normalized_task_str
                ),
            )

            # Return a minimal AgentMemory with the cached reply
            memory = AgentMemory()
            memory.final_reply = cached_reply
            return memory

        # 3. Cache miss - proceed with full execution
        self.logger.divider("AGENT RUN STARTED")
        self.logger.info(
            "agent_run_started",
            session_id=self.session_id,
            task_preview=task[:80] + "..." if len(task) > 80 else task,
        )

        # 4. Build session context for prompts
        session_context = self._build_session_context()

        # 5. Build task with minimal session header
        task_with_context = self._add_session_header(task)

        # 6. Generate todos (planning) with session context
        self.logger.divider("PLANNING PHASE", style="cyan")
        self.logger.info("planning_phase_started")
        todo_list = self._plan(task_with_context, session_context=session_context)
        self.logger.success("planning_phase_completed", todos_count=len(todo_list.todos))

        # 7. Initialize memory with todos
        self.logger.divider("MEMORY INITIALIZATION", style="cyan")
        memory = AgentMemory(todos=todo_list.todos)
        self.logger.info("memory_initialized", todos_count=len(memory.todos))

        # 8. Create executor with memory and session context
        executor = Executor(
            llm=self.llm,
            memory=memory,
            tools=self.tools,
            session_context=session_context,
            verbose=self.verbose,
        )

        # 9. Execute
        self.logger.divider("EXECUTION PHASE", style="cyan")
        self.logger.info("execution_phase_started")
        result = executor.run()
        self.logger.success(
            "execution_phase_completed", total_steps=len(result.state_history)
        )

        # 10. Generate final reply
        self.logger.divider("SUMMARIZATION PHASE", style="cyan")
        self.logger.info("summarization_phase_started")
        result.final_reply = self._summarize(task, result)
        self.logger.success("summarization_phase_completed")

        # 11. Cache the reply for future identical requests
        if result.final_reply:
            self._session.cache_reply(task, result.final_reply)
            self.logger.debug(
                "agent_reply_cached",
                session_id=self.session_id,
                cache_size=len(self._session.cache),
            )

        self.logger.divider("AGENT RUN COMPLETED", style="green")
        
        # Always show final output, even when verbose=False
        if not self.verbose and result.final_reply:
            from rich.console import Console
            from rich.panel import Panel
            from rich import box
            console = Console()
            console.print()
            console.print(Panel(result.final_reply, title="Result", border_style="green", box=box.ROUNDED))
            console.print()

        return result

    def clear_cache(self) -> int:
        """
        Clear the session cache.

        Returns:
            Number of cached entries that were cleared
        """
        count = len(self._session.cache)
        self._session.cache.clear()
        self._session.last_reply = None
        self.logger.info(
            "agent_cache_cleared", session_id=self.session_id, entries_cleared=count
        )
        return count

    @property
    def cache_size(self) -> int:
        """Number of cached task->reply pairs in this session."""
        return len(self._session.cache)

    # ---------------------------------------------------------
    # Internal steps
    # ---------------------------------------------------------

    def _normalize_task(self, task: str) -> str:
        """
        Normalize a task string for cache lookup.

        Strips whitespace and collapses multiple spaces.
        """
        return " ".join(task.strip().split())

    def _add_session_header(self, task: str) -> str:
        """
        Add a minimal session context header to the task.

        This is generic (not chat-specific) and adds minimal tokens.
        """
        header_parts = []

        # Add session ID (useful for debugging/context)
        header_parts.append(f"SessionId: {self.session_id}")

        # Add last reply snippet if available (for continuity)
        if self._session.last_reply:
            header_parts.append(f"LastReply: {self._session.last_reply}")

        if header_parts:
            header = "\n".join(header_parts)
            return f"[Session Context]\n{header}\n\n{task}"

        return task

    def _build_session_context(self) -> str:
        """
        Build a formatted session context string for prompts.

        Includes:
        - Session ID
        - Session facts (e.g., user_name)
        - Conversation history (previous Q&A pairs)
        - Last reply snippet (for continuity)
        - Cache information (number of cached items)

        Returns:
            Formatted session context string
        """
        context_parts = []

        # Session identification
        context_parts.append(f"Session ID: {self.session_id}")

        # Session facts (e.g., user_name from previous interactions)
        if self.session_facts:
            facts_str = ", ".join(f"{k}={v}" for k, v in self.session_facts.items())
            context_parts.append(f"Known Facts: {facts_str}")

        # Conversation history (previous questions and answers)
        conversation_history = self._session.get_conversation_history()
        if conversation_history:
            history_lines = []
            for i, entry in enumerate(conversation_history, 1):
                history_lines.append(f"Q{i}: {entry.question}")
                history_lines.append(f"A{i}: {entry.answer}")
            context_parts.append("Previous Conversation:")
            context_parts.append("\n".join(history_lines))

        # Last reply for continuity (backward compatibility)
        if self._session.last_reply:
            context_parts.append(f"Last Response: {self._session.last_reply}")

        # Cache size (for awareness)
        if self._session.cache:
            context_parts.append(f"Cached Responses: {len(self._session.cache)} items")

        return (
            "\n".join(context_parts)
            if context_parts
            else "No session context available."
        )

    def _update_session_facts(self, user_text: str) -> None:
        """
        Extract facts from user message using regex patterns.

        This is deterministic (no LLM tokens) and only extracts
        well-known patterns like name introductions.

        Args:
            user_text: The user's message to scan for facts
        """
        # Try to extract user name
        for pattern in NAME_PATTERNS:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Capitalize first letter for consistency
                name = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
                self.session_facts["user_name"] = name
                self.logger.debug("session_fact_extracted", fact="user_name", value=name)
                break

    def _plan(self, task: str, session_context: str = "") -> TodoList:
        """
        Planning step (LLM used once).
        Returns validated TodoList.
        """
        return self.planner._generate_todos(
            task=task,
            auto_rewrite=True,
            domain_validator=self.domain_validator,
            use_scoring=True,
            session_context=session_context,
        )

    def _summarize(self, task: str, memory: AgentMemory) -> str:
        """
        Generate a final user-facing reply based on execution results.

        This is called after all todos have been processed (completed or failed).
        """
        # Build todos summary (brief, for context)
        todos_summary_lines = []
        for i, todo in enumerate(memory.todos, 1):
            if todo.is_completed:
                status = "Done"
            elif todo.is_in_progress:
                status = "In Progress"
            else:
                status = "Failed"
            todos_summary_lines.append(f"{i}. [{status}] {todo.todo}")
        todos_summary = (
            "\n".join(todos_summary_lines) if todos_summary_lines else "No todos"
        )

        # Collect the most relevant result data
        # Priority: replies from state history > last_result > todo notes
        relevant_data_parts = []

        # Get replies from completed states
        replies = [s.reply for s in memory.state_history if s.reply]
        if replies:
            relevant_data_parts.append("Replies:\n" + "\n".join(replies[-3:]))

        # Add last tool result if available
        if memory.last_result:
            result_preview = (
                memory.last_result[:500] + "..."
                if len(memory.last_result) > 500
                else memory.last_result
            )
            relevant_data_parts.append(f"Tool Result:\n{result_preview}")

        # Add notes from completed todos
        completed_notes = [t.notes for t in memory.todos if t.is_completed and t.notes]
        if completed_notes and not replies:  # Only if we don't have replies
            relevant_data_parts.append("Notes:\n" + "\n".join(completed_notes[-2:]))

        last_result = (
            "\n\n".join(relevant_data_parts)
            if relevant_data_parts
            else "Task completed successfully."
        )

        # Build prompt using external template
        prompt = get_prompt(
            "FinalReply",
            task=task,
            todos_summary=todos_summary,
            last_result=last_result,
        )

        # Create a simple LLM instance for summarization (no tools needed)
        # Explicitly instruct the model not to use tools
        summary_llm = LLM(
            model=self.model,
            system_prompt="""You are a helpful, friendly assistant. Generate natural, conversational responses.
IMPORTANT: You must NOT use any tools or function calls. Only provide a direct text response.""",
            api_base=self.api_base,
        )

        try:
            final_reply = summary_llm.invoke(prompt)
            self.logger.info(
                "final_reply_generated",
                reply_preview=(
                    final_reply[:100] + "..." if len(final_reply) > 100 else final_reply
                ),
            )
            return final_reply
        except Exception as e:
            self.logger.error("final_reply_failed", exc=e)
            # Fallback: construct a basic reply from the last result
            fallback = self._build_fallback_reply(memory)
            return fallback

    def _build_fallback_reply(self, memory: AgentMemory) -> str:
        """
        Build a fallback reply if summarization fails.
        Uses replies from completed todos or the last result.
        """
        # Collect replies from state history
        replies = [s.reply for s in memory.state_history if s.reply]

        if replies:
            return "\n\n".join(replies[-3:])  # Last 3 replies

        # Check for completed todos with notes
        completed_notes = [t.notes for t in memory.todos if t.is_completed and t.notes]
        if completed_notes:
            return completed_notes[-1]

        # Fall back to last result
        if memory.last_result:
            return memory.last_result

        # Ultimate fallback - count failed todos (not completed and not in progress)
        failed_count = sum(
            1 for t in memory.todos if not t.is_completed and not t.is_in_progress
        )
        if failed_count > 0:
            return f"Task execution encountered {failed_count} failure(s). Please check the logs for details."

        return "Task completed."
        