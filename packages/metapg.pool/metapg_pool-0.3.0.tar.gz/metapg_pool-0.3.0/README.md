# metapg.pool

**High-performance PostgreSQL connection pool with async and sync support**

`metapg.pool` provides async and sync PostgreSQL connection pooling built on psycopg3. It supports multiple databases, smart connection reuse, and context-aware operations.

## Installation

```bash
pip install metapg.pool
```

## Quick Start

```python
import metapg.pool

# Initialize pool
metapg.pool.init_pool(dsn="postgresql://localhost/mydb", db_name="main")

# Async usage
async with metapg.pool.cursor() as cur:
    await cur.execute("SELECT * FROM users")
    users = await cur.fetchall()

# Sync usage (same interface!)
with metapg.pool.cursor() as cur:
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

# Transactions
async with metapg.pool.transaction():
    async with metapg.pool.cursor() as cur:
        await cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
```

## Features

- **🎯 Smart Interface** - Same API for both async and sync operations
- **⚡ High Performance** - Built on psycopg3 with efficient connection pooling
- **🎛️ Multi-Database** - Manage multiple PostgreSQL databases with named pools
- **🧠 Context-Aware** - Smart connection reuse with contextvars
- **🔒 Thread-Safe** - Safe for use in threaded applications
- **⚙️ Zero-Config** - Works out of the box with sensible defaults

## API Reference

### Pool Management

```python
# Initialize pools (creates both async and sync pools)
metapg.pool.init_pool(
    dsn="postgresql://user:pass@host:port/dbname",
    db_name="default",
    min_size=1,
    max_size=20
)

# Get existing pool
pool = metapg.pool.get_pool("default")

# Close specific pool
await metapg.pool.close_pool("default")

# Close all pools
await metapg.pool.close_all_pools()
```

### Database Operations

```python
# Smart cursor (adapts to sync/async context)
async with metapg.pool.cursor("db_name") as cur:
    await cur.execute("SELECT * FROM table")
    results = await cur.fetchall()

# Direct connection access
async with metapg.pool.connection("db_name") as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1")

# Transactions
async with metapg.pool.transaction("db_name"):
    async with metapg.pool.cursor() as cur:
        await cur.execute("INSERT INTO table VALUES (%s)", (value,))
```

## Environment Variables

- `DATABASE_URL` - Default database connection string
- `DATABASE_URL_{NAME}` - Connection string for named database (e.g., `DATABASE_URL_ANALYTICS`)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Part of metapg

This package is part of the [metapg](https://github.com/metapg/metapg) metapackage for PostgreSQL operations.