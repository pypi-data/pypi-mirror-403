"""
Token constants for supported networks.

This module provides well-known token addresses for each supported chain,
making it easy to reference tokens without hardcoding addresses.

Example:
    >>> from xccy.tokens import PolygonTokens
    >>> 
    >>> # Use USDC as collateral
    >>> client.margin.deposit(account, PolygonTokens.USDC, 1000 * 10**6)
    >>> 
    >>> # Build pool key with yield-bearing token
    >>> pool = client.pool.build_pool_key(
    ...     underlying=PolygonTokens.USDC,
    ...     compound_token=PolygonTokens.A_USDC,
    ...     ...
    ... )
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TokenInfo:
    """
    Information about a token.
    
    Attributes:
        address: Contract address (checksummed).
        symbol: Token symbol (e.g., "USDC").
        decimals: Number of decimals.
        name: Full token name.
    """
    
    address: str
    symbol: str
    decimals: int
    name: str = ""
    
    def __str__(self) -> str:
        return self.address


class PolygonTokens:
    """
    Well-known token addresses on Polygon mainnet (chain ID 137).
    
    Includes stablecoins, yield-bearing tokens (aTokens), and ETH variants.
    
    Example:
        >>> from xccy.tokens import PolygonTokens
        >>> 
        >>> # Access address directly
        >>> usdc_address = PolygonTokens.USDC  # "0x3c499c..."
        >>> 
        >>> # Or get full token info
        >>> usdc = PolygonTokens.get_info("USDC")
        >>> print(usdc.decimals)  # 6
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Stablecoins
    # ═══════════════════════════════════════════════════════════════════════════
    
    USDC: str = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
    """Native USDC on Polygon (6 decimals)."""
    
    USDC_E: str = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    """Bridged USDC.e on Polygon (6 decimals)."""
    
    USDT: str = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
    """Tether USD on Polygon (6 decimals)."""
    
    DAI: str = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
    """DAI Stablecoin on Polygon (18 decimals)."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Aave v3 aTokens (Yield-bearing)
    # ═══════════════════════════════════════════════════════════════════════════
    
    A_USDC: str = "0x625E7708f30cA75bfd92586e17077590C60eb4cD"
    """Aave v3 aUSDC (interest-bearing USDC)."""
    
    A_USDT: str = "0x6ab707Aca953eDAeFBc4fD23bA73294241490620"
    """Aave v3 aUSDT (interest-bearing USDT)."""
    
    A_DAI: str = "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE"
    """Aave v3 aDAI (interest-bearing DAI)."""
    
    A_WETH: str = "0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8"
    """Aave v3 aWETH (interest-bearing WETH)."""
    
    A_WMATIC: str = "0x6d80113e533a2C0fe82EaBD35f1875DcEA89Ea97"
    """Aave v3 aWMATIC (interest-bearing WMATIC)."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ETH Variants
    # ═══════════════════════════════════════════════════════════════════════════
    
    WETH: str = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    """Wrapped Ether on Polygon (18 decimals)."""
    
    WMATIC: str = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
    """Wrapped MATIC (18 decimals)."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Liquid Staking
    # ═══════════════════════════════════════════════════════════════════════════
    
    STMATIC: str = "0x3A58a54C066FdC0f2D55FC9C89F0415C92eBf3C4"
    """Lido stMATIC (18 decimals)."""
    
    WSTETH: str = "0x03b54A6e9a984069379fae1a4fC4dBAE93B3bCCD"
    """Wrapped stETH on Polygon (18 decimals)."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Token Info Registry
    # ═══════════════════════════════════════════════════════════════════════════
    
    _TOKEN_INFO: dict[str, TokenInfo] = {
        "USDC": TokenInfo("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "USDC", 6, "USD Coin"),
        "USDC.e": TokenInfo("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "USDC.e", 6, "Bridged USD Coin"),
        "USDT": TokenInfo("0xc2132D05D31c914a87C6611C10748AEb04B58e8F", "USDT", 6, "Tether USD"),
        "DAI": TokenInfo("0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "DAI", 18, "Dai Stablecoin"),
        "aUSDC": TokenInfo("0x625E7708f30cA75bfd92586e17077590C60eb4cD", "aUSDC", 6, "Aave Polygon USDC"),
        "aUSDT": TokenInfo("0x6ab707Aca953eDAeFBc4fD23bA73294241490620", "aUSDT", 6, "Aave Polygon USDT"),
        "aDAI": TokenInfo("0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE", "aDAI", 18, "Aave Polygon DAI"),
        "aWETH": TokenInfo("0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8", "aWETH", 18, "Aave Polygon WETH"),
        "aWMATIC": TokenInfo("0x6d80113e533a2C0fe82EaBD35f1875DcEA89Ea97", "aWMATIC", 18, "Aave Polygon WMATIC"),
        "WETH": TokenInfo("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", "WETH", 18, "Wrapped Ether"),
        "WMATIC": TokenInfo("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", "WMATIC", 18, "Wrapped Matic"),
        "stMATIC": TokenInfo("0x3A58a54C066FdC0f2D55FC9C89F0415C92eBf3C4", "stMATIC", 18, "Lido Staked MATIC"),
        "wstETH": TokenInfo("0x03b54A6e9a984069379fae1a4fC4dBAE93B3bCCD", "wstETH", 18, "Wrapped stETH"),
    }
    
    @classmethod
    def get_info(cls, symbol: str) -> Optional[TokenInfo]:
        """
        Get token information by symbol.
        
        Args:
            symbol: Token symbol (e.g., "USDC", "aUSDC").
            
        Returns:
            TokenInfo if found, None otherwise.
            
        Example:
            >>> info = PolygonTokens.get_info("USDC")
            >>> print(info.decimals)  # 6
        """
        return cls._TOKEN_INFO.get(symbol)
    
    @classmethod
    def get_decimals(cls, address: str) -> int:
        """
        Get decimals for a token by address.
        
        Args:
            address: Token contract address.
            
        Returns:
            Number of decimals, or 18 as default.
        """
        address_lower = address.lower()
        for info in cls._TOKEN_INFO.values():
            if info.address.lower() == address_lower:
                return info.decimals
        return 18  # Default to 18 decimals


# Alias for convenience
Tokens = PolygonTokens


# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions for decimal conversion
# ═══════════════════════════════════════════════════════════════════════════════

def parse_amount(amount: float | int, token: str | TokenInfo) -> int:
    """
    Convert human-readable amount to raw token units.
    
    Args:
        amount: Human-readable amount (e.g., 100.5 for 100.5 USDC).
        token: Token symbol (str) or TokenInfo object.
        
    Returns:
        Raw amount in smallest token units.
        
    Example:
        >>> from xccy.tokens import parse_amount
        >>> 
        >>> # 100 USDC (6 decimals) -> 100_000_000
        >>> raw = parse_amount(100, "USDC")
        >>> 
        >>> # 0.5 WETH (18 decimals) -> 500_000_000_000_000_000
        >>> raw = parse_amount(0.5, "WETH")
    """
    if isinstance(token, TokenInfo):
        decimals = token.decimals
    elif isinstance(token, str):
        # Try symbol first
        info = PolygonTokens.get_info(token)
        if info:
            decimals = info.decimals
        else:
            # Assume it's an address
            decimals = PolygonTokens.get_decimals(token)
    else:
        decimals = 18
    
    return int(amount * (10 ** decimals))


def format_amount(raw_amount: int, token: str | TokenInfo, precision: int = 4) -> str:
    """
    Convert raw token units to human-readable string.
    
    Args:
        raw_amount: Amount in smallest token units.
        token: Token symbol (str) or TokenInfo object.
        precision: Decimal places in output. Defaults to 4.
        
    Returns:
        Formatted string with appropriate decimals.
        
    Example:
        >>> from xccy.tokens import format_amount
        >>> 
        >>> # 100_000_000 USDC units -> "100.0000"
        >>> formatted = format_amount(100_000_000, "USDC")
        >>> 
        >>> # -500_000_000_000_000_000 WETH -> "-0.5000"
        >>> formatted = format_amount(-500_000_000_000_000_000, "WETH")
    """
    if isinstance(token, TokenInfo):
        decimals = token.decimals
    elif isinstance(token, str):
        info = PolygonTokens.get_info(token)
        if info:
            decimals = info.decimals
        else:
            decimals = PolygonTokens.get_decimals(token)
    else:
        decimals = 18
    
    value = raw_amount / (10 ** decimals)
    return f"{value:.{precision}f}"


def get_decimals(token: str) -> int:
    """
    Get decimals for a token by symbol or address.
    
    Args:
        token: Token symbol (e.g., "USDC") or address.
        
    Returns:
        Number of decimals.
        
    Example:
        >>> from xccy.tokens import get_decimals
        >>> get_decimals("USDC")  # 6
        >>> get_decimals("WETH")  # 18
    """
    info = PolygonTokens.get_info(token)
    if info:
        return info.decimals
    return PolygonTokens.get_decimals(token)
