"""Pytest fixtures for XCCY SDK tests."""

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from xccy.types import AccountId, PoolKey


@pytest.fixture
def mock_web3():
    """Mock web3 instance for unit tests."""
    mock = Mock()
    mock.eth.chain_id = 137  # Polygon
    mock.eth.get_block.return_value = {"timestamp": 1704067200}
    mock.eth.gas_price = 30 * 10**9
    mock.is_connected.return_value = True
    return mock


@pytest.fixture
def sample_account() -> AccountId:
    """Sample account for testing."""
    return AccountId(
        owner="0x1234567890123456789012345678901234567890",
        account_id=0,
        isolated_margin_token=None,
    )


@pytest.fixture
def sample_pool_key() -> PoolKey:
    """Sample pool key for testing."""
    return PoolKey(
        underlying_asset="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # USDC
        compound_token="0x625E7708f30cA75bfd92586e17077590C60eb4cD",  # aUSDC
        term_start_timestamp_wad=1704067200 * 10**18,
        term_end_timestamp_wad=1735689600 * 10**18,
        fee_wad=int(0.003 * 10**18),
        tick_spacing=60,
    )


@pytest.fixture
def mock_backend():
    """Mock backend API client."""
    mock = AsyncMock()
    mock.get_pools.return_value = []
    mock.get_positions.return_value = []
    return mock
