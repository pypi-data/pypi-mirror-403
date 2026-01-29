"""
High-level interface for managing conversation history.
"""

import json
from typing import Dict, List, Optional, Any
from peargent.storage import HistoryStore, Thread, Message

# Import concrete implementations
from peargent.storage import FileHistoryStore
from peargent.storage import InMemoryHistoryStore

# Try to import SQL-based stores
try:
    from peargent.storage import PostgreSQLHistoryStore
    POSTGRESQL_AVAILABLE = True
except ImportError:
    PostgreSQLHistoryStore = None
    POSTGRESQL_AVAILABLE = False

try:
    from peargent.storage import SQLiteHistoryStore
    SQLITE_AVAILABLE = True
except ImportError:
    SQLiteHistoryStore = None
    SQLITE_AVAILABLE = False


class ConversationHistory:
    """High-level interface for managing conversation history."""

    def __init__(self, store: HistoryStore):
        """
        Initialize conversation history manager.

        Args:
            store: History storage backend
        """
        self.store = store
        self.current_thread_id: Optional[str] = None

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        """
        Create a new conversation thread.

        Args:
            metadata: Thread metadata

        Returns:
            Thread ID
        """
        thread_id = self.store.create_thread(metadata)
        self.current_thread_id = thread_id
        return thread_id

    def use_thread(self, thread_id: str):
        """
        Set the current active thread.

        Args:
            thread_id: Thread identifier
        """
        thread = self.store.get_thread(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        self.current_thread_id = thread_id

    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> Message:
        """
        Add a user message to the current thread.

        Args:
            content: Message content
            metadata: Message metadata

        Returns:
            Created message
        """
        if not self.current_thread_id:
            raise ValueError("No active thread. Call create_thread() or use_thread() first")

        return self.store.append_message(
            thread_id=self.current_thread_id,
            role="user",
            content=content,
            metadata=metadata
        )

    def add_assistant_message(
        self,
        content: Any,
        agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """
        Add an assistant message to the current thread.

        Args:
            content: Message content
            agent: Agent name
            metadata: Message metadata

        Returns:
            Created message
        """
        if not self.current_thread_id:
            raise ValueError("No active thread. Call create_thread() or use_thread() first")

        return self.store.append_message(
            thread_id=self.current_thread_id,
            role="assistant",
            content=content,
            agent=agent,
            metadata=metadata
        )

    def add_tool_message(
        self,
        tool_call: Dict,
        agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """
        Add a tool execution message to the current thread.

        Args:
            tool_call: Tool call information (name, args, output)
            agent: Agent name
            metadata: Message metadata

        Returns:
            Created message
        """
        if not self.current_thread_id:
            raise ValueError("No active thread. Call create_thread() or use_thread() first")

        return self.store.append_message(
            thread_id=self.current_thread_id,
            role="tool",
            content=tool_call.get("output"),
            agent=agent,
            tool_call=tool_call,
            metadata=metadata
        )

    def get_messages(
        self,
        thread_id: Optional[str] = None,
        role: Optional[str] = None,
        agent: Optional[str] = None
    ) -> List[Message]:
        """
        Get messages from a thread.

        Args:
            thread_id: Thread identifier (uses current thread if not specified)
            role: Filter by message role
            agent: Filter by agent name

        Returns:
            List of messages
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            return []

        return thread.get_messages(role=role, agent=agent)

    def get_thread(self, thread_id: Optional[str] = None) -> Optional[Thread]:
        """
        Get a thread object.

        Args:
            thread_id: Thread identifier (uses current thread if not specified)

        Returns:
            Thread object or None
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            return None
        return self.store.get_thread(tid)

    def list_threads(self) -> List[str]:
        """
        List all thread IDs.

        Returns:
            List of thread IDs
        """
        return self.store.list_threads()

    def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            True if deleted, False if not found
        """
        return self.store.delete_thread(thread_id)

    def trim_messages(self, strategy: str = "last", count: int = 10, keep_system: bool = True, thread_id: Optional[str] = None) -> int:
        """
        Trim messages in the current or specified thread.

        Args:
            strategy: "first", "last", or "first_last"
            count: Number of messages to keep
            keep_system: Preserve system messages
            thread_id: Thread to trim (uses current if not specified)

        Returns:
            Number of messages removed
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            raise ValueError(f"Thread {tid} not found")

        removed = thread.trim_messages(strategy, count, keep_system)

        # Update storage
        self._save_thread(tid, thread)
        return removed

    def delete_message(self, message_id: str, thread_id: Optional[str] = None) -> bool:
        """
        Delete a specific message.

        Args:
            message_id: Message ID to delete
            thread_id: Thread containing the message (uses current if not specified)

        Returns:
            True if deleted, False if not found
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            raise ValueError(f"Thread {tid} not found")

        deleted = thread.delete_message(message_id)

        if deleted:
            self._save_thread(tid, thread)

        return deleted

    def delete_messages(self, message_ids: List[str], thread_id: Optional[str] = None) -> int:
        """
        Delete multiple messages.

        Args:
            message_ids: List of message IDs to delete
            thread_id: Thread containing the messages (uses current if not specified)

        Returns:
            Number of messages deleted
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            raise ValueError(f"Thread {tid} not found")

        deleted_count = thread.delete_messages(message_ids)

        if deleted_count > 0:
            self._save_thread(tid, thread)

        return deleted_count

    def summarize_messages(self, model: Any, start_index: int = 0, end_index: Optional[int] = None, keep_recent: int = 5, thread_id: Optional[str] = None) -> Message:
        """
        Summarize messages using an LLM.

        Args:
            model: LLM model instance
            start_index: Start index for summarization
            end_index: End index (defaults to len-keep_recent)
            keep_recent: Number of recent messages to preserve
            thread_id: Thread to summarize (uses current if not specified)

        Returns:
            The summary Message object
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            raise ValueError(f"Thread {tid} not found")

        summary = thread.summarize_messages(model, start_index, end_index, keep_recent)

        # Update storage
        self._save_thread(tid, thread)
        return summary

    def get_message_count(self, thread_id: Optional[str] = None) -> int:
        """
        Get the number of messages in a thread.

        Args:
            thread_id: Thread to count (uses current if not specified)

        Returns:
            Number of messages
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        thread = self.store.get_thread(tid)
        if not thread:
            return 0

        return len(thread.messages)

    def _select_smart_strategy(self, message_count: int, max_messages: int, thread_id: str) -> str:
        """
        Intelligently select the best context management strategy.

        Analyzes conversation characteristics to pick optimal strategy:
        - Small overflow: trim (faster, no LLM needed)
        - Medium overflow: summarize (preserve context)
        - Large overflow with tools: summarize (preserve tool results)

        Args:
            message_count: Current message count
            max_messages: Maximum allowed messages
            thread_id: Thread to analyze

        Returns:
            Strategy name: "trim_last", "summarize", or None
        """
        if message_count <= max_messages:
            return None

        excess = message_count - max_messages
        thread = self.store.get_thread(thread_id)

        # Check if there are tool messages (important context to preserve)
        has_tools = any(msg.role == "tool" for msg in thread.messages)

        # Small overflow (< 25% over): Just trim recent messages
        if excess < (max_messages * 0.25):
            return "trim_last"

        # Medium overflow or has important tool calls: Summarize to preserve context
        elif excess < (max_messages * 0.5) or has_tools:
            return "summarize"

        # Large overflow: Aggressive summarization
        else:
            return "summarize"

    def manage_context_window(self, model: Any, max_messages: int = 20, strategy: str = "smart", thread_id: Optional[str] = None):
        """
        Automatically manage context window size.

        This is a convenience method that applies context management strategies
        when message count exceeds a threshold.

        Args:
            model: LLM model for summarization (if strategy="summarize" or "smart")
            max_messages: Maximum number of messages before applying strategy
            strategy: "trim_last" (keep recent), "trim_first" (keep oldest),
                     "summarize" (summarize old, keep recent), or
                     "smart" (automatically select best strategy - default)
            thread_id: Thread to manage (uses current if not specified)
        """
        tid = thread_id or self.current_thread_id
        if not tid:
            raise ValueError("No thread specified and no active thread")

        message_count = self.get_message_count(tid)

        if message_count <= max_messages:
            return

        # Smart strategy selection
        if strategy == "smart":
            selected_strategy = self._select_smart_strategy(message_count, max_messages, tid)
            if not selected_strategy:
                return
            strategy = selected_strategy

        if strategy == "trim_last":
            self.trim_messages(strategy="last", count=max_messages, thread_id=tid)
        elif strategy == "trim_first":
            self.trim_messages(strategy="first", count=max_messages, thread_id=tid)
        elif strategy == "summarize":
            # Keep half the max_messages as recent, summarize the rest
            keep_recent = max_messages // 2
            self.summarize_messages(model, keep_recent=keep_recent, thread_id=tid)

    def _save_thread(self, thread_id: str, thread: Thread):
        """
        Save thread changes back to storage.

        This is an internal helper for persistence after modifications.
        """
        if isinstance(self.store, FileHistoryStore):
            # For file store, we need to manually save
            thread_path = self.store._get_thread_path(thread_id)
            with open(thread_path, 'w') as f:
                json.dump(thread.to_dict(), f, indent=2)
        elif isinstance(self.store, InMemoryHistoryStore):
            # For in-memory, it's already updated (reference)
            pass
        elif POSTGRESQL_AVAILABLE and isinstance(self.store, PostgreSQLHistoryStore):
            # For PostgreSQL, we need to completely recreate the thread
            self._save_thread_to_sql(thread_id, thread)
        elif SQLITE_AVAILABLE and isinstance(self.store, SQLiteHistoryStore):
            # For SQLite, we need to completely recreate the thread
            self._save_thread_to_sql(thread_id, thread)

    def _save_thread_to_sql(self, thread_id: str, thread: Thread):
        """
        Save thread changes to SQL database (PostgreSQL or SQLite) using SQLAlchemy.

        This deletes all existing messages and recreates them to maintain consistency.
        """
        # Import here to avoid circular dependency
        from sqlalchemy import update, delete, insert

        if not hasattr(self.store, 'engine'):
            return

        with self.store.engine.begin() as conn:
            # Update thread metadata and timestamps
            stmt = (
                update(self.store.threads_table)
                .where(self.store.threads_table.c.id == thread_id)
                .values(
                    updated_at=thread.updated_at,
                    metadata=thread.metadata
                )
            )
            conn.execute(stmt)

            # Delete all existing messages for this thread
            stmt = delete(self.store.messages_table).where(
                self.store.messages_table.c.thread_id == thread_id
            )
            conn.execute(stmt)

            # Re-insert all messages in the correct order
            for sequence, message in enumerate(thread.messages):
                stmt = insert(self.store.messages_table).values(
                    id=message.id,
                    thread_id=thread_id,
                    timestamp=message.timestamp,
                    role=message.role,
                    content=str(message.content) if message.content else None,
                    agent=message.agent,
                    tool_call=message.tool_call,
                    metadata=message.metadata,
                    sequence=sequence
                )
                conn.execute(stmt)
