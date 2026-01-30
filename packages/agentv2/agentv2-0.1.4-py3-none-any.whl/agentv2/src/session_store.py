"""
In-memory session store for the Agent framework.

Provides a lightweight registry of SessionMemory objects keyed by session_id.
Sessions persist only within the current Python process.

Thread Safety:
- Single-threaded use only (Python GIL provides basic protection for simple operations)
- For multi-threaded use, add locks around mutations
- Compound operations (check-then-act) are NOT thread-safe without locks
"""

from typing import Dict, Optional

from agentv2.schemas.SessionMemory import SessionMemory


class SessionStore:
    """
    In-memory registry of session memories.
    
    Thread Safety:
    - Single-threaded use only
    - Python dict operations are atomic for simple reads/writes (GIL)
    - Compound operations require external locking if multi-threaded
    
    Lifecycle:
    - Sessions are created on first access
    - Sessions persist until manually cleared or process exits
    - Use touch() to track access times for future TTL pruning
    """
    
    _instance: Optional["SessionStore"] = None
    
    def __init__(self):
        self._sessions: Dict[str, SessionMemory] = {}
    
    @classmethod
    def get_instance(cls) -> "SessionStore":
        """Get or create the singleton SessionStore instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get(self, session_id: str) -> SessionMemory:
        """
        Get or create a SessionMemory for the given session_id.
        
        Updates last_accessed_at timestamp on access.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            The SessionMemory for this session (created if not exists)
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id)
        session = self._sessions[session_id]
        session.touch()  # Update access time
        return session
    
    def has(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions
    
    def clear(self, session_id: str) -> bool:
        """
        Clear/delete a specific session.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if session existed and was deleted, False otherwise
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def clear_all(self) -> int:
        """
        Clear all sessions.
        
        Returns:
            Number of sessions that were cleared
        """
        count = len(self._sessions)
        self._sessions.clear()
        return count
    
    def prune_idle(self, max_age_seconds: int) -> int:
        """
        Prune sessions that haven't been accessed in max_age_seconds.
        
        Args:
            max_age_seconds: Maximum age in seconds before pruning
            
        Returns:
            Number of sessions pruned
        """
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        cutoff_iso = cutoff.isoformat()
        
        to_prune = [
            session_id
            for session_id, session in self._sessions.items()
            if session.last_accessed_at < cutoff_iso
        ]
        
        for session_id in to_prune:
            del self._sessions[session_id]
        
        return len(to_prune)
    
    @property
    def session_count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)


# Convenience function to get the global store
def get_session_store() -> SessionStore:
    """Get the global SessionStore instance."""
    return SessionStore.get_instance()
