"""Smart cursor and transaction for sync/async contexts."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

from .pool import (
    _async_connection,
    _get_async_context_vars,
    _get_sync_context_vars,
    _sync_connection,
)


@asynccontextmanager
async def _async_cursor(db_name: str = "default") -> AsyncGenerator[Any, None]:
    """Get an async database cursor with automatic cleanup."""
    _, cursor_var = _get_async_context_vars(db_name)

    existing_cursor = cursor_var.get()
    if existing_cursor is not None:
        yield existing_cursor
        return

    async with _async_connection(db_name) as conn, conn.cursor() as cur:
        token = cursor_var.set(cur)
        try:
            yield cur
        finally:
            cursor_var.reset(token)


@contextmanager
def _sync_cursor(db_name: str = "default") -> Generator[Any, None, None]:
    """Get a sync database cursor with automatic cleanup."""
    _, cursor_var = _get_sync_context_vars(db_name)

    existing_cursor = cursor_var.get()
    if existing_cursor is not None:
        yield existing_cursor
        return

    with _sync_connection(db_name) as conn, conn.cursor() as cur:
        token = cursor_var.set(cur)
        try:
            yield cur
        finally:
            cursor_var.reset(token)


@asynccontextmanager
async def _async_transaction(db_name: str = "default") -> AsyncGenerator[None, None]:
    """Execute within an async database transaction."""
    async with _async_connection(db_name) as conn, conn.transaction():
        yield


@contextmanager
def _sync_transaction(db_name: str = "default") -> Generator[None, None, None]:
    """Execute within a sync database transaction."""
    with _sync_connection(db_name) as conn, conn.transaction():
        yield


class SmartCursor:
    """A cursor that works with both sync and async contexts."""

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name

    async def __aenter__(self):
        self._async_cursor_cm = _async_cursor(self.db_name)
        self._cursor = await self._async_cursor_cm.__aenter__()
        return self._cursor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._async_cursor_cm.__aexit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        self._sync_cursor_cm = _sync_cursor(self.db_name)
        self._cursor = self._sync_cursor_cm.__enter__()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._sync_cursor_cm.__exit__(exc_type, exc_val, exc_tb)


class SmartTransaction:
    """A transaction that works with both sync and async contexts."""

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name

    async def __aenter__(self):
        self._async_tx_cm = _async_transaction(self.db_name)
        return await self._async_tx_cm.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._async_tx_cm.__aexit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        self._sync_tx_cm = _sync_transaction(self.db_name)
        return self._sync_tx_cm.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._sync_tx_cm.__exit__(exc_type, exc_val, exc_tb)


def cursor(db_name: str = "default") -> SmartCursor:
    """Get a smart cursor that works with both sync and async contexts."""
    return SmartCursor(db_name)


def transaction(db_name: str = "default") -> SmartTransaction:
    """Get a smart transaction that works with both sync and async contexts."""
    return SmartTransaction(db_name)
