import datetime
import uuid
from typing import Dict, Optional


class SessionManager:
    """
    Simple session management for chat applications
    Tracks different chat sessions without user authentication
    """

    def __init__(self):
        self.active_sessions: Dict[str, dict] = {}

    # Session expiration settings
    SESSION_EXPIRATION_HOURS = 24

    def create_session(self) -> str:
        """Create a new session with unique ID"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "created_at": datetime.datetime.now().isoformat(),
            "last_active": datetime.datetime.now().isoformat(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session information"""
        if session_id in self.active_sessions:
            self._touch_session(session_id)
            return self.active_sessions[session_id]
        return None

    def _touch_session(self, session_id: str) -> None:
        """Update session last active time"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_active"] = (
                datetime.datetime.now().isoformat()
            )

    def cleanup_sessions(self, max_age: int = SESSION_EXPIRATION_HOURS * 3600) -> None:
        """Remove inactive sessions"""
        current_time = datetime.datetime.now()
        inactive_sessions = [
            sid
            for sid, session in self.active_sessions.items()
            if (
                current_time - datetime.datetime.fromisoformat(session["last_active"])
            ).total_seconds()
            > max_age
        ]

        for sid in inactive_sessions:
            del self.active_sessions[sid]

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)
