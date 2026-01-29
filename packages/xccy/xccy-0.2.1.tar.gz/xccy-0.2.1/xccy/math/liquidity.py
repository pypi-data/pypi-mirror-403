"""
Liquidity math utilities for XCCY Protocol.

This module provides conversions between:
- Liquidity units (abstract units used in the VAMM)
- Notional amounts (real token values users understand)

In the IRS AMM:
- Token0 = "fixed token" (virtual accounting)
- Token1 = "variable token" = Notional

The key formula: notional = liquidity * (sqrtPriceUpper - sqrtPriceLower) / Q96

This comes from SqrtPriceMath.getAmount1Delta in the Solidity contracts.
"""

from decimal import Decimal, getcontext

from xccy.math.fixed_point import Q96, mul_div
from xccy.math.tick import tick_to_sqrt_price_x96

getcontext().prec = 50


# ═══════════════════════════════════════════════════════════════════════════════
# Amount Delta Calculations
# ═══════════════════════════════════════════════════════════════════════════════

def get_amount0_delta(
    sqrt_ratio_a_x96: int,
    sqrt_ratio_b_x96: int,
    liquidity: int,
    round_up: bool = False,
) -> int:
    """
    Calculate the amount of token0 (fixed token) for a liquidity position.
    
    Formula: amount0 = liquidity * (sqrtPriceB - sqrtPriceA) / (sqrtPriceA * sqrtPriceB) * Q96
    
    This is a Python port of SqrtPriceMath.getAmount0Delta.
    
    Args:
        sqrt_ratio_a_x96: First sqrt price (Q64.96).
        sqrt_ratio_b_x96: Second sqrt price (Q64.96).
        liquidity: Liquidity amount.
        round_up: Round result up if True.
        
    Returns:
        Amount of token0.
        
    Example:
        >>> amount0 = get_amount0_delta(sqrt_lower, sqrt_upper, 1000000)
    """
    # Ensure a < b
    if sqrt_ratio_a_x96 > sqrt_ratio_b_x96:
        sqrt_ratio_a_x96, sqrt_ratio_b_x96 = sqrt_ratio_b_x96, sqrt_ratio_a_x96
    
    if sqrt_ratio_a_x96 == 0:
        raise ValueError("sqrt_ratio_a_x96 must be > 0")
    
    numerator1 = liquidity << 96  # liquidity * Q96
    numerator2 = sqrt_ratio_b_x96 - sqrt_ratio_a_x96
    
    # amount0 = (liquidity * Q96 * (sqrtB - sqrtA)) / (sqrtB * sqrtA)
    if round_up:
        intermediate = mul_div(numerator1, numerator2, sqrt_ratio_b_x96, round_up=True)
        return (intermediate + sqrt_ratio_a_x96 - 1) // sqrt_ratio_a_x96
    else:
        return mul_div(numerator1, numerator2, sqrt_ratio_b_x96) // sqrt_ratio_a_x96


def get_amount1_delta(
    sqrt_ratio_a_x96: int,
    sqrt_ratio_b_x96: int,
    liquidity: int,
    round_up: bool = False,
) -> int:
    """
    Calculate the amount of token1 (variable token / notional) for a liquidity position.
    
    Formula: amount1 = liquidity * (sqrtPriceB - sqrtPriceA) / Q96
    
    This is the key formula for notional calculation in IRS AMM.
    
    Args:
        sqrt_ratio_a_x96: First sqrt price (Q64.96).
        sqrt_ratio_b_x96: Second sqrt price (Q64.96).
        liquidity: Liquidity amount.
        round_up: Round result up if True.
        
    Returns:
        Amount of token1 (notional).
        
    Example:
        >>> notional = get_amount1_delta(sqrt_lower, sqrt_upper, 1000000)
    """
    # Ensure a < b
    if sqrt_ratio_a_x96 > sqrt_ratio_b_x96:
        sqrt_ratio_a_x96, sqrt_ratio_b_x96 = sqrt_ratio_b_x96, sqrt_ratio_a_x96
    
    delta = sqrt_ratio_b_x96 - sqrt_ratio_a_x96
    
    if round_up:
        return mul_div(liquidity, delta, Q96, round_up=True)
    else:
        return mul_div(liquidity, delta, Q96)


# ═══════════════════════════════════════════════════════════════════════════════
# Liquidity ↔ Notional Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def liquidity_to_notional(
    liquidity: int,
    tick_lower: int,
    tick_upper: int,
) -> int:
    """
    Convert liquidity units to notional amount.
    
    In the IRS AMM, notional = token1 (variable token).
    
    Formula: notional = liquidity * (sqrtPriceUpper - sqrtPriceLower) / Q96
    
    Args:
        liquidity: Liquidity units (from mint/burn operations).
        tick_lower: Lower tick of the LP range.
        tick_upper: Upper tick of the LP range.
        
    Returns:
        Notional amount in token decimals.
        
    Raises:
        ValueError: If tick_lower >= tick_upper.
        
    Example:
        >>> # Check notional for a position
        >>> notional = liquidity_to_notional(1000000, -6950, -6850)
        >>> print(f"Notional: {notional / 10**6:.2f} USDC")
    """
    if tick_lower >= tick_upper:
        raise ValueError(f"tick_lower ({tick_lower}) must be < tick_upper ({tick_upper})")
    
    sqrt_price_lower = tick_to_sqrt_price_x96(tick_lower)
    sqrt_price_upper = tick_to_sqrt_price_x96(tick_upper)
    
    return get_amount1_delta(sqrt_price_lower, sqrt_price_upper, liquidity)


