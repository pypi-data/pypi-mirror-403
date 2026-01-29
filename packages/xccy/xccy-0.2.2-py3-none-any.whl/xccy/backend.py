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


@dataclass
class CollateralInfo:
    """
    User's collateral balance for a token.
    
    Attributes:
        token: Token address.
        symbol: Token symbol (e.g., "USDC").
        name: Token name.
        decimals: Token decimals.
        amount: Raw balance amount.
        amount_usd: Balance value in USD (scaled by 10^18).
    """
    
    token: str
    symbol: str
    name: str
    decimals: int
    amount: Decimal
    amount_usd: Decimal


@dataclass
class CollateralToken:
    """
    Supported collateral token info.
    
    Attributes:
        token: Token address.
        symbol: Token symbol.
        name: Token name.
        decimals: Token decimals.
        discount: Haircut discount (1.0 = no discount).
    """
    
    token: str
    symbol: str
    name: str
    decimals: int
    discount: Decimal


@dataclass
class LiquidityTrade:
    """
    Liquidity provision (mint/burn) trade record.
    
    Attributes:
        timestamp: Trade timestamp.
        tx_hash: Transaction hash.
        pool_id: Pool identifier.
        owner: LP address.
        account_id: Sub-account ID.
        isolated_margin_token: Margin token address.
        tick_lower: Lower tick of position.
        tick_upper: Upper tick of position.
        liquidity: Liquidity amount.
        notional: Notional value.
        notional_usd: Notional in USD.
    """
    
    timestamp: datetime
    tx_hash: str
    pool_id: str
    owner: str
    account_id: int
    isolated_margin_token: str
    tick_lower: int
    tick_upper: int
    liquidity: Decimal
    notional: Decimal
    notional_usd: Decimal


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
        resolution: str = "1h",
        limit: int = 100,
        offset: int = 0,
    ) -> list[PricePoint]:
        """
        Get historical price data for a pool.
        
        Args:
            pool_id: Pool identifier.
            resolution: Data resolution ("5m", "15m", "1h", "8h", "1d", "1w").
            limit: Maximum data points (default 100, max 1000).
            offset: Pagination offset.
            
        Returns:
            List of PricePoint objects.
            
        Example:
            >>> history = backend.get_pool_price_history(pool_id, resolution="1h")
            >>> for point in history:
            ...     print(f"{point.timestamp}: {point.fixed_rate:.2%}")
        """
        response = self._get("/price-history", params={
            "poolId": pool_id,
            "resolution": resolution,
            "limit": limit,
            "offset": offset,
        })
        
        items = response.get("response", [])
        return [
            PricePoint(
                timestamp=datetime.fromtimestamp(p["timestamp"]),
                fixed_rate=Decimal(str(p.get("rate", 0))),
                variable_rate=Decimal(0),  # Not provided by API
                tick=0,  # Not provided by API
            )
            for p in items if isinstance(p, dict)
        ]
    
    def get_pool_trades(
        self,
        pool_id: Optional[str] = None,
        owner: Optional[str] = None,
        account_id: Optional[int] = None,
        isolated_margin_token: Optional[str] = None,
    ) -> list[TradeRecord]:
        """
        Get trades (swaps) with optional filters.
        
        Args:
            pool_id: Filter by pool ID.
            owner: Filter by trader address.
            account_id: Filter by sub-account ID.
            isolated_margin_token: Filter by margin token.
            
        Returns:
            List of TradeRecord objects.
            
        Example:
            >>> trades = backend.get_pool_trades(pool_id="0x...")
            >>> for t in trades:
            ...     print(f"{t.notional} @ {t.fixed_rate:.2%}")
        """
        params: dict = {}
        if pool_id:
            params["poolId"] = pool_id
        if owner:
            params["owner"] = owner
        if account_id is not None:
            params["accountId"] = account_id
        if isolated_margin_token:
            params["isolatedMarginToken"] = isolated_margin_token
        
        response = self._get("/trades", params)
        items = response.get("response", [])
        
        return [
            TradeRecord(
                tx_hash=t.get("transactionHash", ""),
                timestamp=datetime.fromtimestamp(t["timestamp"]),
                trader=t.get("owner", ""),
                pool_id=t.get("poolId", pool_id or ""),
                notional=Decimal(str(t.get("notional", 0))),
                fixed_rate=Decimal(str(t.get("rate", 0))),
                is_fixed_taker=Decimal(str(t.get("variableTokenDelta", 0))) < 0,
                fee=Decimal(str(t.get("cumulativeFeeIncurred", 0))),
            )
            for t in items if isinstance(t, dict)
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
            positions.append(UserPosition(
                position_id=str(p.get("position_id", p.get("positionId", ""))),
                pool_id=p.get("pool_id", p.get("poolId", "")),
                account_id=int(p.get("account_id", p.get("accountId", 0))),
                isolated_margin_token=p.get("isolated_margin_token", p.get("isolatedMarginToken", "")),
                tick_lower=int(p.get("tick_lower", p.get("tickLower", 0))),
                tick_upper=int(p.get("tick_upper", p.get("tickUpper", 0))),
                liquidity=Decimal(p.get("liquidity", "0")),
                fixed_token_balance=Decimal(p.get("fixed_token_balance", p.get("fixedTokenBalance", "0"))),
                variable_token_balance=Decimal(p.get("variable_token_balance", p.get("variableTokenBalance", "0"))),
                notional_value=Decimal(p.get("notional_value", p.get("notional_usd", p.get("notional", "0")))),
                upnl=Decimal(p.get("upnl", "0")),
                pnl=Decimal(p.get("pnl", "0")),
                dv01=Decimal(p.get("dv01", "0")),
                entry_rate=Decimal(p["entry_rate"]) if p.get("entry_rate") else None,
                current_rate=Decimal(p["current_rate"]) if p.get("current_rate") else None,
                status=p.get("status", "active"),
                opened_at=None,
                rate=Decimal(p["rate"]) if p.get("rate") else None,
                leverage=Decimal(p.get("leverage", "0")),
                margin=Decimal(p.get("margin", "0")),
                is_settled=p.get("is_settled", p.get("isSettled", False)),
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
    
    def get_collateral(
        self,
        address: str,
        account_id: int = 0,
        isolated_margin_token: str = "0x0000000000000000000000000000000000000000",
    ) -> list[CollateralInfo]:
        """
        Get user's collateral balances.
        
        Args:
            address: User wallet address.
            account_id: Sub-account ID (default 0).
            isolated_margin_token: Margin token address (default zero = cross-margin).
            
        Returns:
            List of CollateralInfo with token balances.
            
        Example:
            >>> collateral = backend.get_collateral("0x...")
            >>> for c in collateral:
            ...     print(f"{c.symbol}: {c.amount} (${float(c.amount_usd) / 1e18:.2f})")
        """
        response = self._get("/collateral", params={
            "owner": address,
            "accountId": account_id,
            "isolatedMarginToken": isolated_margin_token,
        })
        items = response.get("response", [])
        
        return [
            CollateralInfo(
                token=c.get("token", ""),
                symbol=c.get("token_metadata", {}).get("symbol", ""),
                name=c.get("token_metadata", {}).get("name", ""),
                decimals=int(c.get("token_metadata", {}).get("decimals", 18)),
                amount=Decimal(str(c.get("amount", 0))),
                amount_usd=Decimal(str(c.get("amount_usd", 0))),
            )
            for c in items if isinstance(c, dict)
        ]
    
    def get_sub_accounts(self, address: str) -> list[SubAccount]:
        """
        Get all sub-accounts for a user.
        
        Args:
            address: User wallet address.
            
        Returns:
            List of SubAccount objects.
            
        Example:
            >>> subs = backend.get_sub_accounts("0x...")
            >>> for s in subs:
            ...     print(f"Account {s.account_id}: {s.isolated_margin_token}")
        """
        response = self._get("/sub-accounts", params={"owner": address})
        items = response.get("response", [])
        
        return [
            SubAccount(
                account_id=int(s.get("accountId", 0)),
                isolated_margin_token=s.get("isolatedMarginToken", ""),
                tokens=[],
                total_collateral_usd=Decimal(0),
            )
            for s in items if isinstance(s, dict)
        ]
    
    def get_user_settlements(
        self,
        address: str,
        account_id: int = 0,
        isolated_margin_token: str = "0x0000000000000000000000000000000000000000",
        pool_id: Optional[str] = None,
    ) -> list[SettlementRecord]:
        """
        Get settled positions for a user.
        
        Args:
            address: User wallet address.
            account_id: Sub-account ID (default 0).
            isolated_margin_token: Margin token address (default zero = cross-margin).
            pool_id: Filter by pool ID (optional).
            
        Returns:
            List of SettlementRecord objects.
        """
        params: dict = {
            "owner": address,
            "accountId": account_id,
            "isolatedMarginToken": isolated_margin_token,
        }
        if pool_id:
            params["poolId"] = pool_id
        
        response = self._get("/settled-positions", params)
        items = response.get("response", [])
        
        return [
            SettlementRecord(
                pool_id=s.get("poolId", ""),
                account_id=int(s.get("accountId", 0)),
                isolated_margin_token=s.get("isolatedMarginToken", ""),
                asset=s.get("asset", ""),
                amount=Decimal(s.get("amount", "0")),
                settled_at=datetime.fromtimestamp(s["timestamp"]) if s.get("timestamp") else datetime.now(),
                tx_hash=s.get("transactionHash", ""),
                settlement_price=Decimal(s["settlementPrice"]) if s.get("settlementPrice") else None,
                notional_at_maturity=Decimal(s.get("notional", "0")),
            )
            for s in items
        ]
    
    def get_user_pnl_history(
        self,
        address: str,
        account_id: Optional[int] = None,
        isolated_margin_token: str = "0x0000000000000000000000000000000000000000",
        time: Optional[str] = None,
    ) -> list[PnLSnapshot]:
        """
        Get historical PnL snapshots for a user.
        
        Args:
            address: User wallet address.
            account_id: Sub-account ID (optional).
            isolated_margin_token: Margin token address (default zero = cross-margin).
            time: Time filter (optional).
            
        Returns:
            List of PnLSnapshot objects.
            
        Example:
            >>> history = backend.get_user_pnl_history("0x...")
            >>> for snap in history:
            ...     print(f"{snap.timestamp.date()}: ${snap.pnl_usd:.2f}")
        """
        params: dict = {
            "owner": address,
            "isolatedMarginToken": isolated_margin_token,
        }
        if account_id is not None:
            params["accountId"] = account_id
        if time:
            params["time"] = time
        
        response = self._get("/pnl-history", params)
        items = response.get("response", [])
        
        return [
            PnLSnapshot(
                timestamp=datetime.fromtimestamp(s["timestamp"]),
                pnl_usd=Decimal(str(s.get("amount", 0))),
                unrealized_pnl_usd=Decimal(0),  # Not separated in API
                realized_pnl_usd=Decimal(0),  # Not separated in API
            )
            for s in items if isinstance(s, dict)
        ]
    
    def get_liquidity_trades(
        self,
        pool_id: Optional[str] = None,
        owner: Optional[str] = None,
        account_id: Optional[int] = None,
        isolated_margin_token: Optional[str] = None,
    ) -> list[LiquidityTrade]:
        """
        Get liquidity provision trades (mint/burn).
        
        Args:
            pool_id: Filter by pool ID.
            owner: Filter by LP address.
            account_id: Filter by sub-account ID.
            isolated_margin_token: Filter by margin token.
            
        Returns:
            List of LiquidityTrade objects.
            
        Example:
            >>> trades = backend.get_liquidity_trades(pool_id="0x...")
            >>> for t in trades:
            ...     print(f"LP: {t.owner[:10]}... notional={t.notional}")
        """
        params: dict = {}
        if pool_id:
            params["poolId"] = pool_id
        if owner:
            params["owner"] = owner
        if account_id is not None:
            params["accountId"] = account_id
        if isolated_margin_token:
            params["isolatedMarginToken"] = isolated_margin_token
        
        response = self._get("/liquidity-trades", params)
        items = response.get("response", [])
        
        return [
            LiquidityTrade(
                timestamp=datetime.fromtimestamp(t["timestamp"]),
                tx_hash=t.get("transactionHash", ""),
                pool_id=t.get("poolId", ""),
                owner=t.get("owner", ""),
                account_id=int(t.get("accountId", 0)),
                isolated_margin_token=t.get("isolatedMarginToken", ""),
                tick_lower=int(t.get("tickLower", 0)),
                tick_upper=int(t.get("tickUpper", 0)),
                liquidity=Decimal(str(t.get("liquidity", 0))),
                notional=Decimal(str(t.get("notional", 0))),
                notional_usd=Decimal(str(t.get("notional_usd", 0))),
            )
            for t in items if isinstance(t, dict)
        ]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Global Endpoints
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_collateral_tokens(self) -> list[CollateralToken]:
        """
        Get list of supported collateral tokens.
        
        Returns:
            List of CollateralToken objects with discount info.
            
        Example:
            >>> tokens = backend.get_collateral_tokens()
            >>> for t in tokens:
            ...     print(f"{t.symbol}: discount={t.discount}")
        """
        response = self._get("/collateral-tokens")
        items = response.get("response", [])
        
        return [
            CollateralToken(
                token=t.get("token", ""),
                symbol=t.get("token_metadata", {}).get("symbol", ""),
                name=t.get("token_metadata", {}).get("name", ""),
                decimals=int(t.get("token_metadata", {}).get("decimals", 18)),
                discount=Decimal(str(t.get("discount", "1"))),
            )
            for t in items if isinstance(t, dict)
        ]
    
    def get_apr_history(
        self,
        asset: str,
        resolution: str = "1h",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Get APR rate history for an asset.
        
        Args:
            asset: Asset address.
            resolution: Data resolution ("5m", "15m", "1h", "8h", "1d", "1w").
            limit: Maximum data points (default 100, max 1000).
            offset: Pagination offset.
            
        Returns:
            List of dicts with timestamp and rate.
            
        Example:
            >>> history = backend.get_apr_history("0x...", resolution="1d")
            >>> for h in history:
            ...     print(f"{h['timestamp']}: {h['rate']}")
        """
        response = self._get("/apr-rate-history", params={
            "asset": asset,
            "resolution": resolution,
            "limit": limit,
            "offset": offset,
        })
        return response.get("response", [])
    
    def get_global_metrics(self) -> dict[str, Any]:
        """
        Get global protocol metrics.
        
        Returns:
            Dictionary with protocol-wide stats:
            - total_liquidity_usd: Total liquidity
            - total_tvl_usd: Total value locked
            - total_volume_24h_usd: 24h trading volume
            - total_positions: Number of positions
            - total_users: Number of unique users
            - active_pools: Number of active pools
            - supported_assets: List of supported asset symbols
            
        Example:
            >>> metrics = backend.get_global_metrics()
            >>> print(f"TVL: ${metrics['data']['total_tvl_usd']}")
        """
        return self._get("/metrics")
    
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
