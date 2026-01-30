import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from agentv2.schemas.TodoSchema import TodoItemInput

if TYPE_CHECKING:
    from agentv2.utils.llm import LLM


# ============================================================================
# CONFIGURATION
# ============================================================================

ACTION_VERB_PATTERN = re.compile(
    r"^(create|initialize|define|implement|configure|write|add|remove|update|set up|build|design|"
    r"search|retrieve|extract|format|return|provide|compose|summarize|present|answer|find|"
    r"gather|collect|organize|structure|display|show|present)\b",
    re.IGNORECASE,
)

FORBIDDEN_PHRASES_WORD_BOUNDARY = [
    # meta / vague
    "ensure",
    "verify",
    "double-check",
    "optimize",
    "finalize",
    "make sure",
    "handle",
    "research",
    "understand",
    "analyze",
    # testing / validation
    "test",
    "validate",
    "check",
    "confirm",
]

# These are intentionally substring checks to catch compound phrasing.
# Note: "and " is removed because it causes false positives with legitimate lists
# (e.g., "header, input field, and unordered list" is one action, not compound)
FORBIDDEN_PHRASES_SUBSTRING = [
    " or ",
    "including ",
    "as well as",
    ", and",
]


def _find_forbidden_phrase(text_lower: str) -> Optional[str]:
    """
    Return the first forbidden phrase found, or None.

    This avoids false positives like matching 'test' inside 'latest' by using
    simple letter-boundary checks for single/multi-word phrases.
    """
    for phrase in FORBIDDEN_PHRASES_WORD_BOUNDARY:
        pattern = rf"(?<![a-z]){re.escape(phrase)}(?![a-z])"
        if re.search(pattern, text_lower):
            return phrase
    for phrase in FORBIDDEN_PHRASES_SUBSTRING:
        if phrase in text_lower:
            return phrase
    return None


FORBIDDEN_TECH_KEYWORDS = [
    # frameworks / tools (planner must be agnostic)
    "fastapi",
    "django",
    "flask",
    "express",
    "postgres",
    "mysql",
    "mongodb",
    "jwt",
    "bcrypt",
    "redis",
    "docker",
    "kubernetes",
    "react",
    "vue",
    "angular",
    "node",
    "npm",
    "pip",
    "yarn",
]

# Limits
MAX_WORDS = 18
MIN_WORDS = 3
MIN_TODO_COUNT = 3
MAX_TODO_COUNT = 7
MAX_REWRITE_ATTEMPTS = 2

# Scoring
MIN_TODO_SCORE = 0.75


# ============================================================================
# DOMAIN VALIDATORS (Pluggable Architecture)
# ============================================================================


class DomainTodoValidator(ABC):
    """
    Abstract base class for domain-specific todo validation.
    Extend this to add domain-specific rules on top of base validation.
    """

    @abstractmethod
    def validate(self, todo: TodoItemInput) -> None:
        """
        Validate a todo against domain-specific rules.
        Raises ValueError if invalid.
        """
        pass


class BackendTodoValidator(DomainTodoValidator):
    """Domain validator for backend/API development tasks."""

    BACKEND_FORBIDDEN = [
        "frontend",
        "ui",
        "css",
        "styling",
        "button",
        "component",
        "render",
    ]

    def validate(self, todo: TodoItemInput) -> None:
        text_lower = todo.todo.lower()
        for keyword in self.BACKEND_FORBIDDEN:
            if keyword in text_lower:
                raise ValueError(
                    f"Backend todo should not reference frontend concept '{keyword}': '{todo.todo}'"
                )


class FrontendTodoValidator(DomainTodoValidator):
    """Domain validator for frontend/UI development tasks."""

    FRONTEND_FORBIDDEN = [
        "database",
        "sql",
        "migration",
        "schema",
        "server",
        "endpoint",
        "api route",
    ]

    def validate(self, todo: TodoItemInput) -> None:
        text_lower = todo.todo.lower()
        for keyword in self.FRONTEND_FORBIDDEN:
            if keyword in text_lower:
                raise ValueError(
                    f"Frontend todo should not reference backend concept '{keyword}': '{todo.todo}'"
                )


class DataTodoValidator(DomainTodoValidator):
    """Domain validator for data/ML tasks."""

    DATA_FORBIDDEN = [
        "deploy",
        "production",
        "user interface",
        "frontend",
        "api endpoint",
    ]

    def validate(self, todo: TodoItemInput) -> None:
        text_lower = todo.todo.lower()
        for keyword in self.DATA_FORBIDDEN:
            if keyword in text_lower:
                raise ValueError(
                    f"Data todo should not reference deployment/UI concept '{keyword}': '{todo.todo}'"
                )


# ============================================================================
# BASE VALIDATION
# ============================================================================


