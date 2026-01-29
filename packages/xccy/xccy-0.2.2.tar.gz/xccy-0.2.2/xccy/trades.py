"""
Trade history manager for XCCY Protocol.

This module provides access to historical trade data through the backend API.
For live trade streaming, use the TradeStream class from xccy.stream.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from xccy.backend import TradeRecord
from xccy.exceptions import BackendError

if TYPE_CHECKING:
    from xccy.client import XccyClient


class TradesManager:
    """
    Manager for querying historical trade data.
    
    Wraps the backend API endpoints for trade history, providing
    convenient methods for fetching pool trades with optional filtering.
    
    Args:
        client: XccyClient instance.
        
    Example:
        >>> # Get recent trades for a pool
        >>> trades, cursor = client.trades.get_pool_trades(pool_id, limit=50)
        >>> for trade in trades:
        ...     print(f"{trade.timestamp}: {trade.notional} @ {trade.fixed_rate:.2%}")
        >>> 
        >>> # Get user's trades
        >>> my_trades = client.trades.get_user_trades(pool_id, "0x...")
    """
    
    def __init__(self, client: "XccyClient") -> None:
        """Initialize the trades manager."""
        self._client = client
    
    def get_pool_trades(
        self,
        pool_id: str,
        user_address: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[list[TradeRecord], Optional[str]]:
        """
        Get historical trades for a pool.
        
        Fetches trade records from the backend API with optional filtering
        by user address and pagination support.
        
        Args:
            pool_id: Pool identifier (bytes32 hex string).
            user_address: Optional filter by trader address.
            limit: Maximum number of trades to return (1-200).
            cursor: Pagination cursor from previous response.
            
        Returns:
            Tuple of (list of TradeRecord, next_cursor or None).
            Use next_cursor to fetch the next page of results.
            
        Raises:
            BackendError: If backend is not configured or request fails.
            
        Example:
            >>> # Get all trades
            >>> trades, cursor = client.trades.get_pool_trades(pool_id)
            >>> 
            >>> # Get specific user's trades
            >>> trades, _ = client.trades.get_pool_trades(
            ...     pool_id,
            ...     user_address="0x...",
            ...     limit=100,
            ... )
            >>> 
            >>> # Paginate through all trades
            >>> all_trades = []
            >>> cursor = None
            >>> while True:
            ...     trades, cursor = client.trades.get_pool_trades(pool_id, cursor=cursor)
            ...     all_trades.extend(trades)
            ...     if not cursor:
            ...         break
        """
        if not self._client.has_backend:
            raise BackendError("Backend not configured", endpoint="trades")
        
        backend = self._client.backend
        
        # Build params
        params = {"limit": limit}
        if user_address:
            params["user_address"] = user_address
        if cursor:
            params["cursor"] = cursor
        
        # Make request
        response = backend._get(f"/pools/{pool_id}/trades", params)
        
        # Parse response
        data = response.get("data", response)
        items = data.get("items", [])
        next_cursor = data.get("next_cursor")
        
        # Parse trades
        trades = []
        for t in items:
            # Parse timestamp
            ts = t.get("timestamp", "")
            if isinstance(ts, str):
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                timestamp = datetime.fromisoformat(ts)
            else:
                timestamp = datetime.fromtimestamp(ts)
            
            # Calculate notional from variable_token_delta
            variable_delta_raw = t.get("variable_token_delta")
            variable_delta = int(variable_delta_raw) if variable_delta_raw else 0
            notional = Decimal(abs(variable_delta))
            
            # Determine if fixed taker (positive variable = receiving variable = paying fixed)
            is_fixed_taker = variable_delta > 0
            
            # Parse fee and rate
            fee_raw = t.get("cumulative_fee_incurred")
            fee = Decimal(str(fee_raw)) if fee_raw else Decimal(0)
            rate_raw = t.get("fixed_rate")
            rate = Decimal(str(rate_raw)) if rate_raw else Decimal(0)
            
            trades.append(TradeRecord(
                tx_hash=t.get("tx_hash", ""),
                timestamp=timestamp,
                trader=t.get("sender", ""),
                pool_id=pool_id,
                notional=notional,
                fixed_rate=rate,
                is_fixed_taker=is_fixed_taker,
                fee=fee,
            ))
        
        return trades, next_cursor
    
    def get_user_trades(
        self,
        pool_id: str,
        user_address: str,
        limit: int = 100,
    ) -> list[TradeRecord]:
        """
        Get all trades for a specific user in a pool.
        
        Convenience method that filters trades by user address.
        
        Args:
            pool_id: Pool identifier.
            user_address: User's wallet address.
            limit: Maximum number of trades.
            
        Returns:
            List of TradeRecord objects for the user.
            
        Example:
            >>> my_trades = client.trades.get_user_trades(pool_id, my_address)
            >>> total_volume = sum(t.notional for t in my_trades)
            >>> print(f"My total volume: {total_volume}")
        """
        trades, _ = self.get_pool_trades(
            pool_id=pool_id,
            user_address=user_address,
            limit=limit,
        )
        return trades
    
    def get_all_pool_trades(
        self,
        pool_id: str,
        user_address: Optional[str] = None,
        max_trades: int = 1000,
    ) -> list[TradeRecord]:
        """
        Get all trades for a pool (handles pagination automatically).
        
        Iterates through all pages until no more trades or max_trades reached.
        
        Args:
            pool_id: Pool identifier.
            user_address: Optional filter by user.
            max_trades: Maximum total trades to fetch.
            
        Returns:
            List of all TradeRecord objects.
            
        Example:
            >>> all_trades = client.trades.get_all_pool_trades(pool_id)
            >>> print(f"Total trades: {len(all_trades)}")
        """
        all_trades: list[TradeRecord] = []
        cursor: Optional[str] = None
        
        while len(all_trades) < max_trades:
            remaining = max_trades - len(all_trades)
            limit = min(200, remaining)
            
            trades, cursor = self.get_pool_trades(
                pool_id=pool_id,
                user_address=user_address,
                limit=limit,
                cursor=cursor,
            )
            
            all_trades.extend(trades)
            
            if not cursor or not trades:
                break
        
        return all_trades
