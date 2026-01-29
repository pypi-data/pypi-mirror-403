"""
Data types for XCCY Protocol.

This module defines the core data structures used throughout the SDK,
matching the Solidity structs in the smart contracts.
"""

from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal
from eth_typing import ChecksumAddress, HexStr


@dataclass(frozen=True)
class AccountId:
    """
    Unique identifier for a user's sub-account.
    
    One wallet can own multiple sub-accounts, each with independent:
    - Margin balances
    - Positions
    - Health factor / liquidation risk
    
    Attributes:
        owner: The wallet address that owns this account.
        account_id: Sub-account index (0, 1, 2, ...).
        isolated_margin_token: If set, account operates in isolated margin mode
            with only this token as collateral (no discount factor applied).
            If None, account operates in cross-margin mode.
    
    Example:
        >>> # Cross-margin account
        >>> main = AccountId(owner="0x...", account_id=0, isolated_margin_token=None)
        >>> 
        >>> # Isolated margin account (USDC only)
        >>> isolated = AccountId(
        ...     owner="0x...",
        ...     account_id=1,
        ...     isolated_margin_token="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
        ... )
    """
    
    owner: str
    account_id: int
    isolated_margin_token: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate account parameters."""
        from web3 import Web3
        
        owner_lower = self.owner.lower()
        if not owner_lower.startswith("0x") or len(self.owner) != 42:
            raise ValueError(f"Invalid owner address: {self.owner}")
        
        # Validate checksum if mixed case (not all lower or all upper)
        if self.owner != owner_lower and self.owner != self.owner.upper():
            if not Web3.is_checksum_address(self.owner):
                raise ValueError(f"Invalid checksum for owner: {self.owner}")
        
        if self.account_id < 0:
            raise ValueError(f"account_id must be non-negative: {self.account_id}")
        
        if self.isolated_margin_token is not None:
            token_lower = self.isolated_margin_token.lower()
            if not token_lower.startswith("0x") or len(self.isolated_margin_token) != 42:
                raise ValueError(f"Invalid isolated_margin_token: {self.isolated_margin_token}")
            # Validate checksum if mixed case
            if (self.isolated_margin_token != token_lower and 
                self.isolated_margin_token != self.isolated_margin_token.upper()):
                if not Web3.is_checksum_address(self.isolated_margin_token):
                    raise ValueError(f"Invalid checksum for isolated_margin_token: {self.isolated_margin_token}")
    
    def to_tuple(self) -> tuple[str, int, str]:
        """
        Convert to tuple for contract calls.
        
        Returns:
            Tuple of (owner, account_id, isolated_margin_token).
            Uses zero address if isolated_margin_token is None.
        """
        return (
            self.owner,
            self.account_id,
            self.isolated_margin_token or "0x0000000000000000000000000000000000000000",
        )
    
    def get_hash(self) -> bytes:
        """
        Compute the account hash used in contract storage.
        
        Returns:
            Keccak256 hash of packed (owner, account_id, isolated_margin_token).
        """
        from web3 import Web3
        return Web3.solidity_keccak(
            ["address", "uint96", "address"],
            list(self.to_tuple())
        )


@dataclass(frozen=True)
class PoolKey:
    """
    Unique identifier for an IRS pool.
    
    A pool represents a market for trading interest rates on a specific
    underlying asset over a defined term period.
    
    Attributes:
        underlying_asset: The payment token (e.g., USDC).
        compound_token: The yield-bearing token for APR calculation (e.g., aUSDC).
        term_start_timestamp_wad: Term start time in WAD format (timestamp * 1e18).
        term_end_timestamp_wad: Term end time in WAD format (timestamp * 1e18).
        fee_wad: Pool fee in WAD format (e.g., 0.003e18 = 0.3%).
        tick_spacing: Minimum tick increment for LP positions.
    
    Example:
        >>> pool = PoolKey(
        ...     underlying_asset="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # USDC
        ...     compound_token="0x625E7708f30cA75bfd92586e17077590C60eb4cD",   # aUSDC
        ...     term_start_timestamp_wad=1704067200 * 10**18,
        ...     term_end_timestamp_wad=1735689600 * 10**18,
        ...     fee_wad=int(0.003 * 10**18),
        ...     tick_spacing=60,
        ... )
    """
    
    underlying_asset: str
    compound_token: str
    term_start_timestamp_wad: int
    term_end_timestamp_wad: int
    fee_wad: int
    tick_spacing: int
    
    def __post_init__(self) -> None:
        """Validate pool key parameters."""
        if self.term_end_timestamp_wad <= self.term_start_timestamp_wad:
            raise ValueError("term_end must be after term_start")
        if self.fee_wad <= 0:
            raise ValueError("fee_wad must be positive")
        if self.tick_spacing <= 0:
            raise ValueError("tick_spacing must be positive")
    
    def to_tuple(self) -> tuple:
        """Convert to tuple for contract calls."""
        return (
            self.underlying_asset,
            self.compound_token,
            self.term_start_timestamp_wad,
            self.term_end_timestamp_wad,
            self.fee_wad,
            self.tick_spacing,
        )
    
    def get_pool_id(self) -> bytes:
        """
        Compute the pool ID hash.
        
        Returns:
            Keccak256 hash of encoded pool key.
        """
        from web3 import Web3
        from eth_abi import encode
        
        encoded = encode(
            ["address", "address", "uint256", "uint256", "uint256", "int24"],
            list(self.to_tuple())
        )
        return Web3.keccak(encoded)
    
    @property
    def term_start_timestamp(self) -> int:
        """Term start as Unix timestamp (seconds)."""
        return self.term_start_timestamp_wad // (10**18)
    
    @property
    def term_end_timestamp(self) -> int:
        """Term end as Unix timestamp (seconds)."""
        return self.term_end_timestamp_wad // (10**18)
    
    @property
    def term_duration_seconds(self) -> int:
        """Duration of the term in seconds."""
        return self.term_end_timestamp - self.term_start_timestamp


@dataclass
class SwapParams:
    """
    Parameters for executing a swap.
    
    Attributes:
        account: The account executing the swap.
        amount_specified: Notional amount. Positive = exact input, negative = exact output.
        sqrt_price_limit_x96: Price limit in Q64.96 format. Acts as slippage protection.
        tick_lower: Lower tick of the position range.
        tick_upper: Upper tick of the position range.
    
    Example:
        >>> params = SwapParams(
        ...     account=account,
        ...     amount_specified=10_000 * 10**6,  # 10k USDC notional
        ...     sqrt_price_limit_x96=0,  # No limit
        ...     tick_lower=-6930,
        ...     tick_upper=-6900,
        ... )
    """
    
    account: AccountId
    amount_specified: int
    sqrt_price_limit_x96: int
    tick_lower: int
    tick_upper: int
    
    def to_tuple(self) -> tuple:
        """Convert to tuple for contract calls."""
        return (
            self.account.to_tuple(),
            self.amount_specified,
            self.sqrt_price_limit_x96,
            self.tick_lower,
            self.tick_upper,
        )


@dataclass
class SwapResult:
    """
    Result of a swap execution.
    
    Attributes:
        fixed_token_delta: Change in fixed token balance.
        variable_token_delta: Change in variable token balance (= notional traded).
        cumulative_fee_incurred: Total fees paid.
        fixed_token_delta_unbalanced: Unbalanced fixed token change (for margin calc).
        position_margin_requirement: Margin required after the swap.
        price_after_swap: Price (sqrtPriceX96) after the swap execution.
        transaction_hash: Hash of the executed transaction.
        gas_used: Gas consumed by the transaction.
    """
    
    fixed_token_delta: int
    variable_token_delta: int
    cumulative_fee_incurred: int
    fixed_token_delta_unbalanced: int
    position_margin_requirement: int
    price_after_swap: int = 0
    transaction_hash: Optional[str] = None
    gas_used: int = 0


@dataclass
class PositionInfo:
    """
    Information about a user's position in a pool.
    
    Attributes:
        pool_id: The pool identifier.
        account: The account owning this position.
        tick_lower: Lower tick boundary.
        tick_upper: Upper tick boundary.
        liquidity: Amount of liquidity (for LP positions).
        fixed_token_balance: Current fixed token balance.
        variable_token_balance: Current variable token balance (notional).
        accumulated_fees: Fees earned (for LP positions).
    """
    
    pool_id: str
    account: AccountId
    tick_lower: int
    tick_upper: int
    liquidity: int
    fixed_token_balance: int
    variable_token_balance: int
    accumulated_fees: int = 0
    
    @property
    def notional(self) -> int:
        """Absolute notional value (variable token balance)."""
        return abs(self.variable_token_balance)
    
    @property
    def is_fixed_taker(self) -> bool:
        """True if this position is paying fixed (receiving variable)."""
        return self.variable_token_balance > 0


@dataclass
class PoolInfo:
    """
    Information about an IRS pool.
    
    Attributes:
        pool_id: Unique pool identifier (hash of PoolKey).
        pool_key: The pool key parameters.
        sqrt_price_x96: Current price in Q64.96 format.
        tick: Current tick (determines fixed rate).
        liquidity: Total active liquidity.
        status: Pool status ("active", "settling", "expired").
    """
    
    pool_id: str
    pool_key: PoolKey
    sqrt_price_x96: int
    tick: int
    liquidity: int
    status: str = "active"
    
    @property
    def is_active(self) -> bool:
        """True if pool is still tradeable."""
        return self.status == "active"


@dataclass
class MarginBalance:
    """
    Margin balance for a specific token.
    
    Attributes:
        token: Token address.
        amount: Raw balance amount (in token decimals).
        value_usd: USD value of the balance.
        discount_factor: Discount factor applied (1.0 for isolated margin).
    """
    
    token: str
    amount: int
    value_usd: Decimal = Decimal(0)
    discount_factor: Decimal = Decimal(1)
    
    @property
    def effective_value_usd(self) -> Decimal:
        """USD value after discount factor is applied."""
        return self.value_usd * self.discount_factor


@dataclass
class HealthStatus:
    """
    Health status of an account.
    
    Attributes:
        margin_value_usd: Total margin value in USD (after discounts).
        obligations_usd: Total obligations in USD.
        health_factor: Ratio of margin to obligations. > 1.0 is healthy.
        is_liquidatable: True if account can be liquidated.
        margin_required: Additional margin needed to be healthy (0 if healthy).
    """
    
    margin_value_usd: Decimal
    obligations_usd: Decimal
    health_factor: Decimal
    is_liquidatable: bool
    margin_required: Decimal = Decimal(0)
    
    @classmethod
    def from_values(cls, margin_value: Decimal, obligations: Decimal) -> "HealthStatus":
        """
        Create HealthStatus from margin value and obligations.
        
        Args:
            margin_value: Total margin value in USD.
            obligations: Total obligations in USD.
            
        Returns:
            HealthStatus instance.
        """
        if obligations == 0:
            health = Decimal("inf")
            is_liquidatable = False
            margin_required = Decimal(0)
        else:
            health = margin_value / obligations
            is_liquidatable = health < 1
            margin_required = max(Decimal(0), obligations - margin_value)
        
        return cls(
            margin_value_usd=margin_value,
            obligations_usd=obligations,
            health_factor=health,
            is_liquidatable=is_liquidatable,
            margin_required=margin_required,
        )


@dataclass
class TradeEvent:
    """
    Live trade event from WebSocket subscription.
    
    Received when Swap, Mint, or Burn events occur on-chain.
    
    Attributes:
        event_type: Event type ("Swap", "Mint", "Burn").
        pool_id: Pool identifier (bytes32 hex).
        sender: Transaction sender address.
        block_number: Block number of the event.
        tx_hash: Transaction hash.
        log_index: Log index within the transaction.
        timestamp: Event timestamp (if available from block).
        
        # Swap-specific fields
        fixed_token_delta: Change in fixed token balance.
        variable_token_delta: Change in variable token balance.
        fee_incurred: Fee paid (for swaps).
        
        # Mint/Burn-specific fields
        amount: Liquidity amount (for mint/burn).
        tick_lower: Lower tick of position.
        tick_upper: Upper tick of position.
    """
    
    event_type: str
    pool_id: str
    sender: str
    block_number: int
    tx_hash: str
    log_index: int = 0
    timestamp: Optional[int] = None
    
    # Swap fields
    fixed_token_delta: int = 0
    variable_token_delta: int = 0
    fee_incurred: int = 0
    
    # Mint/Burn fields
    amount: int = 0
    tick_lower: int = 0
    tick_upper: int = 0
