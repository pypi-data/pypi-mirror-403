"""Integration tests against Polygon mainnet (or Anvil fork).

These tests verify that the SDK correctly communicates with the deployed contracts.

Run with:
    POLYGON_RPC_URL="https://rpc.ankr.com/polygon/..." \
    XCCY_BACKEND_URL="http://localhost:8000" \
    pytest tests/test_integration.py -v

Or with Anvil fork:
    anvil --fork-url "https://rpc.ankr.com/polygon/..." --chain-id 137
    POLYGON_RPC_URL="http://localhost:8545" pytest tests/test_integration.py -v
"""

import pytest
import os
from decimal import Decimal

from xccy import XccyClient
from xccy.types import AccountId, PoolKey
from xccy.constants import POLYGON_CONFIG

# Configuration from environment
POLYGON_RPC = os.environ.get(
    "POLYGON_RPC_URL",
    "https://rpc.ankr.com/polygon/9459a7b0289d1177790c6d0e02b5d2c852d173cfae0ce30ba12b1e7ad3b73cc8"
)
BACKEND_URL = os.environ.get("XCCY_BACKEND_URL", "http://localhost:8000")

# Skip all tests if RPC connection fails
def can_connect_to_rpc():
    """Check if we can connect to the RPC."""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
        return w3.is_connected()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not can_connect_to_rpc(),
    reason=f"Cannot connect to Polygon RPC: {POLYGON_RPC}"
)


@pytest.fixture
def client():
    """Create client connected to Polygon with local backend."""
    return XccyClient(
        rpc_url=POLYGON_RPC,
        backend_url=BACKEND_URL,
    )


@pytest.fixture
def readonly_client():
    """Create read-only client (no private key)."""
    return XccyClient(
        rpc_url=POLYGON_RPC,
        backend_url=None,  # No backend for basic tests
    )


class TestClientConnection:
    """Tests for client connection and configuration."""
    
    def test_client_connects(self, readonly_client):
        """Client should connect to Polygon."""
        assert readonly_client.web3.is_connected()
    
    def test_chain_id_is_polygon(self, readonly_client):
        """Chain ID should be Polygon mainnet (137)."""
        assert readonly_client.config.chain_id == 137
    
    def test_contract_addresses_match_config(self, readonly_client):
        """Contract addresses should match POLYGON_CONFIG."""
        assert readonly_client.config.collateral_engine == POLYGON_CONFIG.collateral_engine
        assert readonly_client.config.vamm_manager == POLYGON_CONFIG.vamm_manager


class TestVAMMManagerIntegration:
    """Integration tests for VAMMManager contract calls."""
    
    def test_vamm_manager_contract_exists(self, readonly_client):
        """VAMMManager contract should exist at configured address."""
        code = readonly_client.web3.eth.get_code(readonly_client.config.vamm_manager)
        assert len(code) > 0, "No contract code at VAMMManager address"


class TestCollateralEngineIntegration:
    """Integration tests for CollateralEngine contract calls."""
    
    def test_collateral_engine_contract_exists(self, readonly_client):
        """CollateralEngine contract should exist at configured address."""
        code = readonly_client.web3.eth.get_code(readonly_client.config.collateral_engine)
        assert len(code) > 0, "No contract code at CollateralEngine address"


class TestOracleHubIntegration:
    """Integration tests for OracleHub contract."""
    
    def test_oracle_hub_contract_exists(self, readonly_client):
        """OracleHub contract should exist at configured address."""
        code = readonly_client.web3.eth.get_code(readonly_client.config.oracle_hub)
        assert len(code) > 0, "No contract code at OracleHub address"


