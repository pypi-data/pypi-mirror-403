"""Unit tests for metapg.pool initialization - no database connection required."""

import os
from unittest.mock import Mock, patch

import pytest

# Import testing utilities from metapg.dev
try:
    from metapg.dev.testing import patch_connection
except ImportError:
    # Fallback to local mocks if dev package not available
    patch_connection = patch

from metapg.pool import close_all_pools, init_pool

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
async def cleanup_pools():
    """Clean up pools after each test."""
    yield
    await close_all_pools()


def test_pool_initialization_returns_pool():
    """Test that pool initialization returns a pool object without connecting."""
    with patch("metapg.pool.pool.AsyncConnectionPool") as mock_async_pool:

        mock_async_pool.return_value = Mock()

        pool = init_pool(
            dsn="postgresql://test:test@localhost:5432/test",
            db_name="test_pool",
            min_size=1,
            max_size=5,
        )

        assert pool is not None
        # Verify the pool was created with correct parameters
        mock_async_pool.assert_called_once()


def test_pool_initialization_with_environment_variables():
    """Test pool initialization using environment variables."""
    with (
        patch.dict(
            os.environ,
            {"DATABASE_URL_TEST": "postgresql://test:test@localhost:5432/test"},
        ),
        patch("metapg.pool.pool.AsyncConnectionPool") as mock_async_pool,
    ):

        mock_async_pool.return_value = Mock()

        pool = init_pool(db_name="test")

        assert pool is not None
        mock_async_pool.assert_called_once()


def test_pool_initialization_parameters():
    """Test that pool initialization uses correct parameters."""
    with patch("metapg.pool.pool.AsyncConnectionPool") as mock_async_pool:

        mock_async_pool.return_value = Mock()

        dsn = "postgresql://user:pass@host:5432/db"
        min_size = 2
        max_size = 10

        init_pool(
            dsn=dsn,
            db_name="test_params",
            min_size=min_size,
            max_size=max_size,
        )

        # Check that the async pool was called with correct parameters
        async_call = mock_async_pool.call_args
        assert "host=host port=5432 dbname=db user=user password=pass" in str(
            async_call
        )