def validate_todo(todo: TodoItemInput) -> None:
    """
    Validate a single todo item against base rules.
    Raises ValueError if invalid.
    """
    text = todo.todo.strip()
    text_lower = text.lower()

    # 1. Must start with a strong action verb
    if not ACTION_VERB_PATTERN.search(text):
        raise ValueError(f"Todo must start with a clear action verb: '{text}'")

    # 2. Must not be empty or trivial
    if len(text.split()) < MIN_WORDS:
        raise ValueError(f"Todo is too short or vague: '{text}'")

    # 3. Must be bounded (not compound)
    if len(text.split()) > MAX_WORDS:
        raise ValueError(f"Todo is too long or compound: '{text}'")

    # 4. Must not contain forbidden phrases
    phrase = _find_forbidden_phrase(text_lower)
    if phrase:
        raise ValueError(f"Todo contains forbidden phrase '{phrase}': '{text}'")

    # 4b. Check for compound actions (two action verbs separated by "and")
    # This catches "Create file and run test" but allows "Create HTML with header, input, and list"
    words = text.split()
    if "and" in words:
        and_index = words.index("and")
        # Check if there's an action verb before and after "and" (compound action)
        before_and = " ".join(words[:and_index]).lower()
        after_and = " ".join(words[and_index + 1 :]).lower()
        if ACTION_VERB_PATTERN.search(before_and) and ACTION_VERB_PATTERN.search(
            after_and
        ):
            raise ValueError(
                f"Todo contains compound action (multiple verbs with 'and'): '{text}'"
            )

    # 5. Must not reference tools or technologies
    for keyword in FORBIDDEN_TECH_KEYWORDS:
        if keyword in text_lower:
            raise ValueError(
                f"Todo references specific technology '{keyword}': '{text}'"
            )

    # 6. Must be deterministic (no meta steps)
    if text_lower.startswith(("review ", "evaluate ", "assess ")):
        raise ValueError(f"Todo is a meta or review task: '{text}'")


def validate_todo_list(todos: List[TodoItemInput]) -> None:
    """
    Validate a list of todo items (base validation only).
    Raises ValueError if any todo is invalid or list size is wrong.
    """
    if not (MIN_TODO_COUNT <= len(todos) <= MAX_TODO_COUNT):
        raise ValueError(
            f"Todo list must contain {MIN_TODO_COUNT}–{MAX_TODO_COUNT} items, got {len(todos)}"
        )

    for index, todo in enumerate(todos):
        try:
            validate_todo(todo)
        except ValueError as e:
            raise ValueError(f"Todo #{index + 1} invalid: {e}") from e


# ============================================================================
# SCORING SYSTEM
# ============================================================================


def score_todo(todo: TodoItemInput) -> float:
    """
    Score a todo item between 0.0 and 1.0.

    Scoring dimensions (weighted):
    - Action verb:       0.30 (executability)
    - Atomicity:         0.25 (one action)
    - Bounded length:    0.15 (no compound steps)
    - No forbidden:      0.15 (determinism)
    - Tool-agnostic:     0.15 (planner safety)
    """
    score = 0.0
    text = todo.todo.strip()
    text_lower = text.lower()
    words = text.split()

    # 1. Action verb (0.30)
    if ACTION_VERB_PATTERN.search(text):
        score += 0.30

    # 2. Atomicity (0.25) - no compound indicators
    compound_indicators = [" and ", ", and", " including ", " or "]
    if not any(p in text_lower for p in compound_indicators):
        score += 0.25

    # 3. Bounded length (0.15)
    if MIN_WORDS <= len(words) <= MAX_WORDS:
        score += 0.15

    # 4. No forbidden phrases (0.15)
    if _find_forbidden_phrase(text_lower) is None:
        score += 0.15

    # 5. Tool / tech agnostic (0.15)
    if not any(k in text_lower for k in FORBIDDEN_TECH_KEYWORDS):
        score += 0.15

    return round(score, 2)


def score_todo_list(todos: List[TodoItemInput]) -> float:
    """
    Calculate average score for a list of todos.
    Returns 0.0 if list is empty.
    """
    if not todos:
        return 0.0
    return round(sum(score_todo(t) for t in todos) / len(todos), 2)


# ============================================================================
# AUTO-REWRITE
# ============================================================================


def rewrite_todo(llm: "LLM", todo_text: str, error: str) -> str:
    """
    Use LLM to rewrite an invalid todo into a valid one.
    Returns the rewritten todo text.
    """
    from agentv2.utils.Prompts import get_prompt

    prompt = get_prompt("TodoRewrite", todo=todo_text, error=error)
    response = llm.invoke(prompt)

    # Extract first line only, strip quotes and whitespace
    rewritten = response.strip().splitlines()[0].strip().strip('"').strip("'")
    return rewritten


# ============================================================================
# VALIDATION + REWRITE PIPELINES
# ============================================================================


