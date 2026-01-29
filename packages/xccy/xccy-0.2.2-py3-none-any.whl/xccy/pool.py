"""
Pool management for XCCY Protocol.

Handles pool queries, state retrieval, and pool key construction.
Pool data is read from the VAMMManager contract.
"""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import time

from xccy.types import PoolKey, PoolInfo
from xccy.math.fixed_point import WAD
from xccy.math.tick import tick_to_fixed_rate, sqrt_price_x96_to_tick
from xccy.exceptions import PoolNotFoundError

if TYPE_CHECKING:
    from xccy.client import XccyClient


class PoolManager:
    """
    Manager for pool-related operations.
    
    Provides methods for querying pool state, building pool keys,
    and checking pool existence.
    
    Access via `client.pool`.
    
    Example:
        >>> # Build a pool key
        >>> pool = client.pool.build_pool_key(
        ...     underlying=PolygonTokens.USDC,
        ...     compound_token=PolygonTokens.A_USDC,
        ...     term_start=1704067200,
        ...     term_end=1735689600,
        ...     fee_percent=0.003,
        ... )
        >>> 
        >>> # Check if pool exists
        >>> if client.pool.pool_exists(pool):
        ...     state = client.pool.get_vamm_state(pool)
        ...     print(f"Current tick: {state['tick']}")
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def build_pool_key(
        self,
        underlying: str,
        compound_token: str,
        term_start: int,
        term_end: int,
        fee_percent: float = 0.003,
        tick_spacing: int = 60,
    ) -> PoolKey:
        """
        Build a PoolKey from parameters.
        
        Args:
            underlying: Underlying asset address (e.g., USDC).
            compound_token: Yield-bearing token (e.g., aUSDC).
            term_start: Term start Unix timestamp.
            term_end: Term end Unix timestamp.
            fee_percent: Pool fee as decimal (e.g., 0.003 = 0.3%).
            tick_spacing: Tick spacing for LP positions.
            
        Returns:
            PoolKey instance.
            
        Example:
            >>> pool = client.pool.build_pool_key(
            ...     underlying=PolygonTokens.USDC,
            ...     compound_token=PolygonTokens.A_USDC,
            ...     term_start=int(time.time()),
            ...     term_end=int(time.time()) + 90 * 86400,  # 90 days
            ... )
        """
        return PoolKey(
            underlying_asset=underlying,
            compound_token=compound_token,
            term_start_timestamp_wad=term_start * WAD,
            term_end_timestamp_wad=term_end * WAD,
            fee_wad=int(fee_percent * WAD),
            tick_spacing=tick_spacing,
        )
    
    def pool_exists(self, pool_key: PoolKey) -> bool:
        """
        Check if a pool exists on-chain.
        
        Args:
            pool_key: The pool key to check.
            
        Returns:
            True if pool exists and is initialized.
        """
        try:
            state = self.get_vamm_state_raw(pool_key)
            return state[0] != 0  # sqrtPriceX96 != 0
        except Exception:
            return False
    
    def get_vamm_state(self, pool_key: PoolKey) -> dict:
        """
        Get the current VAMM state for a pool.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Dictionary with:
            - sqrt_price_x96: Current price (Q64.96)
            - tick: Current tick
            - liquidity: Total active liquidity
            - fixed_rate: Current fixed rate (Decimal)
            
        Raises:
            PoolNotFoundError: If pool doesn't exist.
            
        Example:
            >>> state = client.pool.get_vamm_state(pool)
            >>> print(f"Current fixed rate: {state['fixed_rate']:.2%}")
        """
        raw = self.get_vamm_state_raw(pool_key)
        
        if raw[0] == 0:
            raise PoolNotFoundError(pool_key=pool_key)
        
        sqrt_price_x96 = raw[0]
        tick = raw[1]
        liquidity = raw[2]
        
        return {
            "sqrt_price_x96": sqrt_price_x96,
            "tick": tick,
            "liquidity": liquidity,
            "fixed_rate": tick_to_fixed_rate(tick),
        }
    
    def get_vamm_state_raw(self, pool_key: PoolKey) -> tuple:
        """
        Get raw VAMM state from contract.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Tuple of (sqrtPriceX96, tick, compoundToken).
        """
        contract = self._client.vamm_manager
        pool_id = pool_key.get_pool_id()
        # getVAMMState takes bytes32 poolId, returns (tick, sqrtPriceX96, compoundToken)
        result = contract.functions.getVAMMState(pool_id).call()
        # Return as (sqrtPriceX96, tick, compoundToken) for compatibility
        return (result[1], result[0], result[2])
    
    def get_pool_info(self, pool_key: PoolKey) -> PoolInfo:
        """
        Get comprehensive pool information.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            PoolInfo with full pool details.
            
        Example:
            >>> info = client.pool.get_pool_info(pool)
            >>> print(f"Pool ID: {info.pool_id}")
            >>> print(f"Status: {info.status}")
            >>> print(f"Current tick: {info.tick}")
        """
        state = self.get_vamm_state(pool_key)
        
        # Determine pool status based on timestamps
        now = int(time.time())
        term_start = pool_key.term_start_timestamp
        term_end = pool_key.term_end_timestamp
        
        if now < term_start:
            status = "pending"
        elif now > term_end:
            status = "expired"
        else:
            status = "active"
        
        return PoolInfo(
            pool_id=pool_key.get_pool_id().hex(),
            pool_key=pool_key,
            sqrt_price_x96=state["sqrt_price_x96"],
            tick=state["tick"],
            liquidity=state["liquidity"],
            status=status,
        )
    
    def get_current_tick(self, pool_key: PoolKey) -> int:
        """
        Get current tick for a pool.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Current tick value.
        """
        state = self.get_vamm_state(pool_key)
        return state["tick"]
    
    def get_current_fixed_rate(self, pool_key: PoolKey) -> Decimal:
        """
        Get current fixed rate for a pool.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Fixed rate as Decimal (e.g., 0.05 = 5%).
            
        Example:
            >>> rate = client.pool.get_current_fixed_rate(pool)
            >>> print(f"Current fixed rate: {rate:.2%}")
        """
        state = self.get_vamm_state(pool_key)
        return state["fixed_rate"]
    
    def get_total_liquidity(self, pool_key: PoolKey) -> int:
        """
        Get total active liquidity in a pool.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Total liquidity units.
        """
        state = self.get_vamm_state(pool_key)
        return state["liquidity"]
    
    def get_pool_time_info(self, pool_key: PoolKey) -> dict:
        """
        Get time-related information for a pool.
        
        Args:
            pool_key: The pool to query.
            
        Returns:
            Dictionary with:
            - term_start: Start timestamp
            - term_end: End timestamp
            - duration_days: Total duration in days
            - time_remaining_days: Days until maturity (may be negative)
        """
        term_start = pool_key.term_start_timestamp
        term_end = pool_key.term_end_timestamp
        now = int(time.time())
        
        duration_days = (term_end - term_start) / 86400
        remaining_days = (term_end - now) / 86400
        
        return {
            "term_start": term_start,
            "term_end": term_end,
            "duration_days": duration_days,
            "time_remaining_days": remaining_days,
        }
    
    def is_pool_active(self, pool_key: PoolKey) -> bool:
        """
        Check if pool is currently active (within term period).
        
        Args:
            pool_key: The pool to check.
            
        Returns:
            True if pool is active.
        """
        now = int(time.time())
        return pool_key.term_start_timestamp <= now <= pool_key.term_end_timestamp
    
    def is_pool_expired(self, pool_key: PoolKey) -> bool:
        """
        Check if pool has expired (past term end).
        
        Args:
            pool_key: The pool to check.
            
        Returns:
            True if pool has expired.
        """
        return int(time.time()) > pool_key.term_end_timestamp
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Backend Integration (Optional)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def list_pools(
        self,
        sort: str = "tenor_asc",
        limit: int = 50,
        active_only: bool = True,
    ):
        """
        List pools from backend API.
        
        Requires backend API to be configured.
        
        Args:
            sort: Sort order ("tenor_asc", "tvl_desc", "volume_24h_desc", "apy_desc").
            limit: Maximum results (1-200).
            active_only: If True, only return active pools.
            
        Returns:
            List of PoolSummary objects from backend.
            
        Example:
            >>> pools = client.pool.list_pools(sort="tvl_desc")
            >>> for p in pools:
            ...     print(f"{p.pool_id[:16]}... TVL: ${p.tvl_usd}")
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured. Initialize client with backend_url.")
        
        if active_only:
            return self._client.backend.get_all_active_pools()
        else:
            pools, _ = self._client.backend.get_pools(sort=sort, limit=limit)
            return pools
    
    def get_price_history(
        self,
        pool_id: str,
        period: str = "1d",
        limit: int = 100,
    ):
        """
        Get historical price data from backend.
        
        Args:
            pool_id: Pool identifier.
            period: Data period ("1h", "1d", "1w").
            limit: Maximum data points.
            
        Returns:
            List of PricePoint objects.
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        return self._client.backend.get_pool_price_history(
            pool_id=pool_id,
            period=period,
            limit=limit,
        )
    
    def get_recent_trades(self, pool_id: str, limit: int = 50):
        """
        Get recent trades from backend.
        
        Args:
            pool_id: Pool identifier.
            limit: Maximum trades.
            
        Returns:
            List of TradeRecord objects.
        """
        if not self._client.has_backend:
            raise ValueError("Backend not configured")
        
        return self._client.backend.get_pool_trades(pool_id, limit)
