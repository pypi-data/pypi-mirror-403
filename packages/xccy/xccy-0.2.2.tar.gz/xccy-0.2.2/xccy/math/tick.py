"""
Tick math utilities for XCCY Protocol.

Ticks are discrete price points in the VAMM. Each tick represents a price
of 1.0001^tick, following Uniswap V3's concentrated liquidity design.

In the IRS AMM context:
- Lower ticks = higher fixed rates
- Higher ticks = lower fixed rates
- MIN_TICK (-69100) ≈ 1000% annualized rate
- MAX_TICK (69100) ≈ 0.001% annualized rate
"""

import math
from decimal import Decimal, getcontext

from xccy.math.fixed_point import Q96

getcontext().prec = 50

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

MIN_TICK: int = -69100
"""Minimum tick, corresponds to ~1000% annualized fixed rate."""

MAX_TICK: int = 69100
"""Maximum tick, corresponds to ~0.001% annualized fixed rate."""

MIN_SQRT_RATIO: int = 2503036416286949174936592462
"""Minimum sqrt price ratio (at MIN_TICK)."""

MAX_SQRT_RATIO: int = 2507794810551837817144115957740
"""Maximum sqrt price ratio (at MAX_TICK)."""

# Magic numbers for tick calculation (from Uniswap V3 TickMath)
_TICK_RATIOS = [
    (0x1, 0xfffcb933bd6fad37aa2d162d1a594001),
    (0x2, 0xfff97272373d413259a46990580e213a),
    (0x4, 0xfff2e50f5f656932ef12357cf3c7fdcc),
    (0x8, 0xffe5caca7e10e4e61c3624eaa0941cd0),
    (0x10, 0xffcb9843d60f6159c9db58835c926644),
    (0x20, 0xff973b41fa98c081472e6896dfb254c0),
    (0x40, 0xff2ea16466c96a3843ec78b326b52861),
    (0x80, 0xfe5dee046a99a2a811c461f1969c3053),
    (0x100, 0xfcbe86c7900a88aedcffc83b479aa3a4),
    (0x200, 0xf987a7253ac413176f2b074cf7815e54),
    (0x400, 0xf3392b0822b70005940c7a398e4b70f3),
    (0x800, 0xe7159475a2c29b7443b29c7fa6e889d9),
    (0x1000, 0xd097f3bdfd2022b8845ad8f792aa5825),
    (0x2000, 0xa9f746462d870fdf8a65dc1f90e061e5),
    (0x4000, 0x70d869a156d2a1b890bb3df62baf32f7),
    (0x8000, 0x31be135f97d08fd981231505542fcfa6),
    (0x10000, 0x9aa508b5b7a84e1c677de54f3e99bc9),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Tick ↔ Sqrt Price Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def tick_to_sqrt_price_x96(tick: int) -> int:
    """
    Calculate sqrt(1.0001^tick) * 2^96.
    
    This is a Python port of TickMath.getSqrtRatioAtTick from Uniswap V3.
    
    Args:
        tick: The tick value. Must be in range [MIN_TICK, MAX_TICK].
        
    Returns:
        The sqrt price as a Q64.96 fixed-point number.
        
    Raises:
        ValueError: If tick is out of valid range.
        
    Example:
        >>> sqrt_price = tick_to_sqrt_price_x96(-6930)
        >>> # This corresponds to ~5% fixed rate
    """
    if not (MIN_TICK <= tick <= MAX_TICK):
        raise ValueError(f"Tick {tick} out of range [{MIN_TICK}, {MAX_TICK}]")
    
    abs_tick = abs(tick)
    
    # Start with base ratio
    if abs_tick & 0x1 != 0:
        ratio = 0xfffcb933bd6fad37aa2d162d1a594001
    else:
        ratio = 0x100000000000000000000000000000000
    
    # Apply each bit of the absolute tick
    for mask, multiplier in _TICK_RATIOS[1:]:
        if abs_tick & mask != 0:
            ratio = (ratio * multiplier) >> 128
    
    # Invert if tick is positive
    if tick > 0:
        ratio = (2**256 - 1) // ratio
    
    # Convert from Q128.128 to Q64.96 with rounding up
    sqrt_price_x96 = (ratio >> 32) + (1 if ratio % (1 << 32) != 0 else 0)
    
    return sqrt_price_x96


def sqrt_price_x96_to_tick(sqrt_price_x96: int) -> int:
    """
    Calculate the tick for a given sqrt price.
    
    Returns the greatest tick where getSqrtRatioAtTick(tick) <= sqrtPriceX96.
    
    Args:
        sqrt_price_x96: The sqrt price as a Q64.96 number.
        
    Returns:
        The corresponding tick.
        
    Raises:
        ValueError: If sqrt price is out of valid range.
        
    Example:
        >>> tick = sqrt_price_x96_to_tick(79228162514264337593543950336)
        >>> # Returns tick 0
    """
    if not (MIN_SQRT_RATIO <= sqrt_price_x96 < MAX_SQRT_RATIO):
        raise ValueError(
            f"Sqrt price {sqrt_price_x96} out of range "
            f"[{MIN_SQRT_RATIO}, {MAX_SQRT_RATIO})"
        )
    
    # Use logarithm approach for Python
    # price = sqrt_price^2 / Q96^2 = (sqrt_price / Q96)^2
    # tick = log(price) / log(1.0001) = 2 * log(sqrt_price / Q96) / log(1.0001)
    
    sqrt_ratio = Decimal(sqrt_price_x96) / Decimal(Q96)
    price = sqrt_ratio ** 2
    
    # tick = log_1.0001(price) = ln(price) / ln(1.0001)
    log_base = Decimal("1.0001").ln()
    tick_decimal = price.ln() / log_base
    
    tick = int(tick_decimal)
    
    # Verify and adjust if needed
    if tick_to_sqrt_price_x96(tick + 1) <= sqrt_price_x96:
        tick += 1
    
    return tick


# ═══════════════════════════════════════════════════════════════════════════════
# Tick ↔ Fixed Rate Conversions
# ═══════════════════════════════════════════════════════════════════════════════

def tick_to_price(tick: int) -> Decimal:
    """
    Convert tick to price (1.0001^tick).
    
    Args:
        tick: The tick value.
        
    Returns:
        The price as a Decimal.
        
    Example:
        >>> tick_to_price(0)
        Decimal('1')
        >>> float(tick_to_price(100))  # ~1.01
        1.010049...
    """
    return Decimal("1.0001") ** tick


def price_to_tick(price: Decimal | float) -> int:
    """
    Convert price to nearest tick.
    
    Args:
        price: The price value (should be > 0).
        
    Returns:
        The nearest valid tick.
        
    Raises:
        ValueError: If price is <= 0.
    """
    if price <= 0:
        raise ValueError("Price must be positive")
    
    # tick = log_1.0001(price)
    tick = int(math.log(float(price)) / math.log(1.0001))
    
    # Clamp to valid range
    return max(MIN_TICK, min(MAX_TICK, tick))


def tick_to_fixed_rate(tick: int, years: float = 1.0) -> Decimal:
    """
    Convert tick to annualized fixed rate.
    
    In the IRS AMM (Voltz/XCCY), the formula is:
        rate = 1.0001^(-tick)
    
    This returns the rate as a decimal (e.g., 0.05 for 5%).
    Lower ticks = higher rates.
    
    Note: Voltz internally stores rates as percentage numbers (8.0 = 8%),
    but this function returns decimals (0.08 = 8%) for consistency with
    standard financial conventions.
    
    Args:
        tick: The tick value.
        years: Term length in years (default 1.0). For multi-year terms,
            the rate is annualized.
        
    Returns:
        Annualized fixed rate as Decimal (e.g., 0.05 = 5%).
        
    Example:
        >>> float(tick_to_fixed_rate(-6931))
        0.02...  # ~2%
        >>> float(tick_to_fixed_rate(-20795))
        0.08...  # ~8%
        >>> float(tick_to_fixed_rate(-48790))
        1.0...   # ~100%
    """
    # Voltz formula: rate_pct = 1.0001^(-tick) (as percentage number)
    # We convert to decimal by dividing by 100
    rate_pct = Decimal("1.0001") ** (-tick)
    rate = rate_pct / Decimal(100)
    
    if years != 1.0:
        # Annualize for non-1-year terms
        # The rate needs to be converted considering term length
        rate = rate / Decimal(str(years))
    
    return rate


def fixed_rate_to_tick(rate: Decimal | float, years: float = 1.0) -> int:
    """
    Convert annualized fixed rate to tick.
    
    Inverse of tick_to_fixed_rate. Uses Voltz formula:
        tick = -log(rate * 100) / log(1.0001)
    
    Args:
        rate: Annualized rate as decimal (e.g., 0.05 = 5%).
        years: Term length in years (default 1.0).
        
    Returns:
        The corresponding tick (negative for positive rates).
        
    Raises:
        ValueError: If rate would result in invalid tick.
        
    Example:
        >>> fixed_rate_to_tick(0.02)  # 2% rate
        -6931
        >>> fixed_rate_to_tick(0.08)  # 8% rate
        -20795
        >>> fixed_rate_to_tick(1.0)  # 100% rate
        -48790
    """
    if rate <= 0:
        raise ValueError("Rate must be positive")
    
    rate_val = float(rate)
    
    # For multi-year terms, adjust rate
    if years != 1.0:
        rate_val = rate_val * years
    
    # Convert to percentage number (0.08 -> 8.0)
    rate_pct = rate_val * 100
    
    # tick = -log(rate_pct) / log(1.0001)
    tick = int(-math.log(rate_pct) / math.log(1.0001))
    
    return max(MIN_TICK, min(MAX_TICK, tick))


# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def align_tick_to_spacing(tick: int, tick_spacing: int, round_up: bool = False) -> int:
    """
    Align a tick to the nearest valid tick for a given spacing.
    
    Args:
        tick: The tick to align.
        tick_spacing: The pool's tick spacing.
        round_up: If True, round away from zero; if False, round toward zero.
        
    Returns:
        Aligned tick that is a multiple of tick_spacing.
        
    Example:
        >>> align_tick_to_spacing(-6925, 60)
        -6960  # Rounds down (more negative)
        >>> align_tick_to_spacing(-6925, 60, round_up=True)
        -6900  # Rounds up (toward zero)
    """
    if tick_spacing <= 0:
        raise ValueError("tick_spacing must be positive")
    
    remainder = tick % tick_spacing
    
    if remainder == 0:
        return tick
    
    if round_up:
        if tick < 0:
            return tick - remainder
        else:
            return tick + (tick_spacing - remainder)
    else:
        if tick < 0:
            return tick - remainder - tick_spacing
        else:
            return tick - remainder


def get_tick_range_for_rate(
    target_rate: float,
    width_bps: int = 100,
    tick_spacing: int = 60,
) -> tuple[int, int]:
    """
    Calculate a tick range centered around a target rate.
    
    Args:
        target_rate: Target fixed rate (e.g., 0.05 for 5%).
        width_bps: Width of range in basis points (default 100 = 1%).
        tick_spacing: Pool's tick spacing for alignment.
        
    Returns:
        Tuple of (tick_lower, tick_upper) aligned to tick spacing.
        
    Example:
        >>> get_tick_range_for_rate(0.05, width_bps=50)
        (-6960, -6900)  # Range around 5% ± 0.25%
    """
    # Calculate ticks for rate ± half width
    half_width = Decimal(str(width_bps)) / Decimal("20000")  # bps/2 as decimal
    
    rate_lower = Decimal(str(target_rate)) + half_width
    rate_upper = Decimal(str(target_rate)) - half_width
    
    # Remember: lower tick = higher rate
    tick_upper = align_tick_to_spacing(
        fixed_rate_to_tick(float(rate_upper)), tick_spacing, round_up=True
    )
    tick_lower = align_tick_to_spacing(
        fixed_rate_to_tick(float(rate_lower)), tick_spacing, round_up=False
    )
    
    return (tick_lower, tick_upper)


def format_tick_as_rate(tick: int, decimals: int = 2) -> str:
    """
    Format a tick as a human-readable rate string.
    
    Args:
        tick: The tick value.
        decimals: Number of decimal places for the percentage.
        
    Returns:
        Formatted rate string (e.g., "5.00%").
    """
    rate = tick_to_fixed_rate(tick)
    pct = float(rate) * 100
    return f"{pct:.{decimals}f}%"
