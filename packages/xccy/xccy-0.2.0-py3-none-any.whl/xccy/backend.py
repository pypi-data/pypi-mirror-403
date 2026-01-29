"""
Backend API client for historical and aggregated data.

This module provides optional access to the XCCY backend API (api.xccy.finance)
for data that requires off-chain indexing:
- Historical PnL snapshots
- Price history charts
- Aggregated pool metrics
- Trade history

For real-time on-chain data, use the contract methods directly.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
import httpx

from xccy.constants import DEFAULT_BACKEND_URL
from xccy.exceptions import BackendError


@dataclass
class PoolSummary:
    """
    Summary of a pool from the backend API.
    
    Attributes:
        pool_id: Unique pool identifier (bytes32 hash).
        token: Compound token address (aUSDC, aUSDT, etc.).
        underlying_token: Underlying asset address (USDC, USDT, etc.).
        term_start_timestamp_wad: Term start in WAD format.
        term_end_timestamp_wad: Term end in WAD format.
        tenor_seconds: Pool duration in seconds.
        tick_spacing: VAMM tick spacing.
        fee_wad: Trading fee in WAD.
        current_fixed_rate: Current fixed rate as decimal.
        current_floating_rate: Current variable/floating rate.
        tvl_usd: Total value locked in USD.
        volume_24h_usd: 24-hour trading volume in USD.
        apy: Annualized pool APY.
        status: Pool status ("active", "settling", "expired").
        category: Pool category (e.g., "aave", "compound").
    """
    
    pool_id: str
    token: Optional[str]
    underlying_token: Optional[str]
    term_start_timestamp_wad: str
    term_end_timestamp_wad: str
    tenor_seconds: Optional[str]
    tick_spacing: int
    fee_wad: Optional[str] = None
    current_fixed_rate: Decimal = Decimal(0)
    current_floating_rate: Decimal = Decimal(0)
    tvl_usd: Decimal = Decimal(0)
    volume_24h_usd: Decimal = Decimal(0)
    apy: Decimal = Decimal(0)
    status: str = "unknown"
    category: Optional[str] = None


@dataclass
class PnLSnapshot:
    """
    Historical PnL snapshot for an account.
    
    Attributes:
        timestamp: Snapshot time.
        pnl_usd: Cumulative PnL in USD.
        unrealized_pnl_usd: Unrealized PnL in USD.
        realized_pnl_usd: Realized PnL in USD.
    """
    
    timestamp: datetime
    pnl_usd: Decimal
    unrealized_pnl_usd: Decimal
    realized_pnl_usd: Decimal


@dataclass
class PricePoint:
    """
    Historical price point for a pool.
    
    Attributes:
        timestamp: Price timestamp.
        fixed_rate: Fixed rate at this time.
        variable_rate: Variable rate at this time.
        tick: Pool tick at this time.
    """
    
    timestamp: datetime
    fixed_rate: Decimal
    variable_rate: Decimal
    tick: int


@dataclass
class TradeRecord:
    """
    Historical trade record.
    
    Attributes:
        tx_hash: Transaction hash.
        timestamp: Trade timestamp.
        trader: Trader address.
        pool_id: Pool identifier.
        notional: Trade notional.
        fixed_rate: Rate at execution.
        is_fixed_taker: True if trader paid fixed.
        fee: Fee paid.
    """
    
    tx_hash: str
    timestamp: datetime
    trader: str
    pool_id: str
    notional: Decimal
    fixed_rate: Decimal
    is_fixed_taker: bool
    fee: Decimal


@dataclass
class UserPosition:
    """
    User position from backend API.
    
    Contains full position details including PnL, margin, and rates.
    
    Attributes:
        position_id: Position hash ID.
        pool_id: Pool identifier.
        account_id: Sub-account ID.
        isolated_margin_token: Isolated margin token address.
        tick_lower: Lower tick bound (for LP positions).
        tick_upper: Upper tick bound (for LP positions).
        liquidity: LP liquidity amount.
        fixed_token_balance: Fixed token balance.
        variable_token_balance: Variable token balance (notional).
        notional_value: Notional value in USD.
        upnl: Unrealized PnL.
        pnl: Total PnL.
        dv01: Dollar value of 1 basis point.
        entry_rate: Rate at position entry.
        current_rate: Current pool rate.
        status: Position status ("active", "settling", "settled").
        opened_at: Position open timestamp.
        rate: Implied rate.
        leverage: Position leverage.
        margin: Margin backing this position.
        is_settled: True if position is settled.
        settlement_cashflow: Settlement amount (if settled).
        asset: Asset token address.
        maturity: Maturity timestamp (seconds).
    """
    
    position_id: str  # Changed from int to str (hex hash)
    pool_id: str
    account_id: int
    isolated_margin_token: str
    tick_lower: int
    tick_upper: int
    liquidity: Decimal
    fixed_token_balance: Decimal
    variable_token_balance: Decimal
    notional_value: Decimal
    upnl: Decimal
    pnl: Decimal
    dv01: Decimal
    entry_rate: Optional[Decimal]
    current_rate: Optional[Decimal]
    status: str
    opened_at: Optional[datetime]
    rate: Optional[Decimal]
    leverage: Decimal
    margin: Decimal
    is_settled: bool
    settlement_cashflow: Optional[Decimal]
    asset: Optional[str] = None
    maturity: Optional[int] = None
    
    @property
    def is_lp(self) -> bool:
        """True if this is an LP position (has liquidity)."""
        return self.liquidity > 0
    
    @property
    def is_trader(self) -> bool:
        """True if this is a trader position (fixed/variable taker)."""
        return self.liquidity == 0 and self.variable_token_balance != 0
    
    @property
    def is_fixed_taker(self) -> bool:
        """True if position is paying fixed (receiving variable)."""
        return self.variable_token_balance > 0


@dataclass
class SubAccount:
    """
    Sub-account margin breakdown.
    
    Attributes:
        account_id: Sub-account ID.
        isolated_margin_token: Isolated margin token address.
        tokens: List of token collateral details.
        total_collateral_usd: Total collateral in USD.
    """
    
    account_id: int
    isolated_margin_token: str
    tokens: list[dict]
    total_collateral_usd: Decimal


@dataclass
class UserMetrics:
    """
    Aggregated user metrics from backend.
    
    Attributes:
        user_address: User wallet address.
        total_pnl: Total PnL in USD.
        total_upnl: Unrealized PnL in USD.
        total_collateral: Total collateral in USD.
        margin_ratio: Margin ratio (health factor).
        active_positions: Number of active positions.
        sub_accounts: List of sub-account breakdowns.
    """
    
    user_address: str
    total_pnl: Decimal
    total_upnl: Decimal
    total_collateral: Decimal
    margin_ratio: Decimal
    active_positions: int
    sub_accounts: list[SubAccount]


@dataclass
class SettlementRecord:
    """
    Settlement record for a matured position.
    
    Attributes:
        pool_id: Pool identifier.
        account_id: Sub-account ID.
        isolated_margin_token: Margin token address.
        asset: Asset symbol.
        amount: Settlement amount.
        settled_at: Settlement timestamp.
        tx_hash: Settlement transaction hash.
        settlement_price: Rate at settlement.
        notional_at_maturity: Notional at maturity.
    """
    
    pool_id: str
    account_id: int
    isolated_margin_token: str
    asset: str
    amount: Decimal
    settled_at: datetime
    tx_hash: str
    settlement_price: Optional[Decimal]
    notional_at_maturity: Decimal


class BackendClient:
    """
    Client for the XCCY backend API.
    
    Used for historical data and aggregated metrics that require indexing.
    
    Args:
        base_url: Backend API URL. Defaults to "https://api.xccy.finance".
        timeout: Request timeout in seconds.
        
    Example:
        >>> backend = BackendClient()
        >>> pools, _ = backend.get_pools(sort="tvl_desc")
        >>> for pool in pools:
        ...     print(f"{pool.pool_id[:16]}...: Rate {pool.current_fixed_rate}")
    """
    
    def __init__(
        self,
        base_url: str = DEFAULT_BACKEND_URL,
        timeout: float = 30.0,
    ):
        """Initialize the backend client."""
        # Append /v1 to base URL if not present
        base = base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = base + "/v1"
        self.base_url = base
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
        return self._client
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
    
    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        """
        Make a GET request to the backend.
        
        Args:
            endpoint: API endpoint (e.g., "/pools").
            params: Query parameters.
            
        Returns:
            JSON response as dict.
            
        Raises:
            BackendError: On HTTP or parsing errors.
        """
        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BackendError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                endpoint=endpoint,
            ) from e
        except httpx.RequestError as e:
            raise BackendError(f"Request failed: {e}", endpoint=endpoint) from e
        except Exception as e:
            raise BackendError(f"Unexpected error: {e}", endpoint=endpoint) from e
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Pool Endpoints
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_pools(
        self,
        sort: str = "tenor_asc",
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[list[PoolSummary], Optional[str]]:
        """
        Get list of pools with metrics.
        
        Args:
            sort: Sort order. Options:
                - "tenor_asc": By term duration ascending (default)
                - "tvl_desc": By TVL descending
                - "volume_24h_desc": By 24h volume descending  
                - "apy_desc": By APY descending
                - "created_at_asc": By creation time ascending
            limit: Maximum number of results (1-200).
            cursor: Pagination cursor from previous response.
            
        Returns:
            Tuple of (list of PoolSummary, next_cursor or None).
            
        Example:
            >>> pools, cursor = backend.get_pools(sort="tvl_desc", limit=10)
            >>> for pool in pools:
            ...     print(f"{pool.pool_id[:16]}... TVL: ${pool.tvl_usd:.0f}")
            >>> # Fetch next page
            >>> if cursor:
            ...     more_pools, _ = backend.get_pools(cursor=cursor)
        """
        params = {"sort": sort, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = self._get("/pools", params)
        
        # Backend returns {"response": [...]} or {data: {items: [...]}}
        data = response.get("data", response)
        items = data.get("items", data.get("response", []))
        next_cursor = data.get("next_cursor")
        
        pools = []
        for p in items:
            pools.append(PoolSummary(
                pool_id=p["pool_id"],
                token=p.get("compound_token") or p.get("token"),
                underlying_token=p.get("underlying_token"),
                term_start_timestamp_wad=p.get("term_start_timestamp_wad", "0"),
                term_end_timestamp_wad=p.get("term_end_timestamp_wad", "0"),
                tenor_seconds=p.get("tenor_seconds"),
                tick_spacing=int(p.get("tick_spacing", 1)),
                fee_wad=p.get("fee_wad"),
                current_fixed_rate=Decimal(p.get("current_fixed_rate", "0")),
                current_floating_rate=Decimal(p.get("current_floating_rate", "0")),
                tvl_usd=Decimal(p.get("tvl_usd") or p.get("liquidity_usd", "0")),
                volume_24h_usd=Decimal(p.get("volume_24h_usd", "0")),
                apy=Decimal(p.get("apy") or p.get("lp_apy", "0")),
                status=p.get("status", "unknown"),
                category=p.get("category"),
            ))
        
        return pools, next_cursor
    
    def get_all_active_pools(self) -> list[PoolSummary]:
        """
        Get all active pools (handles pagination automatically).
        
        Returns:
            List of all active PoolSummary objects.
            
        Example:
            >>> pools = backend.get_all_active_pools()
            >>> print(f"Found {len(pools)} active pools")
        """
        all_pools = []
        cursor = None
        
        while True:
            pools, cursor = self.get_pools(sort="tenor_asc", limit=200, cursor=cursor)
            
            # Filter to only active pools
            active = [p for p in pools if p.status == "active"]
            all_pools.extend(active)
            
            if not cursor or not pools:
                break
        
        return all_pools
    
    def get_pool_price_history(
        self,
        pool_id: str,
        period: str = "1d",
        limit: int = 100,
    ) -> list[PricePoint]:
        """
        Get historical price data for a pool.
        
        Args:
            pool_id: Pool identifier.
            period: Data period ("1h", "1d", "1w", "1m").
            limit: Maximum data points.
            
        Returns:
            List of PricePoint objects.
            
        Example:
            >>> history = backend.get_pool_price_history(pool_id, period="1d")
            >>> for point in history:
            ...     print(f"{point.timestamp}: {point.fixed_rate:.2%}")
        """
        data = self._get(
            f"/pools/{pool_id}/price-history",
            params={"period": period, "limit": limit},
        )
        
        return [
            PricePoint(
                timestamp=datetime.fromisoformat(p["timestamp"]),
                fixed_rate=Decimal(str(p.get("fixed_rate", 0))),
                variable_rate=Decimal(str(p.get("variable_rate", 0))),
                tick=int(p.get("tick", 0)),
            )
            for p in data.get("data", data) if isinstance(p, dict)
        ]
    
    def get_pool_trades(
        self,
        pool_id: str,
        limit: int = 50,
    ) -> list[TradeRecord]:
        """
        Get recent trades for a pool.
        
        Args:
            pool_id: Pool identifier.
            limit: Maximum number of trades.
            
        Returns:
            List of TradeRecord objects.
        """
        data = self._get(
            f"/pools/{pool_id}/trades",
            params={"limit": limit},
        )
        
        return [
            TradeRecord(
                tx_hash=t["tx_hash"],
                timestamp=datetime.fromisoformat(t["timestamp"]),
                trader=t["trader"],
                pool_id=pool_id,
                notional=Decimal(str(t.get("notional", 0))),
                fixed_rate=Decimal(str(t.get("fixed_rate", 0))),
                is_fixed_taker=t.get("is_fixed_taker", True),
                fee=Decimal(str(t.get("fee", 0))),
            )
            for t in data.get("trades", data) if isinstance(t, dict)
        ]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # User Endpoints
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_user_positions(
        self,
        address: str,
        account_id: Optional[int] = None,
        pool_id: Optional[str] = None,
    ) -> list[UserPosition]:
        """
        Get all positions for a user.
        
        Returns detailed position data including PnL, rates, and leverage.
        
        Args:
            address: User wallet address.
            account_id: Filter by sub-account ID (optional).
            pool_id: Filter by pool ID (optional).
            
        Returns:
            List of UserPosition objects.
            
        Example:
            >>> positions = backend.get_user_positions("0x...")
            >>> for pos in positions:
            ...     print(f"Pool {pos.pool_id[:16]}...: Notional ${pos.notional_value}")
            ...     print(f"  PnL: ${pos.pnl}, UPnL: ${pos.upnl}")
        """
        params = {"owner": address}
        if account_id is not None:
            params["accountId"] = account_id
        if pool_id is not None:
            params["poolId"] = pool_id
        
        response = self._get("/positions", params)
        data = response.get("data", response)
        positions_data = data.get("response", data.get("positions", []))
        
        positions = []
        for p in positions_data:
            # Parse opened_at, handling trailing Z for UTC
            opened_at = None
            if p.get("opened_at"):
                ts = p["opened_at"]
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                opened_at = datetime.fromisoformat(ts)
            
            positions.append(UserPosition(
                position_id=str(p.get("position_id", "")),
                pool_id=p["pool_id"],
                account_id=int(p.get("account_id", 0)),
                isolated_margin_token=p.get("isolated_margin_token", ""),
                tick_lower=int(p.get("tick_lower", 0)),
                tick_upper=int(p.get("tick_upper", 0)),
                liquidity=Decimal(p.get("liquidity", "0")),
                fixed_token_balance=Decimal(p.get("fixed_token_balance", "0")),
                variable_token_balance=Decimal(p.get("variable_token_balance", "0")),
                notional_value=Decimal(p.get("notional_value", "0")),
                upnl=Decimal(p.get("upnl", "0")),
                pnl=Decimal(p.get("pnl", "0")),
                dv01=Decimal(p.get("dv01", "0")),
                entry_rate=Decimal(p["entry_rate"]) if p.get("entry_rate") else None,
                current_rate=Decimal(p["current_rate"]) if p.get("current_rate") else None,
                status=p.get("status", "unknown"),
                opened_at=opened_at,
                rate=Decimal(p["rate"]) if p.get("rate") else None,
                leverage=Decimal(p.get("leverage", "0")),
                margin=Decimal(p.get("margin", "0")),
                is_settled=p.get("is_settled", False),
                settlement_cashflow=Decimal(p["settlement_cashflow"]) if p.get("settlement_cashflow") else None,
                asset=p.get("asset"),
                maturity=int(p["maturity"]) if p.get("maturity") else None,
            ))
        
        return positions
    
    def get_user_active_positions(self, address: str) -> list[UserPosition]:
        """
        Get only active (non-settled) positions.
        
        Args:
            address: User wallet address.
            
        Returns:
            List of active UserPosition objects.
        """
        all_positions = self.get_user_positions(address)
        return [p for p in all_positions if not p.is_settled and p.status != "settled"]
    
    def get_user_metrics(self, address: str) -> UserMetrics:
        """
        Get aggregated user metrics.
        
        Args:
            address: User wallet address.
            
        Returns:
            UserMetrics with totals and sub-account breakdown.
            
        Example:
            >>> metrics = backend.get_user_metrics("0x...")
            >>> print(f"Total PnL: ${metrics.total_pnl}")
            >>> print(f"Collateral: ${metrics.total_collateral}")
        """
        response = self._get(f"/users/{address}/metrics")
        data = response.get("data", response)
        
        # Parse sub-accounts
        sub_accounts = []
        for sub in data.get("sub_accounts", []):
            sub_accounts.append(SubAccount(
                account_id=int(sub.get("account_id", 0)),
                isolated_margin_token=sub.get("isolated_margin_token", ""),
                tokens=sub.get("tokens", []),
                total_collateral_usd=Decimal(sub.get("total_collateral_usd", "0")),
            ))
        
        return UserMetrics(
            user_address=data.get("user_address", address),
            total_pnl=Decimal(data.get("total_pnl", "0")),
            total_upnl=Decimal(data.get("total_upnl", "0")),
            total_collateral=Decimal(data.get("total_collateral", "0")),
            margin_ratio=Decimal(data.get("margin_ratio", "0")),
            active_positions=int(data.get("active_positions", 0)),
            sub_accounts=sub_accounts,
        )
    
    def get_user_settlements(
        self,
        address: str,
        account_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[SettlementRecord]:
        """
        Get settlement history for a user.
        
        Args:
            address: User wallet address.
            account_id: Filter by sub-account ID (optional).
            limit: Maximum number of records.
            
        Returns:
            List of SettlementRecord objects.
        """
        params = {"limit": limit}
        if account_id is not None:
            params["account_id"] = account_id
        
        response = self._get(f"/users/{address}/settlements", params)
        data = response.get("data", response)
        items = data.get("items", [])
        
        return [
            SettlementRecord(
                pool_id=s["pool_id"],
                account_id=int(s.get("account_id", 0)),
                isolated_margin_token=s.get("isolated_margin_token", ""),
                asset=s.get("asset", ""),
                amount=Decimal(s.get("amount", "0")),
                settled_at=datetime.fromisoformat(s["settled_at"]) if s.get("settled_at") else datetime.now(),
                tx_hash=s.get("tx_hash", ""),
                settlement_price=Decimal(s["settlement_price"]) if s.get("settlement_price") else None,
                notional_at_maturity=Decimal(s.get("notional_at_maturity", "0")),
            )
            for s in items
        ]
    
    def get_user_pnl_history(
        self,
        address: str,
        period: str = "1m",
    ) -> list[PnLSnapshot]:
        """
        Get historical PnL snapshots for a user.
        
        Args:
            address: User wallet address.
            period: History period ("1d", "1w", "1m", "3m", "1y").
            
        Returns:
            List of PnLSnapshot objects.
            
        Example:
            >>> history = backend.get_user_pnl_history("0x...", period="1m")
            >>> for snap in history:
            ...     print(f"{snap.timestamp.date()}: ${snap.pnl_usd:.2f}")
        """
        data = self._get(
            f"/users/{address}/pnl-history",
            params={"period": period},
        )
        
        return [
            PnLSnapshot(
                timestamp=datetime.fromisoformat(s["timestamp"]),
                pnl_usd=Decimal(str(s.get("pnl_usd", 0))),
                unrealized_pnl_usd=Decimal(str(s.get("unrealized_pnl_usd", 0))),
                realized_pnl_usd=Decimal(str(s.get("realized_pnl_usd", 0))),
            )
            for s in data.get("snapshots", data) if isinstance(s, dict)
        ]
    
    def get_user_performance(self, address: str) -> dict[str, Any]:
        """
        Get user performance metrics.
        
        Args:
            address: User wallet address.
            
        Returns:
            Dictionary with performance metrics:
            - total_pnl_usd: Cumulative PnL
            - win_rate: Percentage of profitable trades
            - avg_trade_duration: Average position duration
            - total_volume_usd: Total trading volume
            
        Example:
            >>> perf = backend.get_user_performance("0x...")
            >>> print(f"Win rate: {perf['win_rate']:.1%}")
        """
        return self._get(f"/users/{address}/performance")
    
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Rate Endpoints
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_rate_comparison(
        self,
        pool_id: str,
        period: str = "1d",
    ) -> dict[str, Any]:
        """
        Get fixed vs variable rate comparison over time.
        
        Args:
            pool_id: Pool identifier.
            period: Comparison period.
            
        Returns:
            Dictionary with rate comparison data.
        """
        return self._get(f"/pools/{pool_id}/rates", params={"period": period})
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Health Check
    # ═══════════════════════════════════════════════════════════════════════════
    
    def health_check(self) -> bool:
        """
        Check if the backend is reachable.
        
        Returns:
            True if backend is healthy, False otherwise.
        """
        try:
            self._get("/health")
            return True
        except BackendError:
            return False
