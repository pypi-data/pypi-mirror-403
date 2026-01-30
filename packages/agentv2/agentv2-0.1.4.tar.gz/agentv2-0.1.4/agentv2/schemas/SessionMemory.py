"""
SessionMemory: Lightweight per-session memory for the Agent framework.

This is NOT for execution state. It is ONLY for:
- Exact-match caching (task -> reply)
- Minimal conversational continuity (last_reply snippet)
- User/session preferences (future)

This is NOT for:
- Todos
- AgentState
- Tool outputs
- Execution state
- Reasoning traces
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Task Normalization
# =============================================================================

def normalize_task(task: str) -> str:
    """
    Normalize a task string for cache lookup.
    
    Normalization:
    - Lowercase
    - Strip whitespace
    - Collapse multiple spaces to single space
    
    Args:
        task: Raw task string
        
    Returns:
        Normalized task string
    """
    return " ".join(task.lower().strip().split())


# =============================================================================
# Cache Entry Model
# =============================================================================

class CacheEntry(BaseModel):
    """Metadata for a cached task-reply pair."""
    
    reply: str = Field(description="The cached reply")
    created_at: str = Field(description="ISO timestamp when cached")
    
    @classmethod
    def create(cls, reply: str) -> "CacheEntry":
        """Create a new cache entry with current timestamp."""
        return cls(
            reply=reply,
            created_at=datetime.utcnow().isoformat()
        )


class ConversationEntry(BaseModel):
    """A single conversation turn (question and answer pair)."""
    
    question: str = Field(description="User's question or input")
    answer: str = Field(description="Agent's reply")
    created_at: str = Field(description="ISO timestamp when created")
    
    @classmethod
    def create(cls, question: str, answer: str) -> "ConversationEntry":
        """Create a new conversation entry with current timestamp."""
        return cls(
            question=question,
            answer=answer,
            created_at=datetime.utcnow().isoformat()
        )


# =============================================================================
# Session Memory Model
# =============================================================================

class SessionMemory(BaseModel):
    """
    Lightweight per-session memory for the Agent framework.
    
    Responsibilities:
    - Exact-match caching (task -> reply) to avoid redundant LLM calls
    - Minimal conversational continuity (last_reply snippet for prompts)
    - Session lifecycle tracking (last_accessed_at)
    
    This is NOT for execution state. See FORBIDDEN_KEYS for what cannot be stored.
    
    Thread Safety:
    - Single-threaded use only (Python GIL provides basic protection)
    - For multi-threaded use, add locks in SessionStore
    """
    
    session_id: str = Field(description="Unique session identifier")
    
    # Cache: exact-match task -> reply (with metadata)
    response_cache: Dict[str, CacheEntry] = Field(
        default_factory=dict,
        description="Mapping of normalized_task -> CacheEntry for exact-match caching",
    )
    
    # Context: minimal conversational continuity
    recent_context: Optional[str] = Field(
        default=None,
        description="Truncated snippet of the last reply (for minimal prompt context)",
    )
    
    # Conversation history: list of Q&A pairs
    conversation_history: List[ConversationEntry] = Field(
        default_factory=list,
        description="List of conversation entries (question-answer pairs) for this session",
    )
    
    # Lifecycle tracking
    last_accessed_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of last access (for TTL/pruning)",
    )
    
    # Configuration (excluded from serialization)
    max_cache_entries: int = Field(
        default=50,
        exclude=True,
        description="Maximum cached task-reply pairs (LRU eviction)",
    )
    
    max_context_length: int = Field(
        default=200,
        exclude=True,
        description="Max characters to store in recent_context",
    )
    
    max_conversation_history: int = Field(
        default=20,
        exclude=True,
        description="Maximum number of conversation entries to keep (FIFO eviction)",
    )
    
    is_locked: bool = Field(
        default=False,
        exclude=True,
        description="Read-only lock during execution (prevents mutations)",
    )
    
    # =====================================================================
    # Lifecycle Methods
    # =====================================================================
    
    def touch(self) -> None:
        """Update last_accessed_at timestamp."""
        self.last_accessed_at = datetime.utcnow().isoformat()
    
    def lock(self) -> None:
        """Lock session memory for read-only access during execution."""
        self.is_locked = True
    
    def unlock(self) -> None:
        """Unlock session memory after execution."""
        self.is_locked = False
    
    def _assert_not_locked(self) -> None:
        """Assert that session is not locked."""
        if self.is_locked:
            raise RuntimeError(
                "SessionMemory is read-only during execution. "
                "Mutations are not allowed while Agent is running."
            )
    
    # =====================================================================
    # Context Management
    # =====================================================================
    
    def set_recent_context(self, reply: str) -> None:
        """
        Store a truncated version of the reply for conversational continuity.
        
        Args:
            reply: The reply to store (will be truncated)
            
        Raises:
            RuntimeError: If session is locked
        """
        self._assert_not_locked()
        if reply:
            self.recent_context = reply[: self.max_context_length]
            if len(reply) > self.max_context_length:
                self.recent_context += "..."
        else:
            self.recent_context = None
    
    def add_conversation_entry(self, question: str, answer: str) -> None:
        """
        Add a conversation entry (question-answer pair) to the history.
        
        Args:
            question: User's question or input
            answer: Agent's reply
            
        Raises:
            RuntimeError: If session is locked
        """
        self._assert_not_locked()
        entry = ConversationEntry.create(question, answer)
        
        # FIFO eviction: if history is full, remove oldest entry
        if len(self.conversation_history) >= self.max_conversation_history:
            self.conversation_history.pop(0)
        
        self.conversation_history.append(entry)
    
    def get_conversation_history(self, max_entries: Optional[int] = None) -> List[ConversationEntry]:
        """
        Get conversation history, optionally limited to recent entries.
        
        Args:
            max_entries: Maximum number of recent entries to return (None for all)
            
        Returns:
            List of conversation entries (most recent last)
        """
        if max_entries is None:
            return self.conversation_history.copy()
        return self.conversation_history[-max_entries:] if max_entries > 0 else []
    
    # =====================================================================
    # Cache Management
    # =====================================================================
    
    def cache_reply(self, task: str, reply: str) -> None:
        """
        Cache a reply for a task with LRU eviction.
        
        Args:
            task: The task string (will be normalized)
            reply: The reply to cache
            
        Raises:
            RuntimeError: If session is locked
        """
        self._assert_not_locked()
        normalized = normalize_task(task)
        
        # LRU eviction: if cache is full and this is a new entry, evict oldest
        if normalized not in self.response_cache and len(self.response_cache) >= self.max_cache_entries:
            # Evict oldest entry (first in dict, which is insertion order in Python 3.7+)
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        # Store new entry
        self.response_cache[normalized] = CacheEntry.create(reply)
        
        # Update recent context
        self.set_recent_context(reply)
    
    def get_cached_reply(self, task: str) -> Optional[str]:
        """
        Get cached reply for a task if it exists.
        
        Args:
            task: The task string (will be normalized)
            
        Returns:
            Cached reply if found, None otherwise
        """
        normalized = normalize_task(task)
        entry = self.response_cache.get(normalized)
        if entry:
            self.touch()  # Update access time
            return entry.reply
        return None
    
    def has_cache(self, task: str) -> bool:
        """
        Check if a task is cached.
        
        Args:
            task: The task string (will be normalized)
            
        Returns:
            True if cached, False otherwise
        """
        normalized = normalize_task(task)
        return normalized in self.response_cache
    
    def clear_cache(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            Number of entries that were cleared
            
        Raises:
            RuntimeError: If session is locked
        """
        self._assert_not_locked()
        count = len(self.response_cache)
        self.response_cache.clear()
        self.recent_context = None
        return count
    
    def clear_conversation_history(self) -> int:
        """
        Clear all conversation history entries.
        
        Returns:
            Number of entries that were cleared
            
        Raises:
            RuntimeError: If session is locked
        """
        self._assert_not_locked()
        count = len(self.conversation_history)
        self.conversation_history.clear()
        return count
    
    # =====================================================================
    # Compatibility Properties (for backward compatibility)
    # =====================================================================
    
    @property
    def cache(self) -> Dict[str, str]:
        """
        Backward compatibility: return cache as Dict[str, str].
        
        Note: This is a read-only view. Use cache_reply() to modify.
        """
        return {k: v.reply for k, v in self.response_cache.items()}
    
    @property
    def last_reply(self) -> Optional[str]:
        """Backward compatibility: alias for recent_context."""
        return self.recent_context
    
    def set_last_reply(self, reply: str) -> None:
        """Backward compatibility: alias for set_recent_context."""
        self.set_recent_context(reply)
