# peargent/telemetry/redis_store.py

"""
Redis-based tracing storage implementation.

Provides fast, distributed trace storage using Redis.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .store import TracingStore
from .trace import Trace, TraceStatus
from .span import Span, SpanType, SpanStatus

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisTracingStore(TracingStore):
    """
    Redis-based trace storage for distributed, high-performance applications.

    Features:
    - Fast in-memory storage with optional persistence
    - Distributed access (multiple servers can share same Redis)
    - Built-in expiration (TTL) support
    - Efficient filtering with Redis sets

    Storage structure:
    - Traces: hash at key "{prefix}:trace:{trace_id}"
    - Trace index: sorted set at key "{prefix}:traces:index" (sorted by timestamp)
    - Session index: set at key "{prefix}:session:{session_id}:traces"
    - User index: set at key "{prefix}:user:{user_id}:traces"
    - Agent index: set at key "{prefix}:agent:{agent_name}:traces"
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "peargent",
        ttl: Optional[int] = None  # Time-to-live in seconds (None = no expiration)
    ):
        """
        Initialize Redis tracing store.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (if required)
            key_prefix: Key prefix for namespacing
            ttl: Optional time-to-live for traces in seconds

        Raises:
            ImportError: If redis package is not installed
            redis.ConnectionError: If cannot connect to Redis
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis is required for Redis tracing storage. "
                "Install it with: pip install redis"
            )

        self.key_prefix = key_prefix
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

    def _trace_key(self, trace_id: str) -> str:
        """Get Redis key for trace data."""
        return f"{self.key_prefix}:trace:{trace_id}"

    def _traces_index_key(self) -> str:
        """Get Redis key for traces index (sorted set)."""
        return f"{self.key_prefix}:traces:index"

    def _session_index_key(self, session_id: str) -> str:
        """Get Redis key for session index."""
        return f"{self.key_prefix}:session:{session_id}:traces"

    def _user_index_key(self, user_id: str) -> str:
        """Get Redis key for user index."""
        return f"{self.key_prefix}:user:{user_id}:traces"

    def _agent_index_key(self, agent_name: str) -> str:
        """Get Redis key for agent index."""
        return f"{self.key_prefix}:agent:{agent_name}:traces"

    def _serialize_trace(self, trace: Trace) -> str:
        """Serialize trace to JSON string."""
        return json.dumps({
            "trace_id": trace.trace_id,
            "agent_name": trace.agent_name,
            "input": trace.input,
            "output": trace.output,
            "error": trace.error,
            "session_id": trace.session_id,
            "user_id": trace.user_id,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "duration_ms": trace.duration_ms,
            "status": trace.status.value if trace.status else None,
            "spans": [self._serialize_span(span) for span in trace.spans],
            "total_tokens": trace.total_tokens,
            "total_cost": trace.total_cost,
        })

    def _serialize_span(self, span: Span) -> Dict[str, Any]:
        """Serialize span to dictionary."""
        return {
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_span_id": span.parent_span_id,
            "span_type": span.span_type.value if span.span_type else None,
            "name": span.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "duration_ms": span.duration_ms,
            "status": span.status.value if span.status else None,
            "error": span.error,
            "attributes": span.attributes,
            "model": span.model,
            "token_prompt": span.token_prompt,
            "token_completion": span.token_completion,
            "cost": span.cost,
        }

    def _deserialize_trace(self, data: str) -> Trace:
        """Deserialize trace from JSON string."""
        obj = json.loads(data)

        # Reconstruct spans
        spans = []
        for span_data in obj.get("spans", []):
            span = Span(
                span_id=span_data["span_id"],
                trace_id=span_data["trace_id"],
                parent_span_id=span_data.get("parent_span_id"),
                span_type=SpanType(span_data["span_type"]) if span_data.get("span_type") else None,
                name=span_data["name"],
                start_time=span_data["start_time"],
            )
            span.end_time = span_data.get("end_time")
            span.duration_ms = span_data.get("duration_ms")
            span.status = SpanStatus(span_data["status"]) if span_data.get("status") else None
            span.error = span_data.get("error")
            span.attributes = span_data.get("attributes", {})
            span.model = span_data.get("model")
            span.token_prompt = span_data.get("token_prompt")
            span.token_completion = span_data.get("token_completion")
            span.cost = span_data.get("cost")
            spans.append(span)

        # Reconstruct trace
        trace = Trace(
            trace_id=obj["trace_id"],
            agent_name=obj["agent_name"],
            input=obj.get("input"),
            session_id=obj.get("session_id"),
            user_id=obj.get("user_id"),
        )
        trace.output = obj.get("output")
        trace.error = obj.get("error")
        trace.start_time = obj["start_time"]
        trace.end_time = obj.get("end_time")
        trace.duration_ms = obj.get("duration_ms")
        trace.status = TraceStatus(obj["status"]) if obj.get("status") else None
        trace.spans = spans
        trace.total_tokens = obj.get("total_tokens", 0)
        trace.total_cost = obj.get("total_cost", 0.0)

        return trace

    def save_trace(self, trace: Trace) -> None:
        """Save trace to Redis."""
        trace_key = self._trace_key(trace.trace_id)
        trace_data = self._serialize_trace(trace)

        # Save trace data
        self.client.set(trace_key, trace_data)

        # Set TTL if configured
        if self.ttl:
            self.client.expire(trace_key, self.ttl)

        # Add to main index (sorted by start time)
        self.client.zadd(
            self._traces_index_key(),
            {trace.trace_id: trace.start_time}
        )

        # Add to session index
        if trace.session_id:
            session_key = self._session_index_key(trace.session_id)
            self.client.sadd(session_key, trace.trace_id)
            if self.ttl:
                self.client.expire(session_key, self.ttl)

        # Add to user index
        if trace.user_id:
            user_key = self._user_index_key(trace.user_id)
            self.client.sadd(user_key, trace.trace_id)
            if self.ttl:
                self.client.expire(user_key, self.ttl)

        # Add to agent index
        if trace.agent_name:
            agent_key = self._agent_index_key(trace.agent_name)
            self.client.sadd(agent_key, trace.trace_id)
            if self.ttl:
                self.client.expire(agent_key, self.ttl)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve trace from Redis."""
        trace_key = self._trace_key(trace_id)
        data = self.client.get(trace_key)

        if not data:
            return None

        return self._deserialize_trace(data)

    def list_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Trace]:
        """List traces with optional filtering."""
        # Determine which index to query
        if session_id:
            # Get trace IDs from session index
            trace_ids = self.client.smembers(self._session_index_key(session_id))
        elif user_id:
            # Get trace IDs from user index
            trace_ids = self.client.smembers(self._user_index_key(user_id))
        elif agent_name:
            # Get trace IDs from agent index
            trace_ids = self.client.smembers(self._agent_index_key(agent_name))
        else:
            # Get most recent trace IDs from main index (reverse chronological)
            trace_ids = self.client.zrevrange(
                self._traces_index_key(),
                0,
                limit - 1
            )

        # Retrieve traces
        traces = []
        for trace_id in trace_ids:
            if len(traces) >= limit:
                break

            trace = self.get_trace(trace_id)
            if trace:
                traces.append(trace)

        return traces

    def delete_trace(self, trace_id: str) -> bool:
        """Delete trace from Redis."""
        trace = self.get_trace(trace_id)
        if not trace:
            return False

        # Delete trace data
        self.client.delete(self._trace_key(trace_id))

        # Remove from main index
        self.client.zrem(self._traces_index_key(), trace_id)

        # Remove from session index
        if trace.session_id:
            self.client.srem(self._session_index_key(trace.session_id), trace_id)

        # Remove from user index
        if trace.user_id:
            self.client.srem(self._user_index_key(trace.user_id), trace_id)

        # Remove from agent index
        if trace.agent_name:
            self.client.srem(self._agent_index_key(trace.agent_name), trace_id)

        return True

    def clear_all(self) -> int:
        """Clear all traces from Redis."""
        # Get all trace IDs from main index
        trace_ids = self.client.zrange(self._traces_index_key(), 0, -1)

        count = 0
        for trace_id in trace_ids:
            if self.delete_trace(trace_id):
                count += 1

        # Clean up the main index
        self.client.delete(self._traces_index_key())

        return count
