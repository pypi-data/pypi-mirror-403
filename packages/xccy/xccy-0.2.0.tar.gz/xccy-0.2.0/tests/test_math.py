"""Tests for math utilities."""

import pytest
from decimal import Decimal

from xccy.math.fixed_point import (
    WAD,
    RAY,
    Q96,
    wad_to_decimal,
    decimal_to_wad,
    ray_to_decimal,
    decimal_to_ray,
    mul_div,
)
from xccy.math.tick import (
    MIN_TICK,
    MAX_TICK,
    tick_to_sqrt_price_x96,
    sqrt_price_x96_to_tick,
    tick_to_fixed_rate,
    fixed_rate_to_tick,
    tick_to_price,
    align_tick_to_spacing,
)
from xccy.math.liquidity import (
    get_amount0_delta,
    get_amount1_delta,
    liquidity_to_notional,
    notional_to_liquidity,
)


class TestFixedPoint:
    """Tests for fixed-point arithmetic."""
    
    def test_wad_constants(self):
        """WAD should be 10^18."""
        assert WAD == 10**18
    
    def test_ray_constants(self):
        """RAY should be 10^27."""
        assert RAY == 10**27
    
    def test_q96_constants(self):
        """Q96 should be 2^96."""
        assert Q96 == 2**96
    
    def test_wad_to_decimal(self):
        """Convert WAD to Decimal."""
        assert wad_to_decimal(5 * WAD) == Decimal(5)
        assert wad_to_decimal(WAD // 2) == Decimal("0.5")
    
    def test_decimal_to_wad(self):
        """Convert Decimal to WAD."""
        assert decimal_to_wad(5) == 5 * WAD
        assert decimal_to_wad(0.5) == WAD // 2
    
    def test_ray_to_decimal(self):
        """Convert RAY to Decimal."""
        assert ray_to_decimal(RAY) == Decimal(1)
        assert ray_to_decimal(5 * RAY // 100) == Decimal("0.05")
    
    def test_decimal_to_ray(self):
        """Convert Decimal to RAY."""
        assert decimal_to_ray(1) == RAY
    
    def test_mul_div(self):
        """Test mulDiv helper."""
        assert mul_div(100, 200, 50) == 400
        assert mul_div(100, 200, 300) == 66  # Rounds down
        assert mul_div(100, 200, 300, round_up=True) == 67
    
    def test_mul_div_zero_denominator(self):
        """mulDiv with zero denominator should raise."""
        with pytest.raises(ValueError, match="Division by zero"):
            mul_div(100, 200, 0)


class TestTickMath:
    """Tests for tick math utilities."""
    
    def test_tick_bounds(self):
        """MIN_TICK and MAX_TICK should be symmetric."""
        assert MIN_TICK == -69100
        assert MAX_TICK == 69100
        assert MAX_TICK == -MIN_TICK
    
    def test_tick_to_sqrt_price_at_zero(self):
        """Tick 0 should give sqrt(1.0) * Q96."""
        sqrt_price = tick_to_sqrt_price_x96(0)
        # At tick 0, price = 1.0001^0 = 1, sqrt = 1
        expected = Q96  # Approximately, may have small rounding
        assert abs(sqrt_price - expected) < expected // 1000  # Within 0.1%
    
    def test_tick_to_sqrt_price_positive(self):
        """Positive ticks should give higher prices."""
        sqrt_100 = tick_to_sqrt_price_x96(100)
        sqrt_0 = tick_to_sqrt_price_x96(0)
        assert sqrt_100 > sqrt_0
    
    def test_tick_to_sqrt_price_negative(self):
        """Negative ticks should give lower prices."""
        sqrt_neg100 = tick_to_sqrt_price_x96(-100)
        sqrt_0 = tick_to_sqrt_price_x96(0)
        assert sqrt_neg100 < sqrt_0
    
    def test_tick_to_sqrt_price_out_of_range(self):
        """Ticks outside range should raise."""
        with pytest.raises(ValueError):
            tick_to_sqrt_price_x96(MIN_TICK - 1)
        with pytest.raises(ValueError):
            tick_to_sqrt_price_x96(MAX_TICK + 1)
    
    def test_sqrt_price_to_tick_roundtrip(self):
        """Converting tick -> sqrt -> tick should preserve value."""
        for tick in [-6930, 0, 6930]:
            sqrt_price = tick_to_sqrt_price_x96(tick)
            recovered = sqrt_price_x96_to_tick(sqrt_price)
            assert abs(recovered - tick) <= 1  # Allow rounding error
    
    def test_tick_to_price(self):
        """Tick to price conversion."""
        price_0 = tick_to_price(0)
        assert price_0 == Decimal(1)
        
        price_100 = tick_to_price(100)
        expected = Decimal("1.0001") ** 100
        assert abs(price_100 - expected) < Decimal("0.0001")
    
    def test_tick_to_fixed_rate(self):
        """Tick to fixed rate conversion."""
        # tick -6931 → rate ≈ 2% (1.0001^6931 / 100 ≈ 0.02)
        rate = tick_to_fixed_rate(-6931)
        assert Decimal("0.015") < rate < Decimal("0.025")
    
    def test_fixed_rate_to_tick(self):
        """Fixed rate to tick conversion."""
        # 5% rate → tick ≈ -16094 (tick = -log(5)/log(1.0001))
        tick = fixed_rate_to_tick(0.05)
        assert -17000 < tick < -15000
    
    def test_fixed_rate_to_tick_roundtrip(self):
        """Converting rate -> tick -> rate should be close."""
        original_rate = 0.05
        tick = fixed_rate_to_tick(original_rate)
        recovered_rate = tick_to_fixed_rate(tick)
        assert abs(float(recovered_rate) - original_rate) < 0.005  # Within 0.5%
    
    def test_align_tick_to_spacing(self):
        """Test tick alignment to spacing."""
        # Align -6925 to spacing of 60
        # With round_up=False (default), rounds down (more negative) for negative ticks
        assert align_tick_to_spacing(-6925, 60) == -7020
        
        # Already aligned
        assert align_tick_to_spacing(-6960, 60) == -6960
        
        # Round up (toward zero for negative)
        aligned_up = align_tick_to_spacing(-6925, 60, round_up=True)
        assert aligned_up == -6960
    
    def test_align_tick_invalid_spacing(self):
        """Tick spacing must be positive."""
        with pytest.raises(ValueError):
            align_tick_to_spacing(-6930, 0)
        with pytest.raises(ValueError):
            align_tick_to_spacing(-6930, -60)


class TestLiquidityMath:
    """Tests for liquidity calculations."""
    
    def test_get_amount1_delta_basic(self):
        """Basic amount1 delta calculation."""
        sqrt_lower = tick_to_sqrt_price_x96(-6960)
        sqrt_upper = tick_to_sqrt_price_x96(-6840)
        liquidity = 1_000_000_000
        
        amount1 = get_amount1_delta(sqrt_lower, sqrt_upper, liquidity)
        
        # Should be positive
        assert amount1 > 0
    
    def test_get_amount1_delta_symmetry(self):
        """Order of sqrt prices shouldn't matter."""
        sqrt_lower = tick_to_sqrt_price_x96(-6960)
        sqrt_upper = tick_to_sqrt_price_x96(-6840)
        liquidity = 1_000_000_000
        
        amount1_a = get_amount1_delta(sqrt_lower, sqrt_upper, liquidity)
        amount1_b = get_amount1_delta(sqrt_upper, sqrt_lower, liquidity)
        
        assert amount1_a == amount1_b
    
    def test_liquidity_to_notional(self):
        """Convert liquidity to notional."""
        tick_lower = -6960
        tick_upper = -6840
        liquidity = 1_000_000_000
        
        notional = liquidity_to_notional(liquidity, tick_lower, tick_upper)
        
        # Should be positive
        assert notional > 0
    
    def test_notional_to_liquidity(self):
        """Convert notional to liquidity."""
        tick_lower = -6960
        tick_upper = -6840
        notional = 10_000_000_000  # 10k with 6 decimals
        
        liquidity = notional_to_liquidity(notional, tick_lower, tick_upper)
        
        # Should be positive
        assert liquidity > 0
    
    def test_liquidity_notional_roundtrip(self):
        """Converting liquidity -> notional -> liquidity should be close."""
        tick_lower = -6960
        tick_upper = -6840
        original_liquidity = 1_000_000_000
        
        notional = liquidity_to_notional(original_liquidity, tick_lower, tick_upper)
        recovered = notional_to_liquidity(notional, tick_lower, tick_upper)
        
        # Should be within 1% due to rounding
        assert abs(recovered - original_liquidity) < original_liquidity // 100
    
    def test_invalid_tick_range(self):
        """tick_lower must be < tick_upper."""
        with pytest.raises(ValueError):
            liquidity_to_notional(1000, -6840, -6960)  # Inverted
        
        with pytest.raises(ValueError):
            liquidity_to_notional(1000, -6900, -6900)  # Equal
    
    def test_wider_range_needs_less_liquidity(self):
        """Wider tick range should need less liquidity for same notional."""
        notional = 10_000_000_000
        
        # Narrow range
        liq_narrow = notional_to_liquidity(notional, -6960, -6900)
        
        # Wide range
        liq_wide = notional_to_liquidity(notional, -7200, -6600)
        
        # Wider range needs less liquidity
        assert liq_wide < liq_narrow