def notional_to_liquidity(
    notional: int,
    tick_lower: int,
    tick_upper: int,
) -> int:
    """
    Convert notional amount to liquidity units.
    
    Use this to calculate how much liquidity to mint for a desired notional.
    
    Formula: liquidity = notional * Q96 / (sqrtPriceUpper - sqrtPriceLower)
    
    Args:
        notional: Desired notional amount in token decimals.
        tick_lower: Lower tick of the LP range.
        tick_upper: Upper tick of the LP range.
        
    Returns:
        Liquidity units to pass to mint().
        
    Raises:
        ValueError: If tick_lower >= tick_upper.
        
    Example:
        >>> # Calculate liquidity for 10,000 USDC notional
        >>> liquidity = notional_to_liquidity(10_000 * 10**6, -6950, -6850)
        >>> client.trading.mint(pool, account, -6950, -6850, liquidity)
    """
    if tick_lower >= tick_upper:
        raise ValueError(f"tick_lower ({tick_lower}) must be < tick_upper ({tick_upper})")
    
    sqrt_price_lower = tick_to_sqrt_price_x96(tick_lower)
    sqrt_price_upper = tick_to_sqrt_price_x96(tick_upper)
    
    delta = sqrt_price_upper - sqrt_price_lower
    
    if delta == 0:
        raise ValueError("Tick range results in zero price delta")
    
    # liquidity = notional * Q96 / (sqrtUpper - sqrtLower)
    return (notional * Q96) // delta


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def estimate_liquidity_for_notional(
    notional_usd: float,
    tick_lower: int,
    tick_upper: int,
    token_decimals: int = 6,
) -> int:
    """
    Estimate liquidity needed for a given notional in USD.
    
    Convenience function for quick calculations.
    
    Args:
        notional_usd: Desired notional in USD (e.g., 10000 for $10k).
        tick_lower: Lower tick of the LP range.
        tick_upper: Upper tick of the LP range.
        token_decimals: Decimals of the underlying token (default 6 for USDC).
        
    Returns:
        Estimated liquidity units.
        
    Example:
        >>> liquidity = estimate_liquidity_for_notional(10000, -6950, -6850)
        >>> print(f"Need {liquidity} liquidity units for $10k notional")
    """
    notional_raw = int(notional_usd * (10 ** token_decimals))
    return notional_to_liquidity(notional_raw, tick_lower, tick_upper)


def get_position_value_bounds(
    liquidity: int,
    tick_lower: int,
    tick_upper: int,
    current_tick: int,
) -> tuple[int, int]:
    """
    Calculate the token amounts if position were fully in token0 or token1.
    
    Useful for understanding LP position exposure.
    
    Args:
        liquidity: Position liquidity.
        tick_lower: Lower tick bound.
        tick_upper: Upper tick bound.
        current_tick: Current pool tick.
        
    Returns:
        Tuple of (amount0, amount1) representing:
        - amount0: Fixed token if price at upper bound
        - amount1: Variable token (notional) if price at lower bound
    """
    sqrt_price_lower = tick_to_sqrt_price_x96(tick_lower)
    sqrt_price_upper = tick_to_sqrt_price_x96(tick_upper)
    sqrt_price_current = tick_to_sqrt_price_x96(current_tick)
    
    if current_tick < tick_lower:
        # All in token0 (fixed)
        amount0 = get_amount0_delta(sqrt_price_lower, sqrt_price_upper, liquidity)
        amount1 = 0
    elif current_tick >= tick_upper:
        # All in token1 (variable/notional)
        amount0 = 0
        amount1 = get_amount1_delta(sqrt_price_lower, sqrt_price_upper, liquidity)
    else:
        # Split between both
        amount0 = get_amount0_delta(sqrt_price_current, sqrt_price_upper, liquidity)
        amount1 = get_amount1_delta(sqrt_price_lower, sqrt_price_current, liquidity)
    
    return (amount0, amount1)


def format_notional(notional: int, token_decimals: int = 6, symbol: str = "") -> str:
    """
    Format notional amount as human-readable string.
    
    Args:
        notional: Raw notional amount.
        token_decimals: Token decimals (default 6 for USDC).
        symbol: Optional token symbol to append.
        
    Returns:
        Formatted string.
        
    Example:
        >>> format_notional(10000000000, 6, "USDC")
        '10,000.00 USDC'
    """
    value = notional / (10 ** token_decimals)
    formatted = f"{value:,.2f}"
    return f"{formatted} {symbol}".strip()
