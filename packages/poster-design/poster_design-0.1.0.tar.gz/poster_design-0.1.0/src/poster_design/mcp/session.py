"""
Session management for MCP server.

This module provides session management for multi-user scenarios
when using the MCP integration.
"""

import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class Session:
    """Represents a user session.

    Attributes:
        session_id: Unique session identifier
        canvases: Dictionary of canvases in this session
        created_at: Session creation timestamp
        last_accessed: Last activity timestamp
        timeout: Session timeout in seconds
    """

    session_id: str
    timeout: float = 300.0  # 5 minutes default
    canvases: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def add_canvas(self, canvas_id: str, canvas) -> None:
        """Add a canvas to the session.

        Args:
            canvas_id: Canvas identifier
            canvas: Canvas object
        """
        self.canvases[canvas_id] = canvas
        self.update_accessed()

    def get_canvas(self, canvas_id: str):
        """Get a canvas by ID.

        Args:
            canvas_id: Canvas identifier

        Returns:
            Canvas object or None if not found
        """
        self.update_accessed()
        return self.canvases.get(canvas_id)

    def remove_canvas(self, canvas_id: str) -> None:
        """Remove a canvas from the session.

        Args:
            canvas_id: Canvas identifier
        """
        if canvas_id in self.canvases:
            del self.canvases[canvas_id]
        self.update_accessed()

    def update_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if the session has expired.

        Returns:
            True if session has expired, False otherwise
        """
        return (time.time() - self.last_accessed) > self.timeout


class SessionManager:
    """Manages multiple user sessions."""

    def __init__(self, default_timeout: float = 300.0):
        """Initialize the session manager.

        Args:
            default_timeout: Default session timeout in seconds
        """
        self.default_timeout = default_timeout
        self.sessions: Dict[str, Session] = {}

    def get_or_create_session(self, session_id: str) -> Session:
        """Get an existing session or create a new one.

        Args:
            session_id: Session identifier

        Returns:
            Session object
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(
                session_id=session_id,
                timeout=self.default_timeout,
            )
        else:
            self.sessions[session_id].update_accessed()

        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.update_accessed()
        return session

    def remove_session(self, session_id: str) -> None:
        """Remove a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

    def cleanup_expired(self) -> None:
        """Remove all expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]

    def list_sessions(self) -> List[str]:
        """List all active session IDs.

        Returns:
            List of session IDs
        """
        self.cleanup_expired()
        return list(self.sessions.keys())

    def get_session_count(self) -> int:
        """Get the number of active sessions.

        Returns:
            Number of sessions
        """
        self.cleanup_expired()
        return len(self.sessions)
