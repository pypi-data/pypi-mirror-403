"""Pub/sub events for PostgreSQL LISTEN/NOTIFY."""

from psycopg import AsyncConnection, Connection
from psycopg.rows import dict_row

from .pool import _get_async_pool, _get_sync_pool


class Events:
    """Pub/sub events context for LISTEN/NOTIFY.

    Works with both sync and async contexts. Creates a dedicated connection
    (not from pool) with autocommit enabled for LISTEN/NOTIFY operations.

    Examples:
        # Async usage
        async with events() as ev:
            await ev.listen("orders", "inventory")
            await ev.notify("orders", "new_order:123")
            async for msg in ev:
                print(f"{msg.channel}: {msg.payload}")

        # Sync usage
        with events() as ev:
            ev.listen("orders")
            ev.notify("orders", "new_order:123")
            for msg in ev:
                print(f"{msg.channel}: {msg.payload}")
    """

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        self._channels: set[str] = set()
        self._conn = None
        self._is_async = False

    # Async context manager

    async def __aenter__(self) -> "Events":
        self._is_async = True
        pool = _get_async_pool(self.db_name)
        if pool.closed:
            await pool.open()
        self._conn = await AsyncConnection.connect(
            pool.conninfo,
            autocommit=True,
            row_factory=dict_row,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for channel in self._channels:
            await self._conn.execute(f"UNLISTEN {channel}")
        await self._conn.close()
        self._conn = None

    # Sync context manager

    def __enter__(self) -> "Events":
        self._is_async = False
        pool = _get_sync_pool(self.db_name)
        self._conn = Connection.connect(
            pool.conninfo,
            autocommit=True,
            row_factory=dict_row,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for channel in self._channels:
            self._conn.execute(f"UNLISTEN {channel}")
        self._conn.close()
        self._conn = None

    # Listen methods

    async def _async_listen(self, *channels: str) -> None:
        for channel in channels:
            if channel not in self._channels:
                await self._conn.execute(f"LISTEN {channel}")
                self._channels.add(channel)

    def _sync_listen(self, *channels: str) -> None:
        for channel in channels:
            if channel not in self._channels:
                self._conn.execute(f"LISTEN {channel}")
                self._channels.add(channel)

    def listen(self, *channels: str):
        """Subscribe to one or more channels."""
        if self._is_async:
            return self._async_listen(*channels)
        self._sync_listen(*channels)

    # Unlisten methods

    async def _async_unlisten(self, *channels: str) -> None:
        for channel in channels:
            if channel in self._channels:
                await self._conn.execute(f"UNLISTEN {channel}")
                self._channels.discard(channel)

    def _sync_unlisten(self, *channels: str) -> None:
        for channel in channels:
            if channel in self._channels:
                self._conn.execute(f"UNLISTEN {channel}")
                self._channels.discard(channel)

    def unlisten(self, *channels: str):
        """Unsubscribe from one or more channels."""
        if self._is_async:
            return self._async_unlisten(*channels)
        self._sync_unlisten(*channels)

    # Notify methods

    async def _async_notify(self, channel: str, payload: str = "") -> None:
        await self._conn.execute("SELECT pg_notify(%s, %s)", (channel, payload))

    def _sync_notify(self, channel: str, payload: str = "") -> None:
        self._conn.execute("SELECT pg_notify(%s, %s)", (channel, payload))

    def notify(self, channel: str, payload: str = ""):
        """Send a notification to a channel."""
        if self._is_async:
            return self._async_notify(channel, payload)
        self._sync_notify(channel, payload)

    # Iteration for receiving notifications

    def __aiter__(self):
        return self._conn.notifies().__aiter__()

    def __iter__(self):
        return self._conn.notifies().__iter__()


def events(db_name: str = "default") -> Events:
    """Create a pub/sub events context for LISTEN/NOTIFY.

    Args:
        db_name: Name of the database to connect to

    Returns:
        Events context manager
    """
    return Events(db_name)
