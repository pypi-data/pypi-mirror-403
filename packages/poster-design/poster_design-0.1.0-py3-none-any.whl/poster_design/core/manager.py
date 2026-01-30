"""
Canvas and session management for poster design.

This module provides managers for handling multiple canvases and
sessions, particularly useful for MCP server scenarios.
"""

import uuid
import time
from typing import Dict, Optional
from datetime import datetime

from poster_design.core.canvas import Canvas


class CanvasManager:
    """Manages multiple canvas instances.

    Useful for scenarios where multiple canvases need to be tracked,
    such as in MCP sessions or batch operations.
    """

    def __init__(self):
        """Initialize the canvas manager."""
        self.canvases: Dict[str, Canvas] = {}

    def create(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        preset: Optional[str] = None,
        dpi: int = 72,
        canvas_id: Optional[str] = None,
    ) -> str:
        """Create a new canvas.

        Args:
            width: Canvas width
            height: Canvas height
            preset: Preset name
            dpi: DPI
            canvas_id: Optional custom canvas ID

        Returns:
            The ID of the created canvas
        """
        if canvas_id is None:
            canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"

        canvas = Canvas(width=width, height=height, preset=preset, dpi=dpi)
        canvas._id = canvas_id
        self.canvases[canvas_id] = canvas
        return canvas_id

    def get(self, canvas_id: str) -> Optional[Canvas]:
        """Get a canvas by ID.

        Args:
            canvas_id: The canvas ID

        Returns:
            The canvas if found, None otherwise
        """
        return self.canvases.get(canvas_id)

    def delete(self, canvas_id: str) -> bool:
        """Delete a canvas.

        Args:
            canvas_id: The canvas ID to delete

        Returns:
            True if canvas was deleted, False if not found
        """
        if canvas_id in self.canvases:
            del self.canvases[canvas_id]
            return True
        return False

    def list(self) -> list[str]:
        """List all canvas IDs.

        Returns:
            List of canvas IDs
        """
        return list(self.canvases.keys())


class SessionManager:
    """Manages design sessions for multi-user scenarios.

    Particularly useful for MCP server implementations where
    multiple clients may be working simultaneously.
    """

    def __init__(self, session_timeout: int = 3600):
        """Initialize the session manager.

        Args:
            session_timeout: Session timeout in seconds (default 1 hour)
        """
        self.sessions: Dict[str, Dict[str, any]] = {}
        self.session_timeout = session_timeout

    def create_session(self) -> str:
        """Create a new session.

        Returns:
            The session ID
        """
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = {
            "canvas_manager": CanvasManager(),
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, any]]:
        """Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session data if found, None otherwise
        """
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired(self, timeout: Optional[int] = None) -> int:
        """Clean up expired sessions.

        Args:
            timeout: Override timeout in seconds

        Returns:
            Number of sessions cleaned up
        """
        timeout = timeout if timeout is not None else self.session_timeout
        current_time = time.time()
        expired = []

        for session_id, session_data in self.sessions.items():
            last_activity = session_data["updated_at"]
            if current_time - last_activity > timeout:
                expired.append(session_id)

        for session_id in expired:
            self.delete_session(session_id)

        return len(expired)

    def update_activity(self, session_id: str) -> None:
        """Update the last activity time for a session.

        Args:
            session_id: The session ID

        Raises:
            KeyError: If session not found
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session not found: {session_id}")
        self.sessions[session_id]["updated_at"] = time.time()
