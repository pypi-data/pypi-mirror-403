"""Tests for PositionInfo dataclass."""

import pytest
from decimal import Decimal

from xccy.types import AccountId, PositionInfo


@pytest.fixture
def sample_account() -> AccountId:
    """Sample account for testing."""
    return AccountId(
        owner="0x1234567890123456789012345678901234567890",
        account_id=0,
        isolated_margin_token=None,
    )


class TestPositionInfo:
    """Tests for PositionInfo dataclass properties."""
    
    def test_notional_property(self, sample_account):
        """notional returns absolute value of variable_token_balance."""
        position = PositionInfo(
            pool_id="0x" + "ab" * 32,
            account=sample_account,
            tick_lower=-6930,
            tick_upper=-6900,
            liquidity=1000,
            fixed_token_balance=100,
            variable_token_balance=-5000,
        )
        assert position.notional == 5000
    
    def test_is_fixed_taker_true(self, sample_account):
        """is_fixed_taker returns True when variable_token_balance > 0."""
        position = PositionInfo(
            pool_id="0x" + "ab" * 32,
            account=sample_account,
            tick_lower=-6930,
            tick_upper=-6900,
            liquidity=0,
            fixed_token_balance=-100,
            variable_token_balance=5000,  # Positive = paying fixed
        )
        assert position.is_fixed_taker is True
    
    def test_is_fixed_taker_false(self, sample_account):
        """is_fixed_taker returns False when variable_token_balance <= 0."""
        position = PositionInfo(
            pool_id="0x" + "ab" * 32,
            account=sample_account,
            tick_lower=-6930,
            tick_upper=-6900,
            liquidity=0,
            fixed_token_balance=100,
            variable_token_balance=-5000,  # Negative = paying variable
        )
        assert position.is_fixed_taker is False
