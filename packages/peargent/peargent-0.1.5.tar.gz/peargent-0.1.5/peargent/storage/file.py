"""
File-based history storage implementation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import HistoryStore, Thread, Message


class FileHistoryStore(HistoryStore):
    """File-based history storage using JSON files."""

    def __init__(self, storage_dir: str = ".peargent_history"):
        """
        Initialize file-based store.

        Args:
            storage_dir: Directory to store history files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def _get_thread_path(self, thread_id: str) -> Path:
        """Get file path for a thread."""
        return self.storage_dir / f"{thread_id}.json"

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        """Create a new conversation thread."""
        thread = Thread(metadata=metadata)
        thread_path = self._get_thread_path(thread.id)

        with open(thread_path, 'w') as f:
            json.dump(thread.to_dict(), f, indent=2)

        return thread.id

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID."""
        thread_path = self._get_thread_path(thread_id)
        if not thread_path.exists():
            return None

        with open(thread_path, 'r') as f:
            data = json.load(f)

        return Thread.from_dict(data)

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
        thread = self.get_thread(thread_id)
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

        # Save updated thread
        thread_path = self._get_thread_path(thread_id)
        with open(thread_path, 'w') as f:
            json.dump(thread.to_dict(), f, indent=2)

        return message

    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        thread = self.get_thread(thread_id)
        if not thread:
            return []
        return thread.messages

    def list_threads(self) -> List[str]:
        """List all thread IDs."""
        return [f.stem for f in self.storage_dir.glob("*.json")]

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        thread_path = self._get_thread_path(thread_id)
        if thread_path.exists():
            thread_path.unlink()
            return True
        return False
