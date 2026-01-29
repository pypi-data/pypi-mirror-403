"""
Database-backed tracing stores for PostgreSQL and SQLite using SQLAlchemy ORM.

Provides persistent storage for traces and spans with proper indexing and querying.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime
import json

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from peargent.observability.trace import Trace, Span, SpanType


def create_trace_model(base, table_name: str = "traces", spans_table_name: str = "spans"):
    """
    Dynamically create a Trace model with custom table name.

    Args:
        base: SQLAlchemy declarative base
        table_name: Name for the traces table
        spans_table_name: Name for the spans table (for relationship)

    Returns:
        SQLAlchemy model class
    """

    class TraceModel(base):
        __tablename__ = table_name

        id = Column(String(36), primary_key=True)
        agent_name = Column(String(255), nullable=False, index=True)
        input_data = Column(Text)
        output = Column(Text)
        error = Column(Text)
        session_id = Column(String(255), index=True)
        user_id = Column(String(255), index=True)
        start_time = Column(DateTime, nullable=False, index=True)
        end_time = Column(DateTime)
        duration_ms = Column(Integer)
        total_tokens = Column(Integer, default=0)
        total_cost = Column(Float, default=0.0)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)

        # Relationship to spans
        spans = relationship(
            "SpanModel",
            back_populates="trace",
            cascade="all, delete-orphan",
            foreign_keys=f"SpanModel.trace_id"
        )

    return TraceModel


def create_span_model(base, table_name: str = "spans", traces_table_name: str = "traces"):
    """
    Dynamically create a Span model with custom table name.

    Args:
        base: SQLAlchemy declarative base
        table_name: Name for the spans table
        traces_table_name: Name for the traces table (for foreign key)

    Returns:
        SQLAlchemy model class
    """

    class SpanModel(base):
        __tablename__ = table_name

        id = Column(String(36), primary_key=True)
        trace_id = Column(String(36), ForeignKey(f"{traces_table_name}.id", ondelete="CASCADE"), nullable=False, index=True)
        parent_span_id = Column(String(36))
        span_type = Column(String(50), nullable=False, index=True)
        name = Column(String(255), nullable=False)
        start_time = Column(DateTime, nullable=False)
        end_time = Column(DateTime)
        duration_ms = Column(Integer)

        # LLM-specific fields
        llm_prompt = Column(Text)
        llm_response = Column(Text)
        llm_model = Column(String(100))
        prompt_tokens = Column(Integer)
        completion_tokens = Column(Integer)
        cost = Column(Float)

        # Tool-specific fields
        tool_name = Column(String(255))
        tool_args = Column(Text)
        tool_output = Column(Text)

        created_at = Column(DateTime, default=datetime.utcnow, index=True)

        # Relationship to trace
        trace = relationship("TraceModel", back_populates="spans")

    return SpanModel


class DatabaseTracingStore:
    """
    SQLAlchemy-based tracing store for PostgreSQL and SQLite.

    Args:
        connection_string: Database connection string
            - PostgreSQL: "postgresql://user:password@host:port/database"
            - SQLite: "sqlite:///path/to/database.db"
        traces_table: Name of the traces table (default: "traces")
        spans_table: Name of the spans table (default: "spans")
        auto_migrate: Automatically create schema if it doesn't exist (default: True)
    """

    def __init__(
        self,
        connection_string: str,
        traces_table: str = "traces",
        spans_table: str = "spans",
        auto_migrate: bool = True
    ):
        self.connection_string = connection_string
        self.traces_table = traces_table
        self.spans_table = spans_table

        # Create engine
        self.engine = create_engine(connection_string)

        # Create a unique declarative base for this instance
        self.Base = declarative_base()

        # Create custom models with specified table names
        self.TraceModel = create_trace_model(self.Base, traces_table, spans_table)
        self.SpanModel = create_span_model(self.Base, spans_table, traces_table)

        # Update relationships after both models are created
        self.TraceModel.spans.property.argument = self.SpanModel
        self.SpanModel.trace.property.argument = self.TraceModel

        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Run migrations if requested
        if auto_migrate:
            self.run_migrations()

    def run_migrations(self):
        """Create database schema."""
        self.Base.metadata.create_all(bind=self.engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_trace(self, trace: Trace) -> None:
        """
        Save a complete trace with all its spans to the database.

        Args:
            trace: Trace object to save
        """
        session = self._get_session()
        try:
            # Convert timestamps
            start_time = self._convert_timestamp(trace.start_time)
            end_time = self._convert_timestamp(trace.end_time)
            duration_ms = int(trace.duration * 1000) if trace.duration else None

            # Convert error to string
            error_str = None
            if trace.error:
                error_str = str(trace.error) if not isinstance(trace.error, str) else trace.error

            # Check if trace exists
            existing_trace = session.query(self.TraceModel).filter_by(id=trace.trace_id).first()

            if existing_trace:
                # Update existing trace
                existing_trace.agent_name = trace.agent_name
                existing_trace.input_data = trace.input
                existing_trace.output = trace.output
                existing_trace.error = error_str
                existing_trace.session_id = trace.session_id
                existing_trace.user_id = trace.user_id
                existing_trace.start_time = start_time
                existing_trace.end_time = end_time
                existing_trace.duration_ms = duration_ms
                existing_trace.total_tokens = trace.total_tokens
                existing_trace.total_cost = trace.total_cost
            else:
                # Create new trace
                trace_model = self.TraceModel(
                    id=trace.trace_id,
                    agent_name=trace.agent_name,
                    input_data=trace.input,
                    output=trace.output,
                    error=error_str,
                    session_id=trace.session_id,
                    user_id=trace.user_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    total_tokens=trace.total_tokens,
                    total_cost=trace.total_cost
                )
                session.add(trace_model)

            # Save all spans
            for span in trace.spans:
                self._save_span(session, span, trace.trace_id)

            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def _save_span(self, session: Session, span: Span, trace_id: str) -> None:
        """
        Save a span to the database.

        Args:
            session: Database session
            span: Span object to save
            trace_id: Parent trace ID
        """
        # Convert timestamps
        start_time = self._convert_timestamp(span.start_time)
        end_time = self._convert_timestamp(span.end_time)
        duration_ms = int(span.duration * 1000) if span.duration else None

        # Serialize tool_args
        tool_args_json = None
        if hasattr(span, 'tool_args') and span.tool_args:
            tool_args_json = json.dumps(span.tool_args)

        # Check if span exists
        existing_span = session.query(self.SpanModel).filter_by(id=span.span_id).first()

        if existing_span:
            # Update existing span
            existing_span.trace_id = trace_id
            existing_span.parent_span_id = span.parent_id
            existing_span.span_type = span.span_type.value
            existing_span.name = span.name
            existing_span.start_time = start_time
            existing_span.end_time = end_time
            existing_span.duration_ms = duration_ms
            existing_span.llm_prompt = getattr(span, 'llm_prompt', None)
            existing_span.llm_response = getattr(span, 'llm_response', None)
            existing_span.llm_model = getattr(span, 'llm_model', None)
            existing_span.prompt_tokens = getattr(span, 'prompt_tokens', None)
            existing_span.completion_tokens = getattr(span, 'completion_tokens', None)
            existing_span.cost = getattr(span, 'cost', None)
            existing_span.tool_name = getattr(span, 'tool_name', None)
            existing_span.tool_args = tool_args_json
            existing_span.tool_output = getattr(span, 'tool_output', None)
        else:
            # Create new span
            span_model = self.SpanModel(
                id=span.span_id,
                trace_id=trace_id,
                parent_span_id=span.parent_id,
                span_type=span.span_type.value,
                name=span.name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                llm_prompt=getattr(span, 'llm_prompt', None),
                llm_response=getattr(span, 'llm_response', None),
                llm_model=getattr(span, 'llm_model', None),
                prompt_tokens=getattr(span, 'prompt_tokens', None),
                completion_tokens=getattr(span, 'completion_tokens', None),
                cost=getattr(span, 'cost', None),
                tool_name=getattr(span, 'tool_name', None),
                tool_args=tool_args_json,
                tool_output=getattr(span, 'tool_output', None)
            )
            session.add(span_model)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID with all its spans.

        Args:
            trace_id: Trace identifier

        Returns:
            Trace object or None if not found
        """
        session = self._get_session()
        try:
            trace_model = session.query(self.TraceModel).filter_by(id=trace_id).first()

            if not trace_model:
                return None

            # Build Trace object
            trace = Trace(
                trace_id=trace_model.id,
                agent_name=trace_model.agent_name,
                input_data=trace_model.input_data or "",
                session_id=trace_model.session_id,
                user_id=trace_model.user_id
            )

            trace.output = trace_model.output
            trace.error = trace_model.error
            trace.start_time = trace_model.start_time.timestamp() if trace_model.start_time else None
            trace.end_time = trace_model.end_time.timestamp() if trace_model.end_time else None
            trace.duration = trace_model.duration_ms / 1000.0 if trace_model.duration_ms else None
            trace.total_tokens = trace_model.total_tokens or 0
            trace.total_cost = trace_model.total_cost or 0.0

            # Add spans
            for span_model in trace_model.spans:
                span = self._model_to_span(span_model)
                trace.spans.append(span)

            return trace
        finally:
            session.close()

    def list_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Trace]:
        """
        List traces with optional filtering.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            agent_name: Filter by agent name
            limit: Maximum number of traces to return

        Returns:
            List of Trace objects
        """
        session = self._get_session()
        try:
            query = session.query(self.TraceModel)

            if session_id:
                query = query.filter_by(session_id=session_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if agent_name:
                query = query.filter_by(agent_name=agent_name)

            query = query.order_by(self.TraceModel.start_time.desc()).limit(limit)

            traces = []
            for trace_model in query.all():
                # Don't load spans for list (performance)
                trace = Trace(
                    trace_id=trace_model.id,
                    agent_name=trace_model.agent_name,
                    input_data=trace_model.input_data or "",
                    session_id=trace_model.session_id,
                    user_id=trace_model.user_id
                )

                trace.output = trace_model.output
                trace.error = trace_model.error
                trace.start_time = trace_model.start_time.timestamp() if trace_model.start_time else None
                trace.end_time = trace_model.end_time.timestamp() if trace_model.end_time else None
                trace.duration = trace_model.duration_ms / 1000.0 if trace_model.duration_ms else None
                trace.total_tokens = trace_model.total_tokens or 0
                trace.total_cost = trace_model.total_cost or 0.0

                traces.append(trace)

            return traces
        finally:
            session.close()

    def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace and all its spans.

        Args:
            trace_id: Trace ID to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        session = self._get_session()
        try:
            trace = session.query(self.TraceModel).filter_by(id=trace_id).first()
            if trace:
                session.delete(trace)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def clear_all(self) -> int:
        """
        Clear all traces and spans from the database.

        Returns:
            int: Number of traces deleted
        """
        session = self._get_session()
        try:
            count = session.query(self.TraceModel).count()
            session.query(self.SpanModel).delete()
            session.query(self.TraceModel).delete()
            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()

    def _convert_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Convert various timestamp formats to datetime."""
        if timestamp is None:
            return None

        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)

        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except:
                return None

        return None

    def _model_to_span(self, span_model) -> Span:
        """Convert database model to Span object."""
        span = Span(
            span_id=span_model.id,
            trace_id=span_model.trace_id,
            span_type=SpanType(span_model.span_type),
            name=span_model.name,
            parent_span_id=span_model.parent_span_id
        )

        span.start_time = span_model.start_time.timestamp() if span_model.start_time else None
        span.end_time = span_model.end_time.timestamp() if span_model.end_time else None
        span.duration = span_model.duration_ms / 1000.0 if span_model.duration_ms else None

        # Add optional fields
        if span_model.llm_prompt:
            span.llm_prompt = span_model.llm_prompt
        if span_model.llm_response:
            span.llm_response = span_model.llm_response
        if span_model.llm_model:
            span.llm_model = span_model.llm_model
        if span_model.prompt_tokens is not None:
            span.prompt_tokens = span_model.prompt_tokens
        if span_model.completion_tokens is not None:
            span.completion_tokens = span_model.completion_tokens
        if span_model.cost is not None:
            span.cost = float(span_model.cost)
        if span_model.tool_name:
            span.tool_name = span_model.tool_name
        if span_model.tool_args:
            span.tool_args = json.loads(span_model.tool_args)
        if span_model.tool_output:
            span.tool_output = span_model.tool_output

        return span

    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()

    def __del__(self):
        """Cleanup: close connection on deletion."""
        try:
            self.close()
        except:
            pass


# Convenience aliases
PostgreSQLTracingStore = DatabaseTracingStore
SQLiteTracingStore = DatabaseTracingStore
