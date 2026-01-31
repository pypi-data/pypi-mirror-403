# metapg.pool

**High-performance PostgreSQL connection pool with async and sync support**

`metapg.pool` provides async and sync PostgreSQL connection pooling built on psycopg3. It supports multiple databases, smart connection reuse, and context-aware operations.

## Installation

```bash
pip install metapg.pool
```

## Quick Start

```python
from metapg.pool import init_pool, cursor, transaction, events

# Initialize pool
init_pool(dsn="postgresql://localhost/mydb")

# Async usage
async with cursor() as cur:
    await cur.execute("SELECT * FROM users")
    users = await cur.fetchall()

# Sync usage (same interface!)
with cursor() as cur:
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
```

## Features

- **Smart Cursor** - Same API for both async and sync operations
- **Smart Transaction** - Nested transaction support with automatic savepoints
- **Events (LISTEN/NOTIFY)** - Pub/sub with dedicated connections
- **Multi-Database** - Manage multiple PostgreSQL databases with named pools
- **Context-Aware** - Smart connection reuse with contextvars
- **Zero-Config** - Works out of the box with sensible defaults

## Smart Cursor

The `cursor()` function returns a `SmartCursor` that automatically adapts to sync or async context:

```python
from metapg.pool import cursor

# Async
async with cursor() as cur:
    await cur.execute("SELECT * FROM users")
    users = await cur.fetchall()

# Sync
with cursor() as cur:
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
```

## Smart Transaction

The `transaction()` function returns a `SmartTransaction` for atomic operations:

```python
from metapg.pool import transaction, cursor

# Async
async with transaction():
    async with cursor() as cur:
        await cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
        await cur.execute("INSERT INTO logs (msg) VALUES (%s)", ("User created",))

# Sync
with transaction():
    with cursor() as cur:
        cur.execute("INSERT INTO users (name) VALUES (%s)", ("Bob",))
```

## Events (LISTEN/NOTIFY)

The `events()` context manager provides pub/sub functionality with PostgreSQL's LISTEN/NOTIFY:

```python
from metapg.pool import events

# Async
async with events() as ev:
    await ev.listen("orders", "inventory")
    await ev.notify("orders", "new_order:123")

    async for msg in ev:
        print(f"{msg.channel}: {msg.payload}")
        if should_stop:
            break

# Sync
with events() as ev:
    ev.listen("orders")
    ev.notify("orders", "new_order:456")

    for msg in ev:
        print(f"{msg.channel}: {msg.payload}")
        if should_stop:
            break
```

### Events API

- `ev.listen(*channels)` - Subscribe to channels
- `ev.unlisten(*channels)` - Unsubscribe from channels
- `ev.notify(channel, payload)` - Send a notification
- Iterate `ev` to receive messages

## Pool Management

```python
from metapg.pool import init_pool, get_pool, close_pool, close_all_pools

# Initialize pools (creates both async and sync pools)
init_pool(
    dsn="postgresql://user:pass@host:port/dbname",
    db_name="default",
    min_size=1,
    max_size=20,
    application_name="my-app"
)

# Get existing pool
pool = get_pool("default")

# Close specific pool
await close_pool("default")

# Close all pools
await close_all_pools()
```

## Multi-Database Support

```python
from metapg.pool import init_pool, cursor

# Initialize multiple databases
init_pool(dsn="postgresql://localhost/app", db_name="app")
init_pool(dsn="postgresql://localhost/analytics", db_name="analytics")

# Query different databases
async with cursor("app") as cur:
    await cur.execute("SELECT * FROM users")

async with cursor("analytics") as cur:
    await cur.execute("SELECT * FROM events")
```

## Environment Variables

- `DATABASE_URL` - Default database connection string
- `DATABASE_URL_{NAME}` - Connection string for named database (e.g., `DATABASE_URL_ANALYTICS`)
- `METAPG_APPLICATION_NAME` - Application name for connections
- `PGAPPNAME` - PostgreSQL standard application name (fallback)

## License

MIT License

## Part of metapg

This package is part of the [metapg](https://github.com/metapg/metapg) project for PostgreSQL operations.
