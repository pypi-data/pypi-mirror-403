"""
metapg.pool - Connection pool for PostgreSQL databases.

A high-performance async and sync connection pool built on psycopg3.
"""

from .config import DatabaseConfig
from .cursor import SmartCursor, SmartTransaction, cursor, transaction
from .events import Events, events
from .pool import (
    close_all_pools,
    close_pool,
    connection,
    get_pool,
    init_pool,
)

__version__ = "0.3.0"
__all__ = [
    # Pool management
    "init_pool",
    "get_pool",
    "close_pool",
    "close_all_pools",
    "connection",
    # Cursor and transaction
    "SmartCursor",
    "SmartTransaction",
    "cursor",
    "transaction",
    # Events (LISTEN/NOTIFY)
    "Events",
    "events",
    # Config
    "DatabaseConfig",
]
