"""
SQLite-based history storage implementation using SQLAlchemy.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import HistoryStore, Thread, Message

try:
    from sqlalchemy import (
        create_engine, Table, Column, String, DateTime, Integer,
        MetaData, select, insert, update, delete, Index, ForeignKey,
        Text, JSON, func
    )
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class SQLiteHistoryStore(HistoryStore):
    """SQLite-based history storage using SQLAlchemy for local persistence."""

    def __init__(self, database_path: str = "peargent_history.db", table_prefix: str = "peargent"):
        """
        Initialize SQLite store with SQLAlchemy.

        Args:
            database_path: Path to SQLite database file (default: "peargent_history.db")
            table_prefix: Prefix for table names (default: "peargent")

        Raises:
            ImportError: If SQLAlchemy is not installed
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy is required for SQLite history storage. "
                "Install it with: pip install sqlalchemy"
            )

        self.database_path = database_path
        self.table_prefix = table_prefix

        # Create SQLAlchemy engine
        # Use check_same_thread=False for SQLite to allow multi-threaded access
        connection_string = f"sqlite:///{database_path}"
        self.engine = create_engine(
            connection_string,
            connect_args={"check_same_thread": False}
        )

        # Define metadata and tables
        self.metadata = MetaData()

        # Define threads table
        self.threads_table = Table(
            f"{table_prefix}_threads",
            self.metadata,
            Column("id", String, primary_key=True),
            Column("created_at", DateTime, nullable=False),
            Column("updated_at", DateTime, nullable=False),
            Column("metadata", JSON, default={}),
        )

        # Define messages table
        self.messages_table = Table(
            f"{table_prefix}_messages",
            self.metadata,
            Column("id", String, primary_key=True),
            Column("thread_id", String, ForeignKey(f"{table_prefix}_threads.id", ondelete="CASCADE"), nullable=False),
            Column("timestamp", DateTime, nullable=False),
            Column("role", String, nullable=False),
            Column("content", Text),
            Column("agent", String),
            Column("tool_call", JSON),
            Column("metadata", JSON, default={}),
            Column("sequence", Integer, nullable=False),
            Index(f"idx_{table_prefix}_messages_thread_id", "thread_id", "sequence")
        )

        # Create tables if they don't exist
        self._init_tables()

    def _init_tables(self):
        """Create tables if they don't exist."""
        self.metadata.create_all(self.engine)

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        """Create a new conversation thread."""
        thread = Thread(metadata=metadata)

        with self.engine.begin() as conn:
            stmt = insert(self.threads_table).values(
                id=thread.id,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                metadata=thread.metadata
            )
            conn.execute(stmt)

        return thread.id

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID."""
        with self.engine.connect() as conn:
            # Get thread metadata
            stmt = select(self.threads_table).where(
                self.threads_table.c.id == thread_id
            )
            result = conn.execute(stmt).first()

            if not result:
                return None

            # Create thread object
            thread = Thread(
                thread_id=result.id,
                metadata=result.metadata or {},
                created_at=result.created_at,
                updated_at=result.updated_at
            )

            # Get messages
            stmt = (
                select(self.messages_table)
                .where(self.messages_table.c.thread_id == thread_id)
                .order_by(self.messages_table.c.sequence.asc())
            )
            messages_result = conn.execute(stmt)

            for msg_row in messages_result:
                message = Message(
                    message_id=msg_row.id,
                    timestamp=msg_row.timestamp,
                    role=msg_row.role,
                    content=msg_row.content,
                    agent=msg_row.agent,
                    tool_call=msg_row.tool_call,
                    metadata=msg_row.metadata or {}
                )
                thread.messages.append(message)

            return thread

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
        # Check if thread exists
        if not self.get_thread(thread_id):
            raise ValueError(f"Thread {thread_id} not found")

        message = Message(
            role=role,
            content=content,
            agent=agent,
            tool_call=tool_call,
            metadata=metadata
        )

        with self.engine.begin() as conn:
            # Get current max sequence
            stmt = select(func.coalesce(func.max(self.messages_table.c.sequence), -1) + 1).where(
                self.messages_table.c.thread_id == thread_id
            )
            sequence = conn.execute(stmt).scalar()

            # Insert message
            stmt = insert(self.messages_table).values(
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

            # Update thread's updated_at
            stmt = (
                update(self.threads_table)
                .where(self.threads_table.c.id == thread_id)
                .values(updated_at=datetime.now())
            )
            conn.execute(stmt)

        return message

    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        thread = self.get_thread(thread_id)
        if not thread:
            return []
        return thread.messages

    def list_threads(self) -> List[str]:
        """List all thread IDs ordered by most recently updated."""
        with self.engine.connect() as conn:
            stmt = select(self.threads_table.c.id).order_by(
                self.threads_table.c.updated_at.desc()
            )
            result = conn.execute(stmt)
            return [row.id for row in result]

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread (messages are cascade deleted)."""
        with self.engine.begin() as conn:
            stmt = delete(self.threads_table).where(
                self.threads_table.c.id == thread_id
            )
            result = conn.execute(stmt)
            return result.rowcount > 0