def validate_and_rewrite_todos(
    llm: "LLM", todos: List[TodoItemInput]
) -> List[TodoItemInput]:
    """
    Validate todos and attempt to rewrite invalid ones (base validation only).
    Returns validated (possibly rewritten) todos.
    Raises ValueError if a todo cannot be repaired after MAX_REWRITE_ATTEMPTS.
    """
    # First check list size (cannot be fixed by rewriting)
    if not (MIN_TODO_COUNT <= len(todos) <= MAX_TODO_COUNT):
        raise ValueError(
            f"Todo list must contain {MIN_TODO_COUNT}–{MAX_TODO_COUNT} items, got {len(todos)}. "
            "Regenerate the entire plan."
        )

    validated: List[TodoItemInput] = []

    for index, todo in enumerate(todos):
        current = todo

        for attempt in range(MAX_REWRITE_ATTEMPTS + 1):
            try:
                validate_todo(current)
                validated.append(current)
                break
            except ValueError as e:
                if attempt == MAX_REWRITE_ATTEMPTS:
                    raise ValueError(
                        f"Todo #{index + 1} could not be repaired after {MAX_REWRITE_ATTEMPTS} attempts: "
                        f"'{todo.todo}'"
                    ) from e

                # Attempt rewrite
                rewritten_text = rewrite_todo(
                    llm=llm,
                    todo_text=current.todo,
                    error=str(e),
                )
                # Preserve original notes
                current = TodoItemInput(todo=rewritten_text, notes=todo.notes)

    return validated


def validate_and_rewrite_with_domain(
    llm: "LLM",
    todos: List[TodoItemInput],
    domain_validator: Optional[DomainTodoValidator] = None,
) -> List[TodoItemInput]:
    """
    Validate todos with optional domain-specific rules and auto-rewrite.

    Args:
        llm: LLM instance for rewriting
        todos: List of todos to validate
        domain_validator: Optional domain-specific validator

    Returns:
        List of validated (possibly rewritten) todos

    Raises:
        ValueError: If a todo cannot be repaired after MAX_REWRITE_ATTEMPTS
    """
    # First check list size (cannot be fixed by rewriting)
    if not (MIN_TODO_COUNT <= len(todos) <= MAX_TODO_COUNT):
        raise ValueError(
            f"Todo list must contain {MIN_TODO_COUNT}–{MAX_TODO_COUNT} items, got {len(todos)}. "
            "Regenerate the entire plan."
        )

    validated: List[TodoItemInput] = []

    for index, todo in enumerate(todos):
        current = todo

        for attempt in range(MAX_REWRITE_ATTEMPTS + 1):
            try:
                # Base validation
                validate_todo(current)

                # Domain-specific validation
                if domain_validator:
                    domain_validator.validate(current)

                validated.append(current)
                break

            except ValueError as e:
                if attempt == MAX_REWRITE_ATTEMPTS:
                    raise ValueError(
                        f"Todo #{index + 1} failed validation permanently: '{todo.todo}'"
                    ) from e

                # Attempt rewrite
                rewritten_text = rewrite_todo(
                    llm=llm,
                    todo_text=current.todo,
                    error=str(e),
                )
                # Preserve original notes
                current = TodoItemInput(todo=rewritten_text, notes=todo.notes)

    return validated


def validate_score_and_rewrite(
    llm: "LLM",
    todos: List[TodoItemInput],
    min_score: float = MIN_TODO_SCORE,
    domain_validator: Optional[DomainTodoValidator] = None,
) -> List[TodoItemInput]:
    """
    Full validation pipeline: validate + score + domain check + auto-rewrite.

    This is the recommended pipeline for production use.

    Flow for each todo:
    1. Base validation (hard rules)
    2. Domain validation (if provided)
    3. Quality scoring (must meet min_score threshold)
    4. Auto-rewrite on failure (bounded attempts)

    Args:
        llm: LLM instance for rewriting
        todos: List of todos to validate
        min_score: Minimum acceptable quality score (default: 0.75)
        domain_validator: Optional domain-specific validator

    Returns:
        List of validated, high-quality todos

    Raises:
        ValueError: If a todo cannot be repaired after MAX_REWRITE_ATTEMPTS
    """
    # First check list size (cannot be fixed by rewriting)
    if not (MIN_TODO_COUNT <= len(todos) <= MAX_TODO_COUNT):
        raise ValueError(
            f"Todo list must contain {MIN_TODO_COUNT}–{MAX_TODO_COUNT} items, got {len(todos)}. "
            "Regenerate the entire plan."
        )

    final_todos: List[TodoItemInput] = []

    for index, todo in enumerate(todos):
        current = todo

        for attempt in range(MAX_REWRITE_ATTEMPTS + 1):
            try:
                # 1. Hard validation (base rules)
                validate_todo(current)

                # 2. Domain-specific validation
                if domain_validator:
                    domain_validator.validate(current)

                # 3. Quality scoring
                score = score_todo(current)
                if score < min_score:
                    raise ValueError(
                        f"Todo quality score too low ({score} < {min_score})"
                    )

                final_todos.append(current)
                break

            except ValueError as e:
                if attempt == MAX_REWRITE_ATTEMPTS:
                    raise ValueError(
                        f"Todo #{index + 1} permanently rejected after {MAX_REWRITE_ATTEMPTS} rewrites: "
                        f"'{todo.todo}'"
                    ) from e

                # Attempt rewrite
                rewritten_text = rewrite_todo(
                    llm=llm,
                    todo_text=current.todo,
                    error=str(e),
                )
                # Preserve original notes
                current = TodoItemInput(todo=rewritten_text, notes=todo.notes)

    return final_todos
