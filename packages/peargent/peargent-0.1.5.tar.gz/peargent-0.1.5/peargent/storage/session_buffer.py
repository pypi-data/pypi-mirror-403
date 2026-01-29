"""
In-memory history storage implementation.
"""

from typing import Dict, List, Optional, Any
from .base import HistoryStore, Thread, Message


class InMemoryHistoryStore(HistoryStore):
    """In-memory history storage (useful for testing and development)."""

    def __init__(self):
        """Initialize in-memory store."""
        self.threads: Dict[str, Thread] = {}

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        """Create a new conversation thread."""
        thread = Thread(metadata=metadata)
        self.threads[thread.id] = thread
        return thread.id

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID."""
        return self.threads.get(thread_id)

    def append_message(
        self,
        thread_id: str,
        role: str,
        content: Any,
        agent: Optional[str] = None,
        tool_call: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Append a message to a thread."""
        thread = self.threads.get(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        message = Message(
            role=role,
            content=content,
            agent=agent,
            tool_call=tool_call,
            metadata=metadata
        )
        thread.add_message(message)
        return message

    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        thread = self.threads.get(thread_id)
        if not thread:
            return []
        return thread.messages

    def list_threads(self) -> List[str]:
        """List all thread IDs."""
        return list(self.threads.keys())

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        if thread_id in self.threads:
            del self.threads[thread_id]
            return True
        return False
