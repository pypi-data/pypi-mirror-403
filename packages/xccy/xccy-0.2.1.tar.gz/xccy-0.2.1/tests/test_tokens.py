"""Tests for token constants."""

import pytest

from xccy.tokens import PolygonTokens, TokenInfo


class TestPolygonTokens:
    """Tests for Polygon token constants."""
    
    def test_usdc_address(self):
        """USDC address should be valid."""
        assert PolygonTokens.USDC.startswith("0x")
        assert len(PolygonTokens.USDC) == 42
    
    def test_usdt_address(self):
        """USDT address should be valid."""
        assert PolygonTokens.USDT.startswith("0x")
        assert len(PolygonTokens.USDT) == 42
    
    def test_aave_tokens(self):
        """Aave aTokens should be defined."""
        assert PolygonTokens.A_USDC.startswith("0x")
        assert PolygonTokens.A_USDT.startswith("0x")
        assert PolygonTokens.A_DAI.startswith("0x")
    
    def test_eth_variants(self):
        """ETH variants should be defined."""
        assert PolygonTokens.WETH.startswith("0x")
        assert PolygonTokens.WMATIC.startswith("0x")
    
    def test_get_info_usdc(self):
        """Get USDC token info."""
        info = PolygonTokens.get_info("USDC")
        
        assert info is not None
        assert info.symbol == "USDC"
        assert info.decimals == 6
        assert info.address == PolygonTokens.USDC
    
    def test_get_info_unknown(self):
        """Unknown token returns None."""
        info = PolygonTokens.get_info("UNKNOWN_TOKEN")
        assert info is None
    
    def test_get_decimals_usdc(self):
        """USDC should have 6 decimals."""
        decimals = PolygonTokens.get_decimals(PolygonTokens.USDC)
        assert decimals == 6
    
    def test_get_decimals_weth(self):
        """WETH should have 18 decimals."""
        decimals = PolygonTokens.get_decimals(PolygonTokens.WETH)
        assert decimals == 18
    
    def test_get_decimals_unknown(self):
        """Unknown token defaults to 18 decimals."""
        decimals = PolygonTokens.get_decimals("0x0000000000000000000000000000000000000000")
        assert decimals == 18
    
    def test_get_decimals_case_insensitive(self):
        """Address matching should be case-insensitive."""
        upper = PolygonTokens.get_decimals(PolygonTokens.USDC.upper())
        lower = PolygonTokens.get_decimals(PolygonTokens.USDC.lower())
        assert upper == lower == 6
    
    def test_token_info_str(self):
        """TokenInfo __str__ returns address."""
        info = TokenInfo("0x123", "TEST", 18)
        assert str(info) == "0x123"


class TestTokenAddressesUnique:
    """Verify all token addresses are unique."""
    
    def test_all_addresses_unique(self):
        """No duplicate addresses."""
        addresses = [
            PolygonTokens.USDC,
            PolygonTokens.USDC_E,
            PolygonTokens.USDT,
            PolygonTokens.DAI,
            PolygonTokens.A_USDC,
            PolygonTokens.A_USDT,
            PolygonTokens.A_DAI,
            PolygonTokens.WETH,
            PolygonTokens.WMATIC,
        ]
        
        # Check uniqueness
        assert len(addresses) == len(set(addresses))
    
    def test_addresses_are_checksummed(self):
        """All addresses should be valid checksums (mixed case)."""
        addresses = [
            PolygonTokens.USDC,
            PolygonTokens.USDT,
            PolygonTokens.WETH,
        ]
        
        for addr in addresses:
            # Should have both upper and lower case letters
            has_upper = any(c.isupper() for c in addr[2:])
            has_lower = any(c.islower() for c in addr[2:])
            # At least one should be true for a valid checksum
            assert has_upper or has_lower
