"""
Position management for XCCY Protocol.

Handles position queries, health monitoring, and margin requirement checks.
All position data is read from the CollateralEngine contract.
"""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from xccy.types import AccountId, PositionInfo, HealthStatus, PoolKey
from xccy.math.fixed_point import wad_to_decimal, WAD
from xccy.exceptions import AccountNotFoundError

if TYPE_CHECKING:
    from xccy.client import XccyClient


class PositionManager:
    """
    Manager for position queries and health monitoring.
    
    Provides methods for checking margin requirements, calculating
    health factor, and querying position details.
    
    Access via `client.position`.
    
    Example:
        >>> # Check if account is healthy
        >>> shortfall = client.position.check_margin_requirement(account)
        >>> if shortfall == 0:
        ...     print("Account is healthy!")
        >>> else:
        ...     print(f"Need ${shortfall:.2f} more margin")
        >>> 
        >>> # Get health factor
        >>> status = client.position.get_health_status(account)
        >>> print(f"Health: {status.health_factor:.2f}")
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def check_margin_requirement(self, account: AccountId) -> Decimal:
        """
        Check if account meets margin requirements.
        
        Calls CollateralEngine.checkMarginRequirement on-chain.
        
        Args:
            account: The account to check.
            
        Returns:
            Margin shortfall in USD (0 if healthy, > 0 if undercollateralized).
            
        Example:
            >>> shortfall = client.position.check_margin_requirement(account)
            >>> if shortfall > 0:
            ...     print(f"Warning: Need ${shortfall:.2f} more margin!")
        """
        contract = self._client.collateral_engine
        result = contract.functions.checkMarginRequirement(
            account.to_tuple(),
        ).call()
        
        # Result is in USD with WAD precision
        return wad_to_decimal(result)
    
    def get_obligations(self, account: AccountId) -> Decimal:
        """
        Get total obligations (margin required) for an account.
        
        Calls CollateralEngine.calculateAccountObligation on-chain.
        
        Args:
            account: The account to query.
            
        Returns:
            Total obligations in USD as Decimal.
            
        Example:
            >>> obligations = client.position.get_obligations(account)
            >>> print(f"Total obligations: ${obligations:.2f}")
        """
        contract = self._client.collateral_engine
        result = contract.functions.calculateAccountObligation(
            account.to_tuple(),
        ).call()
        
        return wad_to_decimal(result)
    
    def get_obligations_wad(self, account: AccountId) -> int:
        """
        Get total obligations in WAD format.
        
        Args:
            account: The account to query.
            
        Returns:
            Obligations as WAD-encoded integer.
        """
        contract = self._client.collateral_engine
        return contract.functions.calculateAccountObligation(
            account.to_tuple(),
        ).call()
    
    def is_liquidatable(self, account: AccountId) -> bool:
        """
        Check if account can be liquidated.
        
        An account is liquidatable if margin_value < obligations.
        
        Args:
            account: The account to check.
            
        Returns:
            True if account can be liquidated.
            
        Example:
            >>> if client.position.is_liquidatable(account):
            ...     print("WARNING: Account at liquidation risk!")
        """
        shortfall = self.check_margin_requirement(account)
        return shortfall > 0
    
    def get_health_factor(self, account: AccountId) -> Decimal:
        """
        Calculate health factor for an account.
        
        Health factor = margin_value / obligations
        - > 1.0: Healthy
        - < 1.0: Undercollateralized (liquidatable)
        - infinity: No positions
        
        Args:
            account: The account to query.
            
        Returns:
            Health factor as Decimal.
            
        Example:
            >>> health = client.position.get_health_factor(account)
            >>> if health < Decimal("1.2"):
            ...     print("Warning: Health factor below safe threshold")
        """
        obligations = self.get_obligations(account)
        
        if obligations == 0:
            return Decimal("inf")
        
        margin_value = self._client.margin.get_total_value_usd(account)
        return margin_value / obligations
    
    def get_health_status(self, account: AccountId) -> HealthStatus:
        """
        Get comprehensive health status for an account.
        
        Args:
            account: The account to query.
            
        Returns:
            HealthStatus with margin value, obligations, health factor,
            and liquidation status.
            
        Example:
            >>> status = client.position.get_health_status(account)
            >>> print(f"Margin: ${status.margin_value_usd:.2f}")
            >>> print(f"Obligations: ${status.obligations_usd:.2f}")
            >>> print(f"Health: {status.health_factor:.2f}")
            >>> print(f"Liquidatable: {status.is_liquidatable}")
        """
        margin_value = self._client.margin.get_total_value_usd(account)
        obligations = self.get_obligations(account)
        
        return HealthStatus.from_values(margin_value, obligations)
    
    def get_active_positions(self, owner: Optional[str] = None):
        """
        Get all active positions for a user.
        
        Fetches position data from the backend API.
        
        Args:
            owner: Wallet address. Uses signer address if not provided.
            
        Returns:
            List of UserPosition objects.
            
        Raises:
            ValueError: If backend not configured or no owner provided.
            
        Example:
            >>> positions = client.position.get_active_positions()
            >>> for pos in positions:
            ...     print(f"Pool: {pos.pool_id[:16]}...")
            ...     print(f"  Notional: ${pos.notional_value}")
            ...     print(f"  PnL: ${pos.pnl}, UPnL: ${pos.upnl}")
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured. Initialize client with backend_url.")
        
        address = owner or self._client.signer_address
        if not address:
            raise ValueError("No owner address provided and no signer configured")
        
        return self._client.backend.get_user_active_positions(address)
    
    def get_all_positions(self, owner: Optional[str] = None):
        """
        Get all positions (including settled) for a user.
        
        Args:
            owner: Wallet address. Uses signer address if not provided.
            
        Returns:
            List of all UserPosition objects.
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        address = owner or self._client.signer_address
        if not address:
            raise ValueError("No owner address provided")
        
        return self._client.backend.get_user_positions(address)
    
    def get_position_count(self, owner: Optional[str] = None) -> int:
        """
        Get number of active positions.
        
        Args:
            owner: Wallet address. Uses signer address if not provided.
            
        Returns:
            Count of active positions.
        """
        if not self._client.has_backend:
            return 0  # Can't query without backend
        
        address = owner or self._client.signer_address
        if not address:
            return 0
        
        positions = self.get_active_positions(address)
        return len(positions)
    
    def get_user_metrics(self, owner: Optional[str] = None):
        """
        Get aggregated metrics for a user.
        
        Includes total PnL, collateral, and sub-account breakdown.
        
        Args:
            owner: Wallet address. Uses signer address if not provided.
            
        Returns:
            UserMetrics object with totals and breakdowns.
            
        Example:
            >>> metrics = client.position.get_user_metrics()
            >>> print(f"Total PnL: ${metrics.total_pnl}")
            >>> print(f"Total Collateral: ${metrics.total_collateral}")
            >>> print(f"Active Positions: {metrics.active_positions}")
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        address = owner or self._client.signer_address
        if not address:
            raise ValueError("No owner address provided")
        
        return self._client.backend.get_user_metrics(address)
    
    def get_settlements(self, owner: Optional[str] = None, account_id: Optional[int] = None):
        """
        Get settlement history for matured positions.
        
        Args:
            owner: Wallet address. Uses signer address if not provided.
            account_id: Filter by sub-account ID (optional).
            
        Returns:
            List of SettlementRecord objects.
            
        Example:
            >>> settlements = client.position.get_settlements()
            >>> for s in settlements:
            ...     print(f"Pool {s.pool_id[:16]}...: ${s.amount}")
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        address = owner or self._client.signer_address
        if not address:
            raise ValueError("No owner address provided")
        
        return self._client.backend.get_user_settlements(address, account_id)
    
    def estimate_liquidation_price(
        self,
        account: AccountId,
        token: str,
    ) -> Optional[Decimal]:
        """
        Estimate the price at which account becomes liquidatable.
        
        This is a simplified estimate assuming single collateral token.
        
        Args:
            account: The account.
            token: Collateral token to analyze.
            
        Returns:
            Liquidation price, or None if not applicable.
        """
        balance = self._client.margin.get_balance(account, token)
        if balance == 0:
            return None
        
        obligations = self.get_obligations(account)
        if obligations == 0:
            return None
        
        from xccy.tokens import PolygonTokens
        decimals = PolygonTokens.get_decimals(token)
        balance_decimal = Decimal(balance) / Decimal(10 ** decimals)
        
        # Liquidation price = obligations / balance
        return obligations / balance_decimal
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Backend Integration (Optional)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_pnl_history(
        self,
        owner: str,
        period: str = "1m",
    ):
        """
        Get historical PnL snapshots from backend.
        
        Requires backend API to be configured.
        
        Args:
            owner: Wallet address.
            period: History period ("1d", "1w", "1m", "3m").
            
        Returns:
            List of PnLSnapshot objects.
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        return self._client.backend.get_user_pnl_history(owner, period)
    
    def get_performance(self, owner: str):
        """
        Get user performance metrics from backend.
        
        Requires backend API to be configured.
        
        Args:
            owner: Wallet address.
            
        Returns:
            Performance metrics dictionary.
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        return self._client.backend.get_user_performance(owner)
