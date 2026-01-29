"""
Redis-based history storage implementation.

This is an EXAMPLE implementation showing how to extend peargent's history system
with custom storage backends. Users can follow this pattern to create their own
implementations (MongoDB, DynamoDB, etc.).

To use this:
1. Install redis: pip install redis
2. Start Redis server: redis-server (or use Redis Cloud)
3. Import and use like any other history store
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import HistoryStore, Thread, Message

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisHistoryStore(HistoryStore):
    """
    Redis-based history storage for distributed, high-performance applications.

    Features:
    - Fast in-memory storage with optional persistence
    - Distributed access (multiple servers can share same Redis)
    - Built-in expiration (TTL) support
    - Pub/sub capabilities for real-time updates

    Storage structure:
    - Threads: hash at key "thread:{thread_id}"
    - Messages: list at key "thread:{thread_id}:messages"
    - Thread index: sorted set at key "threads:index"
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "peargent",
        ttl: Optional[int] = None  # Time-to-live in seconds (None = no expiration)
    ):
        """
        Initialize Redis store.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (if required)
            prefix: Key prefix for namespacing
            ttl: Optional time-to-live for threads in seconds

        Raises:
            ImportError: If redis package is not installed
            redis.ConnectionError: If cannot connect to Redis
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis is required for Redis history storage. "
                "Install it with: pip install redis"
            )

        self.prefix = prefix
        self.ttl = ttl

        # Create Redis connection
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Automatically decode bytes to strings
        )

        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise redis.ConnectionError(
                f"Cannot connect to Redis at {host}:{port}. "
                f"Make sure Redis server is running. Error: {e}"
            )

    def _thread_key(self, thread_id: str) -> str:
        """Get Redis key for thread metadata."""
        return f"{self.prefix}:thread:{thread_id}"

    def _messages_key(self, thread_id: str) -> str:
        """Get Redis key for thread messages."""
        return f"{self.prefix}:thread:{thread_id}:messages"

    def _index_key(self) -> str:
        """Get Redis key for thread index (sorted set by update time)."""
        return f"{self.prefix}:threads:index"

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        """Create a new conversation thread."""
        thread = Thread(metadata=metadata)

        # Store thread metadata as hash
        thread_data = {
            "id": thread.id,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "metadata": json.dumps(thread.metadata)
        }

        pipe = self.client.pipeline()

        # Set thread data
        pipe.hset(self._thread_key(thread.id), mapping=thread_data)

        # Add to thread index (sorted by updated_at timestamp)
        pipe.zadd(
            self._index_key(),
            {thread.id: thread.updated_at.timestamp()}
        )

        # Set TTL if configured
        if self.ttl:
            pipe.expire(self._thread_key(thread.id), self.ttl)
            pipe.expire(self._messages_key(thread.id), self.ttl)

        pipe.execute()

        return thread.id

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID."""
        # Get thread metadata
        thread_data = self.client.hgetall(self._thread_key(thread_id))

        if not thread_data:
            return None

        # Parse thread data
        thread = Thread(
            thread_id=thread_data["id"],
            metadata=json.loads(thread_data.get("metadata", "{}")),
            created_at=datetime.fromisoformat(thread_data["created_at"]),
            updated_at=datetime.fromisoformat(thread_data["updated_at"])
        )

        # Get messages (stored as JSON list)
        messages_json = self.client.lrange(self._messages_key(thread_id), 0, -1)

        for msg_json in messages_json:
            msg_data = json.loads(msg_json)
            message = Message(
                message_id=msg_data["id"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                role=msg_data["role"],
                content=msg_data["content"],
                agent=msg_data.get("agent"),
                tool_call=msg_data.get("tool_call"),
                metadata=msg_data.get("metadata", {})
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
        if not self.client.exists(self._thread_key(thread_id)):
            raise ValueError(f"Thread {thread_id} not found")

        message = Message(
            role=role,
            content=content,
            agent=agent,
            tool_call=tool_call,
            metadata=metadata
        )

        # Serialize message
        message_json = json.dumps({
            "id": message.id,
            "timestamp": message.timestamp.isoformat(),
            "role": message.role,
            "content": message.content,
            "agent": message.agent,
            "tool_call": message.tool_call,
            "metadata": message.metadata
        })

        pipe = self.client.pipeline()

        # Append message to list
        pipe.rpush(self._messages_key(thread_id), message_json)

        # Update thread's updated_at
        now = datetime.now()
        pipe.hset(self._thread_key(thread_id), "updated_at", now.isoformat())

        # Update index
        pipe.zadd(self._index_key(), {thread_id: now.timestamp()})

        # Refresh TTL if configured
        if self.ttl:
            pipe.expire(self._thread_key(thread_id), self.ttl)
            pipe.expire(self._messages_key(thread_id), self.ttl)

        pipe.execute()

        return message

    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        thread = self.get_thread(thread_id)
        if not thread:
            return []
        return thread.messages

    def list_threads(self) -> List[str]:
        """List all thread IDs ordered by most recently updated."""
        # Get from sorted set in reverse order (most recent first)
        thread_ids = self.client.zrevrange(self._index_key(), 0, -1)
        return thread_ids

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and all its messages."""
        pipe = self.client.pipeline()

        # Delete thread data
        pipe.delete(self._thread_key(thread_id))

        # Delete messages
        pipe.delete(self._messages_key(thread_id))

        # Remove from index
        pipe.zrem(self._index_key(), thread_id)

        results = pipe.execute()

        # Check if thread was deleted (first delete command)
        return results[0] > 0

    # Additional Redis-specific methods

    def get_thread_count(self) -> int:
        """Get total number of threads."""
        return self.client.zcard(self._index_key())

    def get_message_count(self, thread_id: str) -> int:
        """Get number of messages in a thread."""
        return self.client.llen(self._messages_key(thread_id))

    def clear_all(self):
        """
        Clear all history data (DANGEROUS!).

        Use with caution - this deletes ALL threads and messages.
        """
        pattern = f"{self.prefix}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        total_threads = self.get_thread_count()
        total_messages = 0

        for thread_id in self.list_threads():
            total_messages += self.get_message_count(thread_id)

        # Get Redis memory usage
        info = self.client.info("memory")

        return {
            "total_threads": total_threads,
            "total_messages": total_messages,
            "redis_memory_used": info.get("used_memory_human", "N/A"),
            "redis_memory_peak": info.get("used_memory_peak_human", "N/A"),
        }
