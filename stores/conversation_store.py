"""
Conversation Store

In-memory storage for active conversation context.
Stores only until task is completed (API tool invoked).
"""

import uuid
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Auto-expire conversations after 30 minutes of inactivity
CONVERSATION_TTL_SECONDS = 30 * 60


@dataclass
class Message:
    """Single message in conversation."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class Conversation:
    """Active conversation context."""
    id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = time.time()

    def is_expired(self) -> bool:
        """Check if conversation has expired."""
        return time.time() - self.updated_at > CONVERSATION_TTL_SECONDS

    def get_history(self) -> List[Dict[str, str]]:
        """Get messages as list of dicts."""
        return [{"role": m.role, "content": m.content} for m in self.messages]


class ConversationStore:
    """
    In-memory conversation store.

    Stores conversation context until task is completed.
    Thread-safe for async usage.
    """

    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}

    def create(self, user_id: str) -> Conversation:
        """Create a new conversation."""
        conv_id = str(uuid.uuid4())
        conv = Conversation(id=conv_id, user_id=user_id)
        self._conversations[conv_id] = conv
        logger.info(f"Created conversation: {conv_id}")
        return conv

    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        conv = self._conversations.get(conversation_id)
        if conv and conv.is_expired():
            self.delete(conversation_id)
            return None
        return conv

    def get_or_create(self, conversation_id: Optional[str], user_id: str) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            conv = self.get(conversation_id)
            if conv:
                return conv
        return self.create(user_id)

    def delete(self, conversation_id: str) -> None:
        """Delete conversation (task completed)."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")

    def cleanup_expired(self) -> int:
        """Remove expired conversations. Returns count removed."""
        expired = [
            cid for cid, conv in self._conversations.items()
            if conv.is_expired()
        ]
        for cid in expired:
            del self._conversations[cid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")
        return len(expired)

    def count(self) -> int:
        """Get number of active conversations."""
        return len(self._conversations)


# Global singleton instance
conversation_store = ConversationStore()
