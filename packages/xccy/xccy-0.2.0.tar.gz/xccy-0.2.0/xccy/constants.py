"""
Constants for XCCY Protocol.

This module contains network configurations, contract addresses,
and mathematical constants used throughout the SDK.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════════════════════════
# Mathematical Constants
# ═══════════════════════════════════════════════════════════════════════════════

WAD: int = 10**18
"""WAD precision (18 decimals). Used for most values in the protocol."""

RAY: int = 10**27
"""RAY precision (27 decimals). Used for APR/APY values."""

Q96: int = 2**96
"""Q96 fixed-point multiplier. Used in sqrt price calculations."""

Q128: int = 2**128
"""Q128 fixed-point multiplier. Used for fee/token growth accounting."""

# ═══════════════════════════════════════════════════════════════════════════════
# Tick Bounds
# ═══════════════════════════════════════════════════════════════════════════════

MIN_TICK: int = -69100
"""Minimum tick value. Corresponds to ~1000% annualized fixed rate."""

MAX_TICK: int = 69100
"""Maximum tick value. Corresponds to ~0.001% annualized fixed rate."""

MIN_SQRT_RATIO: int = 2503036416286949174936592462
"""Minimum sqrt price ratio (at MIN_TICK)."""

MAX_SQRT_RATIO: int = 2507794810551837817144115957740
"""Maximum sqrt price ratio (at MAX_TICK)."""

# ═══════════════════════════════════════════════════════════════════════════════
# Default Backend URL
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_BACKEND_URL: str = "https://api.xccy.finance"
"""Default backend API URL for historical data queries."""

# ═══════════════════════════════════════════════════════════════════════════════
# Network Configurations
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class NetworkConfig:
    """
    Network configuration containing contract addresses.
    
    Attributes:
        chain_id: EVM chain ID.
        name: Human-readable network name.
        collateral_engine: CollateralEngine proxy address.
        vamm_manager: VAMMManager proxy address.
        oracle_hub: OracleHub proxy address.
        apr_oracle: AprOracle proxy address.
        operator: Operator router address.
        multicall3: Multicall3 address (standard on most chains).
    """
    
    chain_id: int
    name: str
    collateral_engine: str
    vamm_manager: str
    oracle_hub: str
    apr_oracle: str
    operator: Optional[str] = None
    multicall3: str = "0xcA11bde05977b3631167028862bE2a173976CA11"


# Polygon Mainnet (Chain ID 137)
POLYGON_CONFIG = NetworkConfig(
    chain_id=137,
    name="Polygon",
    collateral_engine="0x23E2DD3bB6e35162eB48d473d540764d5902BAe5",  # checksummed
    vamm_manager="0xe8FE9b71355B1701036671AD3c8F6dF585eb7eBd",
    oracle_hub="0x7a5084DEc5Fd89Ee1079005cE9cEa094c2A66E8E",
    apr_oracle="0xA192144F89edC9fBB3D225856FaF284d9287EDb8",
    operator=None,  # To be deployed
    multicall3="0xcA11bde05977b3631167028862bE2a173976CA11",
)


# Network registry by chain ID
NETWORKS: dict[int, NetworkConfig] = {
    137: POLYGON_CONFIG,
}

# Network registry by name
NETWORKS_BY_NAME: dict[str, NetworkConfig] = {
    "polygon": POLYGON_CONFIG,
    "matic": POLYGON_CONFIG,
}


def get_network_config(chain_id_or_name: int | str) -> NetworkConfig:
    """
    Get network configuration by chain ID or name.
    
    Args:
        chain_id_or_name: Chain ID (int) or network name (str).
        
    Returns:
        NetworkConfig for the specified network.
        
    Raises:
        ValueError: If network is not supported.
        
    Example:
        >>> config = get_network_config(137)
        >>> print(config.name)  # "Polygon"
        >>> 
        >>> config = get_network_config("polygon")
        >>> print(config.chain_id)  # 137
    """
    if isinstance(chain_id_or_name, int):
        if chain_id_or_name not in NETWORKS:
            raise ValueError(f"Unsupported chain ID: {chain_id_or_name}")
        return NETWORKS[chain_id_or_name]
    else:
        name = chain_id_or_name.lower()
        if name not in NETWORKS_BY_NAME:
            raise ValueError(f"Unsupported network: {chain_id_or_name}")
        return NETWORKS_BY_NAME[name]


# ═══════════════════════════════════════════════════════════════════════════════
# ABI Loading
# ═══════════════════════════════════════════════════════════════════════════════

_ABI_DIR = Path(__file__).parent / "abi"
_ABI_CACHE: dict[str, list] = {}


def load_abi(contract_name: str) -> list:
    """
    Load ABI for a contract.
    
    Args:
        contract_name: Name of the contract (e.g., "CollateralEngine").
        
    Returns:
        ABI as a list of function/event definitions.
        
    Raises:
        FileNotFoundError: If ABI file doesn't exist.
        
    Example:
        >>> abi = load_abi("CollateralEngine")
        >>> print(len(abi))  # Number of ABI entries
    """
    if contract_name in _ABI_CACHE:
        return _ABI_CACHE[contract_name]
    
    abi_path = _ABI_DIR / f"{contract_name}.json"
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI not found: {abi_path}")
    
    with open(abi_path) as f:
        abi = json.load(f)
    
    _ABI_CACHE[contract_name] = abi
    return abi


# ═══════════════════════════════════════════════════════════════════════════════
# Zero Address
# ═══════════════════════════════════════════════════════════════════════════════

ZERO_ADDRESS: str = "0x0000000000000000000000000000000000000000"
"""The zero address, used for cross-margin mode (no isolated token)."""
