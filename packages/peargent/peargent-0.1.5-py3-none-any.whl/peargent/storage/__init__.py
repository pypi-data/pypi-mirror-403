"""
Unified storage module for Peargent.

Provides storage type configurations and implementations that work across history and tracing.
All storage types and stores can be imported from this single module.
"""

# Storage type configuration classes
from .storage_types import (
    StorageType,
    InMemory,
    File,
    Sqlite,
    Postgresql,
    Redis,
)

# Base classes for storage implementations
from .base import Message, Thread, HistoryStore, FunctionalHistoryStore

# Concrete storage implementations
from .session_buffer import InMemoryHistoryStore
from .file import FileHistoryStore

# Try to export SQL-based stores
try:
    from .postgresql import PostgreSQLHistoryStore
    __all_sql__ = ['PostgreSQLHistoryStore']
except ImportError:
    PostgreSQLHistoryStore = None
    __all_sql__ = []

try:
    from .sqlite import SQLiteHistoryStore
    __all_sql__ += ['SQLiteHistoryStore']
except ImportError:
    SQLiteHistoryStore = None

# Try to export Redis store
try:
    from .redis import RedisHistoryStore
    __all_redis__ = ['RedisHistoryStore']
except ImportError:
    RedisHistoryStore = None
    __all_redis__ = []

__all__ = [
    # Storage type configurations
    'StorageType',
    'InMemory',
    'File',
    'Sqlite',
    'Postgresql',
    'Redis',
    # Base classes
    'Message',
    'Thread',
    'HistoryStore',
    'FunctionalHistoryStore',
    # Concrete implementations
    'InMemoryHistoryStore',
    'FileHistoryStore',
] + __all_sql__ + __all_redis__
