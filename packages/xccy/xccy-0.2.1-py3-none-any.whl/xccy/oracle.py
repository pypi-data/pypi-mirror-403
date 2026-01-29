"""
Oracle queries for XCCY Protocol.

Provides access to price and rate data from on-chain oracles:
- OracleHub: USD prices for collateral tokens
- AprOracle: APR/APY data for yield-bearing tokens
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from xccy.math.fixed_point import wad_to_decimal, ray_to_decimal, WAD, RAY
from xccy.exceptions import OracleError

if TYPE_CHECKING:
    from xccy.client import XccyClient


class OracleManager:
    """
    Manager for oracle data queries.
    
    Provides methods for fetching prices and rates from on-chain oracles.
    
    Access via `client.oracle`.
    
    Example:
        >>> # Get token price in USD
        >>> price = client.oracle.get_price_usd(PolygonTokens.USDC)
        >>> print(f"USDC price: ${price:.4f}")
        >>> 
        >>> # Get current APR for Aave aToken
        >>> apr = client.oracle.get_apr(PolygonTokens.A_USDC)
        >>> print(f"Current APR: {apr:.2%}")
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def get_price_usd(self, token: str) -> Decimal:
        """
        Get the USD price of a token.
        
        Queries OracleHub for the current price.
        
        Args:
            token: Token address.
            
        Returns:
            Price in USD as Decimal.
            
        Raises:
            OracleError: If price is not available.
            
        Example:
            >>> price = client.oracle.get_price_usd(PolygonTokens.WETH)
            >>> print(f"ETH: ${price:.2f}")
        """
        try:
            contract = self._client.oracle_hub
            price_wad, updated_at, valid = contract.functions.getPriceUsdWad(token).call()
            if not valid:
                raise OracleError(f"Price not valid for {token}", asset=token)
            return wad_to_decimal(price_wad)
        except OracleError:
            raise
        except Exception as e:
            raise OracleError(f"Failed to get price for {token}: {e}", asset=token) from e
    
    def get_price_usd_wad(self, token: str) -> int:
        """
        Get the USD price of a token in WAD format.
        
        Args:
            token: Token address.
            
        Returns:
            Price as WAD-encoded integer (18 decimals).
            
        Raises:
            OracleError: If price is stale or not valid.
        """
        contract = self._client.oracle_hub
        price_wad, updated_at, valid = contract.functions.getPriceUsdWad(token).call()
        
        if not valid:
            raise OracleError(f"Price not valid for {token}", asset=token)
        
        return price_wad
    
    def get_apr(self, compound_token: str) -> Decimal:
        """
        Get the current APR for a yield-bearing token.
        
        Queries AprOracle for the instantaneous annualized rate.
        
        Args:
            compound_token: Yield-bearing token (e.g., aUSDC).
            
        Returns:
            APR as Decimal (e.g., 0.05 = 5%).
            
        Example:
            >>> apr = client.oracle.get_apr(PolygonTokens.A_USDC)
            >>> print(f"Aave USDC APR: {apr:.2%}")
        """
        try:
            contract = self._client.apr_oracle
            apr_ray, updated_at, valid = contract.functions.getOnAprRay(compound_token).call()
            if not valid:
                raise OracleError(f"APR not valid for {compound_token}", asset=compound_token)
            return ray_to_decimal(apr_ray)
        except OracleError:
            raise
        except Exception as e:
            raise OracleError(f"Failed to get APR for {compound_token}: {e}", asset=compound_token) from e
    
    def get_apr_ray(self, compound_token: str) -> int:
        """
        Get the current APR in RAY format.
        
        Args:
            compound_token: Yield-bearing token.
            
        Returns:
            APR as RAY-encoded integer (27 decimals).
            
        Raises:
            OracleError: If APR is stale or not valid.
        """
        contract = self._client.apr_oracle
        apr_ray, updated_at, valid = contract.functions.getOnAprRay(compound_token).call()
        
        if not valid:
            raise OracleError(f"APR not valid for {compound_token}", asset=compound_token)
        
        return apr_ray
    
    def get_rate_from_to(
        self,
        compound_token: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> Decimal:
        """
        Get the cumulative rate between two timestamps.
        
        This is the growth factor of the yield-bearing token over the period.
        For example, if $1 at from_timestamp became $1.05 at to_timestamp,
        the rate would be 1.05.
        
        Args:
            compound_token: Yield-bearing token.
            from_timestamp: Start Unix timestamp.
            to_timestamp: End Unix timestamp.
            
        Returns:
            Growth factor as Decimal.
            
        Example:
            >>> # Get rate over 1 year
            >>> rate = client.oracle.get_rate_from_to(
            ...     PolygonTokens.A_USDC,
            ...     from_timestamp=1704067200,  # Jan 1, 2024
            ...     to_timestamp=1735689600,    # Jan 1, 2025
            ... )
            >>> apy = rate - 1  # Convert to yield
            >>> print(f"Realized APY: {apy:.2%}")
        """
        try:
            contract = self._client.apr_oracle
            rate_ray = contract.functions.getRateFromTo(
                compound_token,
                from_timestamp,
                to_timestamp,
            ).call()
            return ray_to_decimal(rate_ray)
        except Exception as e:
            raise OracleError(
                f"Failed to get rate for {compound_token}: {e}",
                asset=compound_token,
            ) from e
    
    def get_rate_from_to_ray(
        self,
        compound_token: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> int:
        """
        Get cumulative rate in RAY format.
        
        Args:
            compound_token: Yield-bearing token.
            from_timestamp: Start Unix timestamp.
            to_timestamp: End Unix timestamp.
            
        Returns:
            Rate as RAY-encoded integer.
        """
        contract = self._client.apr_oracle
        return contract.functions.getRateFromTo(
            compound_token,
            from_timestamp,
            to_timestamp,
        ).call()
    
    def get_apy_from(
        self,
        compound_token: str,
        from_timestamp: int,
    ) -> Decimal:
        """
        Calculate APY from a past timestamp to now.
        
        Args:
            compound_token: Yield-bearing token.
            from_timestamp: Start Unix timestamp.
            
        Returns:
            Annualized yield as Decimal.
            
        Example:
            >>> # APY over last 30 days
            >>> import time
            >>> apy = client.oracle.get_apy_from(
            ...     PolygonTokens.A_USDC,
            ...     from_timestamp=int(time.time()) - 30 * 86400,
            ... )
        """
        current_block = self._client.web3.eth.get_block("latest")
        to_timestamp = current_block["timestamp"]
        
        rate = self.get_rate_from_to(compound_token, from_timestamp, to_timestamp)
        
        # Calculate annualized yield
        duration_seconds = to_timestamp - from_timestamp
        if duration_seconds <= 0:
            return Decimal(0)
        
        duration_years = Decimal(duration_seconds) / Decimal(365 * 24 * 3600)
        
        if duration_years == 0:
            return Decimal(0)
        
        # APY = rate^(1/years) - 1
        apy = rate ** (Decimal(1) / duration_years) - 1
        return apy
    
    def get_variable_rate_in_wad(
        self,
        compound_token: str,
        term_start_wad: int,
        current_timestamp_wad: int,
    ) -> int:
        """
        Get the realized variable rate for a term in WAD format.
        
        This is the accumulated rate from term start to now.
        
        Args:
            compound_token: Yield-bearing token.
            term_start_wad: Term start timestamp in WAD.
            current_timestamp_wad: Current timestamp in WAD.
            
        Returns:
            Variable rate in WAD.
        """
        from_ts = term_start_wad // WAD
        to_ts = current_timestamp_wad // WAD
        
        rate = self.get_rate_from_to(compound_token, from_ts, to_ts)
        
        # Convert to WAD (rate - 1 gives the yield)
        yield_decimal = rate - 1
        return int(yield_decimal * WAD)
    
    def is_price_available(self, token: str) -> bool:
        """
        Check if price is available for a token.
        
        Args:
            token: Token address.
            
        Returns:
            True if price can be fetched.
        """
        try:
            self.get_price_usd_wad(token)
            return True
        except Exception:
            return False
    
    def is_apr_available(self, compound_token: str) -> bool:
        """
        Check if APR is available for a token.
        
        Args:
            compound_token: Yield-bearing token.
            
        Returns:
            True if APR can be fetched.
        """
        try:
            self.get_apr_ray(compound_token)
            return True
        except Exception:
            return False
