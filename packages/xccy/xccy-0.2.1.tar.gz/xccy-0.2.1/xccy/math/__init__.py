"""
Math utilities for XCCY Protocol.

Provides conversions between:
- Ticks and fixed rates
- Liquidity units and notional amounts
- WAD/RAY fixed-point representations and decimals
"""

from xccy.math.tick import (
    tick_to_fixed_rate,
    fixed_rate_to_tick,
    tick_to_sqrt_price_x96,
    sqrt_price_x96_to_tick,
)
from xccy.math.liquidity import (
    liquidity_to_notional,
    notional_to_liquidity,
    get_amount0_delta,
    get_amount1_delta,
)
from xccy.math.fixed_point import (
    wad_to_decimal,
    decimal_to_wad,
    ray_to_decimal,
    decimal_to_ray,
    WAD,
    RAY,
    Q96,
)

__all__ = [
    # Tick math
    "tick_to_fixed_rate",
    "fixed_rate_to_tick",
    "tick_to_sqrt_price_x96",
    "sqrt_price_x96_to_tick",
    # Liquidity math
    "liquidity_to_notional",
    "notional_to_liquidity",
    "get_amount0_delta",
    "get_amount1_delta",
    # Fixed point
    "wad_to_decimal",
    "decimal_to_wad",
    "ray_to_decimal",
    "decimal_to_ray",
    "WAD",
    "RAY",
    "Q96",
]
