"""Integration tests for metapg.pool - requires database connection."""

import os

import pytest

# Import the pool package directly
from metapg.pool import close_all_pools, close_pool, cursor, init_pool, transaction

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def cleanup_pools():
    """Clean up pools after each test."""
    yield
    await close_all_pools()


@pytest.mark.asyncio
async def test_basic_cursor():
    """Test basic cursor functionality with database."""
    async with cursor() as cur:
        await cur.execute("SELECT 1 as test_value")
        result = await cur.fetchone()
        assert result["test_value"] == 1


@pytest.mark.asyncio
async def test_named_database():
    """Test using named database pools."""
    # Set up test environment
    os.environ["DATABASE_URL_ANALYTICS"] = os.getenv("DATABASE_URL")

    async with cursor("analytics") as cur:
        await cur.execute("SELECT 'analytics' as db_name")
        result = await cur.fetchone()
        assert result["db_name"] == "analytics"


@pytest.mark.asyncio
async def test_transaction():
    """Test transaction functionality with real database."""
    # Create a test table
    async with cursor() as cur:
        await cur.execute(
            """
            CREATE TEMP TABLE test_tx (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """,
        )

    # Test successful transaction
    async with transaction(), cursor() as cur:
        await cur.execute("INSERT INTO test_tx (value) VALUES (%s)", ("test",))

    # Verify data was committed
    async with cursor() as cur:
        await cur.execute("SELECT COUNT(*) as count FROM test_tx")
        result = await cur.fetchone()
        assert result["count"] == 1

    # Test rollback on exception
    with pytest.raises(Exception):
        async with transaction():
            async with cursor() as cur:
                await cur.execute(
                    "INSERT INTO test_tx (value) VALUES (%s)",
                    ("rollback",),
                )
                raise Exception("Test rollback")

    # Verify data was rolled back
    async with cursor() as cur:
        await cur.execute("SELECT COUNT(*) as count FROM test_tx")
        result = await cur.fetchone()
        assert result["count"] == 1  # Still only 1 record


@pytest.mark.asyncio
async def test_cursor_in_transaction():
    """Test cursor functionality within transaction with database."""
    # Create a test table
    async with cursor() as cur:
        await cur.execute(
            """
            CREATE TEMP TABLE test_atomic (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """,
        )

    # Test cursor within transaction
    async with transaction(), cursor() as cur:
        await cur.execute(
            "INSERT INTO test_atomic (value) VALUES (%s)",
            ("atomic_test",),
        )

    # Verify data was committed
    async with cursor() as cur:
        await cur.execute("SELECT COUNT(*) as count FROM test_atomic")
        result = await cur.fetchone()
        assert result["count"] == 1


@pytest.mark.asyncio
async def test_nested_cursors():
    """Test nested cursor usage with connection reuse and real queries."""
    async with cursor() as cur1:
        await cur1.execute("SELECT 1 as outer_value")
        outer_result = await cur1.fetchone()

        # Nested cursor should reuse the same connection
        async with cursor() as cur2:
            await cur2.execute("SELECT 2 as inner_value")
            inner_result = await cur2.fetchone()

            assert outer_result["outer_value"] == 1
            assert inner_result["inner_value"] == 2


@pytest.mark.asyncio
async def test_pool_initialization_with_real_connection():
    """Test explicit pool initialization with actual database connection."""
    pool = init_pool(
        dsn=os.getenv("DATABASE_URL"),
        db_name="test_pool",
        min_size=1,
        max_size=5,
    )

    assert pool is not None

    # Test using the initialized pool with real database
    async with cursor("test_pool") as cur:
        await cur.execute("SELECT 'initialized' as status")
        result = await cur.fetchone()
        assert result["status"] == "initialized"

    await close_pool("test_pool")
