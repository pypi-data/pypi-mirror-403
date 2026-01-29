"""
Fixed-point arithmetic utilities.

This module provides conversions between fixed-point representations
(WAD, RAY, Q96) and Python Decimal/float types.
"""

from decimal import Decimal, getcontext

# Set decimal precision high enough for financial calculations
getcontext().prec = 50

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

WAD: int = 10**18
"""WAD precision (18 decimals). Standard unit for most protocol values."""

RAY: int = 10**27
"""RAY precision (27 decimals). Used for APR/APY values in Aave-style oracles."""

Q96: int = 2**96
"""Q96 fixed-point multiplier. Used in Uniswap V3-style sqrt price encoding."""

Q128: int = 2**128
"""Q128 fixed-point multiplier. Used for fee and token growth accounting."""


# ═══════════════════════════════════════════════════════════════════════════════
# WAD Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def wad_to_decimal(wad_value: int) -> Decimal:
    """
    Convert WAD-encoded value to Decimal.
    
    Args:
        wad_value: Value encoded with 18 decimal places.
        
    Returns:
        Decimal representation.
        
    Example:
        >>> wad_to_decimal(5 * 10**18)
        Decimal('5')
        >>> wad_to_decimal(int(1.5 * 10**18))
        Decimal('1.5')
    """
    return Decimal(wad_value) / Decimal(WAD)


def decimal_to_wad(value: Decimal | float | int) -> int:
    """
    Convert Decimal/float to WAD-encoded integer.
    
    Args:
        value: Value to encode.
        
    Returns:
        WAD-encoded integer (18 decimal places).
        
    Example:
        >>> decimal_to_wad(5)
        5000000000000000000
        >>> decimal_to_wad(1.5)
        1500000000000000000
    """
    return int(Decimal(str(value)) * Decimal(WAD))


def wad_to_float(wad_value: int) -> float:
    """
    Convert WAD-encoded value to float.
    
    Note: Use wad_to_decimal() for precision-critical calculations.
    
    Args:
        wad_value: Value encoded with 18 decimal places.
        
    Returns:
        Float representation.
    """
    return float(wad_to_decimal(wad_value))


# ═══════════════════════════════════════════════════════════════════════════════
# RAY Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def ray_to_decimal(ray_value: int) -> Decimal:
    """
    Convert RAY-encoded value to Decimal.
    
    Args:
        ray_value: Value encoded with 27 decimal places.
        
    Returns:
        Decimal representation.
        
    Example:
        >>> ray_to_decimal(10**27)
        Decimal('1')
        >>> ray_to_decimal(int(0.05 * 10**27))  # 5% APR
        Decimal('0.05')
    """
    return Decimal(ray_value) / Decimal(RAY)


def decimal_to_ray(value: Decimal | float | int) -> int:
    """
    Convert Decimal/float to RAY-encoded integer.
    
    Args:
        value: Value to encode.
        
    Returns:
        RAY-encoded integer (27 decimal places).
        
    Example:
        >>> decimal_to_ray(0.05)  # 5% APR
        50000000000000000000000000
    """
    return int(Decimal(str(value)) * Decimal(RAY))


def ray_to_float(ray_value: int) -> float:
    """
    Convert RAY-encoded value to float.
    
    Note: Use ray_to_decimal() for precision-critical calculations.
    
    Args:
        ray_value: Value encoded with 27 decimal places.
        
    Returns:
        Float representation.
    """
    return float(ray_to_decimal(ray_value))


# ═══════════════════════════════════════════════════════════════════════════════
# RAY <-> WAD Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def ray_to_wad(ray_value: int) -> int:
    """
    Convert RAY-encoded value to WAD-encoded value.
    
    Args:
        ray_value: Value with 27 decimal places.
        
    Returns:
        Value with 18 decimal places.
    """
    return ray_value // (10**9)


def wad_to_ray(wad_value: int) -> int:
    """
    Convert WAD-encoded value to RAY-encoded value.
    
    Args:
        wad_value: Value with 18 decimal places.
        
    Returns:
        Value with 27 decimal places.
    """
    return wad_value * (10**9)


# ═══════════════════════════════════════════════════════════════════════════════
# Q96 Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def q96_to_decimal(q96_value: int) -> Decimal:
    """
    Convert Q96-encoded value to Decimal.
    
    Args:
        q96_value: Value encoded with 2^96 multiplier.
        
    Returns:
        Decimal representation.
    """
    return Decimal(q96_value) / Decimal(Q96)


def decimal_to_q96(value: Decimal | float | int) -> int:
    """
    Convert Decimal/float to Q96-encoded integer.
    
    Args:
        value: Value to encode.
        
    Returns:
        Q96-encoded integer.
    """
    return int(Decimal(str(value)) * Decimal(Q96))


# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def mul_div(a: int, b: int, denominator: int, round_up: bool = False) -> int:
    """
    Compute (a * b) / denominator with full precision.
    
    Mimics Solidity's FullMath.mulDiv for consistent results.
    
    Args:
        a: First multiplicand.
        b: Second multiplicand.
        denominator: Divisor.
        round_up: If True, round up instead of down.
        
    Returns:
        Result of (a * b) / denominator.
        
    Raises:
        ValueError: If denominator is zero.
    """
    if denominator == 0:
        raise ValueError("Division by zero")
    
    result = (a * b) // denominator
    if round_up and (a * b) % denominator != 0:
        result += 1
    return result


def format_wad(wad_value: int, decimals: int = 4) -> str:
    """
    Format WAD value as a human-readable string.
    
    Args:
        wad_value: WAD-encoded value.
        decimals: Number of decimal places to display.
        
    Returns:
        Formatted string.
        
    Example:
        >>> format_wad(1234567890123456789)
        '1.2346'
    """
    value = wad_to_decimal(wad_value)
    return f"{value:.{decimals}f}"


def format_ray(ray_value: int, decimals: int = 4) -> str:
    """
    Format RAY value as a human-readable string.
    
    Args:
        ray_value: RAY-encoded value.
        decimals: Number of decimal places to display.
        
    Returns:
        Formatted string.
    """
    value = ray_to_decimal(ray_value)
    return f"{value:.{decimals}f}"


def format_percent(value: Decimal | float, decimals: int = 2) -> str:
    """
    Format a decimal rate as a percentage string.
    
    Args:
        value: Decimal rate (e.g., 0.05 for 5%).
        decimals: Number of decimal places.
        
    Returns:
        Formatted percentage string.
        
    Example:
        >>> format_percent(0.0523)
        '5.23%'
    """
    pct = float(value) * 100
    return f"{pct:.{decimals}f}%"
