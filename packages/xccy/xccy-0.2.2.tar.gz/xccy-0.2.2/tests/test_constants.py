"""Tests for constants and network configuration."""

import pytest

from xccy.constants import (
    WAD,
    RAY,
    Q96,
    MIN_TICK,
    MAX_TICK,
    DEFAULT_BACKEND_URL,
    POLYGON_CONFIG,
    NETWORKS,
    get_network_config,
    load_abi,
    ZERO_ADDRESS,
)


class TestMathConstants:
    """Tests for mathematical constants."""
    
    def test_wad(self):
        """WAD should be 10^18."""
        assert WAD == 10**18
    
    def test_ray(self):
        """RAY should be 10^27."""
        assert RAY == 10**27
    
    def test_q96(self):
        """Q96 should be 2^96."""
        assert Q96 == 2**96
    
    def test_tick_bounds(self):
        """Tick bounds should be valid."""
        assert MIN_TICK < 0
        assert MAX_TICK > 0
        assert MIN_TICK == -MAX_TICK  # Symmetric


class TestNetworkConfig:
    """Tests for network configuration."""
    
    def test_polygon_config_exists(self):
        """Polygon config should be defined."""
        assert POLYGON_CONFIG is not None
        assert POLYGON_CONFIG.chain_id == 137
        assert POLYGON_CONFIG.name == "Polygon"
    
    def test_polygon_addresses(self):
        """Polygon contract addresses should be valid."""
        assert POLYGON_CONFIG.collateral_engine.startswith("0x")
        assert len(POLYGON_CONFIG.collateral_engine) == 42
        
        assert POLYGON_CONFIG.vamm_manager.startswith("0x")
        assert POLYGON_CONFIG.oracle_hub.startswith("0x")
        assert POLYGON_CONFIG.apr_oracle.startswith("0x")
    
    def test_multicall_address(self):
        """Multicall3 should be standard address."""
        # Standard Multicall3 address
        assert POLYGON_CONFIG.multicall3 == "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    def test_networks_registry(self):
        """Networks should be registered by chain ID."""
        assert 137 in NETWORKS
        assert NETWORKS[137] == POLYGON_CONFIG
    
    def test_get_network_by_chain_id(self):
        """Get network config by chain ID."""
        config = get_network_config(137)
        assert config == POLYGON_CONFIG
    
    def test_get_network_by_name(self):
        """Get network config by name."""
        config = get_network_config("polygon")
        assert config == POLYGON_CONFIG
        
        config = get_network_config("matic")
        assert config == POLYGON_CONFIG
    
    def test_get_network_invalid_chain_id(self):
        """Invalid chain ID should raise."""
        with pytest.raises(ValueError, match="Unsupported chain ID"):
            get_network_config(999)
    
    def test_get_network_invalid_name(self):
        """Invalid network name should raise."""
        with pytest.raises(ValueError, match="Unsupported network"):
            get_network_config("unknown_network")


class TestABILoading:
    """Tests for ABI loading."""
    
    def test_load_collateral_engine_abi(self):
        """Load CollateralEngine ABI."""
        abi = load_abi("CollateralEngine")
        assert isinstance(abi, list)
        assert len(abi) > 0
    
    def test_load_vamm_manager_abi(self):
        """Load VAMMManager ABI."""
        abi = load_abi("VAMMManager")
        assert isinstance(abi, list)
        assert len(abi) > 0
    
    def test_load_erc20_abi(self):
        """Load ERC20 ABI."""
        abi = load_abi("ERC20")
        assert isinstance(abi, list)
        
        # Should have standard ERC20 functions
        function_names = [item.get("name") for item in abi if item.get("type") == "function"]
        assert "transfer" in function_names or "Transfer" in function_names
    
    def test_load_unknown_abi(self):
        """Unknown ABI should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_abi("NonExistentContract")
    
    def test_abi_caching(self):
        """ABI loading should cache results."""
        abi1 = load_abi("CollateralEngine")
        abi2 = load_abi("CollateralEngine")
        
        # Should be same object (cached)
        assert abi1 is abi2


class TestOtherConstants:
    """Tests for other constants."""
    
    def test_default_backend_url(self):
        """Default backend URL should be set."""
        assert DEFAULT_BACKEND_URL == "https://api.xccy.finance"
    
    def test_zero_address(self):
        """Zero address should be valid."""
        assert ZERO_ADDRESS == "0x0000000000000000000000000000000000000000"
        assert len(ZERO_ADDRESS) == 42
