from datetime import datetime, timedelta
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ChatMemoryModel(BaseModel):
    """
    Hermes Chat Memory Model with Conversation History Management

    This model handles conversation memory and context persistence
    using the Hermes capabilities for chat history management.
    """

    session_id: str = Field(..., description="Unique session identifier")
    conversation_memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="""Persistent memory store for the conversation
        Maintains context across sessions and interactions""",
    )

    recent_conversations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="""Last N conversations for quick recall
        Helps maintain context continuity""",
    )

    # Converstation message limit settings
    MAX_MESSAGES_PER_SESSION = 100

    @property
    def get_memory_history(self):
        """Memory and persistance store for the conversation"""
        return self.conversation_memory

    def get_memory_session(self) -> str:
        """Get current session identifier"""
        return self.session_id

    def apply_hermes_context(self, context_data: Dict[str, Any]) -> None:
        """Merge Hermes context into conversation memory
        This should be called when receiving context updates from Hermes"""
        self.conversation_memory.update(context_data)

    def cleanup_old_sessions(self, max_age: timedelta = timedelta(hours=24)) -> None:
        """Remove old conversation sessions from memory
        This helps maintain performance and memory usage"""
        current_time = datetime.now()

        # Remove expired sessions
        if "saved_sessions" in self.conversation_memory:
            valid_sessions = [
                sess
                for sess in self.conversation_memory["saved_sessions"]
                if current_time - sess["timestamp"] < max_age
            ]
            self.conversation_memory["saved_sessions"] = valid_sessions

        # Keep conversation history to a reasonable size
        if "messages" in self.conversation_memory:
            self.conversation_memory["messages"] = self.conversation_memory["messages"][
                -self.MAX_MESSAGES_PER_SESSION :
            ]

    def add_new_message(self, role: str, content: str) -> None:
        """Add a new message to conversation memory"""
        if "messages" not in self.conversation_memory:
            self.conversation_memory["messages"] = []

        message_data = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content[
                :1500
            ],  # Increase message length limit for use case testing
        }

        self.conversation_memory["messages"].append(message_data)

    def get_recent_context(self, last_n: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        if "messages" in self.conversation_memory:
            return self.conversation_memory["messages"][-last_n:]
        return []

    def current_conversation_summary(self, n: int = 5) -> str:
        """Generate current conversation summary"""
        if not self.conversation_memory.get("messages"):
            return "No conversation history available"

        # Extract latest messages
        recent_messages = "\n".join(
            [
                f"{m['role'].upper()}: {m['content'][:200]}"
                for m in self.conversation_memory["messages"][-n:]
            ]
        )

        return f"RECENT CONVERSATION (LAST {n} MESSAGES):\n{recent_messages}"


class HermesChatHistoryAPI:
    """
    Conan Agent Chat History API

    Provides an interface to the agent's conversational memory
    with enhanced capabilities for context management.
    """

    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.history = ChatMemoryModel(session_id=session_id)

    @property
    def messages(self) -> List[Dict[str, str]]:
        """Get conversation messages"""
        if "messages" in self.history.get_memory_history:
            return self.history.get_memory_history["messages"]
        return []

    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history"""
        self.history.add_new_message(role, content)

    def get_conversation_context(self) -> Dict[str, Any]:
        """Get complete conversation context"""
        return {
            "session_id": self.history.get_memory_session,
            "messages": self.messages,
            "timestamp": datetime.now().isoformat(),
        }

    def summarize_conversation(self, format: str = "detailed") -> str:
        """Summarize conversation history

        Args:
            format: Summary format - 'detailed' or 'brief'

        Returns:
            Formatted summary of conversation
        """
        if not self.messages:
            return "No conversation history available"

        summary_parts = []

        if format == "detailed":
            # Detailed format with conversation flow
            summary_parts.append("### Conversation Summary ###")
            summary_parts.append(f"Session: {self.session_id}")
            summary_parts.append(f"Messages: {len(self.messages)}")

            # Add the entire conversation
            for i, msg in enumerate(self.messages):
                summary_parts.append(f"\n{i + 1}. {msg['role'].upper()}:")
                summary_parts.append(
                    f"   {msg['content'][:250]}".replace("*{title}*", "").replace(
                        "{\n}", ""
                    )
                )
        else:
            # Brief format with key points
            summary_parts.append("### Conversation Highlights ###")
            summary_parts.append(f"Session: {self.session_id}")
            summary_parts.append(f"Messages: {len(self.messages)}")

            # Add recent messages
            summary_parts.append("\nRecent Messages:")
            for msg in reversed(self.messages[-3:]):
                summary_parts.append(f"- {msg['role'].upper()}:")
                summary_parts.append(f"  {msg['content'][:200]}")

        return "\n".join(summary_parts)

    def save_session(self, session_data: Dict[str, Any]) -> None:
        """Save session for later recall"""
        if "saved_sessions" not in self.history.get_memory_history:
            self.history.get_memory_history["saved_sessions"] = []

        saved_session = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "data": session_data,
        }

        self.history.get_memory_history["saved_sessions"].append(saved_session)

        # Clean up old sessions
        self.history.cleanup_old_sessions()
