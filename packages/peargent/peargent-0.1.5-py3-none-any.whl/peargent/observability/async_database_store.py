"""
Async database stores with background queue for non-blocking operations.

Provides async write operations while maintaining sync read API.
"""

from typing import List, Optional, Any
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import atexit

from peargent.observability.database_store import DatabaseTracingStore
from peargent.observability.trace import Trace


class AsyncDatabaseTracingStore(DatabaseTracingStore):
    """
    Async-enabled database store with background queue for writes.

    Writes (save_trace, delete_trace, clear_all) happen asynchronously in a background thread.
    Reads (get_trace, list_traces) are still synchronous for consistency.

    Args:
        connection_string: Database connection string
        traces_table: Name of the traces table (default: "traces")
        spans_table: Name of the spans table (default: "spans")
        auto_migrate: Automatically create schema if it doesn't exist (default: True)
        max_queue_size: Maximum number of pending operations (default: 1000)
        num_workers: Number of background worker threads (default: 2)
    """

    def __init__(
        self,
        connection_string: str,
        traces_table: str = "traces",
        spans_table: str = "spans",
        auto_migrate: bool = True,
        max_queue_size: int = 1000,
        num_workers: int = 2
    ):
        # Initialize parent
        super().__init__(connection_string, traces_table, spans_table, auto_migrate)

        # Create queue for async operations
        self._write_queue = queue.Queue(maxsize=max_queue_size)
        self._executor = ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix="db-writer")
        self._shutdown = False

        # Start worker threads
        for _ in range(num_workers):
            self._executor.submit(self._worker)

        # Register cleanup on exit
        atexit.register(self.shutdown)

    def _worker(self):
        """Background worker that processes write operations."""
        while not self._shutdown:
            try:
                # Get operation from queue with timeout
                operation = self._write_queue.get(timeout=1.0)

                if operation is None:  # Shutdown signal
                    break

                op_type, args, kwargs, callback = operation

                try:
                    # Execute the operation
                    if op_type == "save_trace":
                        result = self._sync_save_trace(*args, **kwargs)
                    elif op_type == "delete_trace":
                        result = self._sync_delete_trace(*args, **kwargs)
                    elif op_type == "clear_all":
                        result = self._sync_clear_all(*args, **kwargs)
                    else:
                        result = None

                    # Call callback if provided
                    if callback:
                        callback(result, None)

                except Exception as e:
                    # Call error callback if provided
                    if callback:
                        callback(None, e)

                finally:
                    self._write_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                # Log error but keep worker running
                print(f"Worker error: {e}")

    def _sync_save_trace(self, trace: Trace) -> None:
        """Synchronous version of save_trace for background execution."""
        return super().save_trace(trace)

    def _sync_delete_trace(self, trace_id: str) -> bool:
        """Synchronous version of delete_trace for background execution."""
        return super().delete_trace(trace_id)

    def _sync_clear_all(self) -> int:
        """Synchronous version of clear_all for background execution."""
        return super().clear_all()

    def save_trace(self, trace: Trace, callback: Optional[callable] = None) -> None:
        """
        Save trace asynchronously in background thread.

        Args:
            trace: Trace object to save
            callback: Optional callback(result, error) called when done
        """
        if self._shutdown:
            raise RuntimeError("Store is shutting down, cannot queue new operations")

        try:
            self._write_queue.put_nowait(("save_trace", (trace,), {}, callback))
        except queue.Full:
            # Queue is full, fall back to synchronous write
            print("Warning: Write queue full, performing synchronous write")
            self._sync_save_trace(trace)

    def delete_trace(self, trace_id: str, callback: Optional[callable] = None) -> bool:
        """
        Delete trace asynchronously in background thread.

        Args:
            trace_id: Trace ID to delete
            callback: Optional callback(result, error) called when done

        Returns:
            True (operation queued, actual result in callback)
        """
        if self._shutdown:
            raise RuntimeError("Store is shutting down, cannot queue new operations")

        try:
            self._write_queue.put_nowait(("delete_trace", (trace_id,), {}, callback))
            return True
        except queue.Full:
            print("Warning: Write queue full, performing synchronous delete")
            return self._sync_delete_trace(trace_id)

    def clear_all(self, callback: Optional[callable] = None) -> int:
        """
        Clear all traces asynchronously in background thread.

        Args:
            callback: Optional callback(result, error) called when done

        Returns:
            0 (operation queued, actual result in callback)
        """
        if self._shutdown:
            raise RuntimeError("Store is shutting down, cannot queue new operations")

        try:
            self._write_queue.put_nowait(("clear_all", (), {}, callback))
            return 0
        except queue.Full:
            print("Warning: Write queue full, performing synchronous clear")
            return self._sync_clear_all()

    def flush(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all pending write operations to complete.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if all operations completed, False if timeout
        """
        try:
            self._write_queue.join()
            return True
        except:
            return False

    def shutdown(self, timeout: float = 5.0):
        """
        Shutdown the async store gracefully.

        Args:
            timeout: Maximum time to wait for pending operations
        """
        if self._shutdown:
            return

        self._shutdown = True

        # Wait for queue to empty
        try:
            self._write_queue.join()
        except:
            pass

        # Send shutdown signals
        for _ in range(self._executor._max_workers):
            try:
                self._write_queue.put_nowait(None)
            except:
                pass

        # Shutdown executor
        self._executor.shutdown(wait=True)

        # Close database connection
        super().close()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown(timeout=2.0)
        except:
            pass


# Convenience aliases
AsyncPostgreSQLTracingStore = AsyncDatabaseTracingStore
AsyncSQLiteTracingStore = AsyncDatabaseTracingStore
