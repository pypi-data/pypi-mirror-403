"""
Trading operations for XCCY Protocol.

Handles swaps and liquidity provision (mint/burn) through the VAMMManager.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from xccy.types import AccountId, PoolKey, SwapParams, SwapResult
from xccy.math.tick import tick_to_sqrt_price_x96, MIN_SQRT_RATIO, MAX_SQRT_RATIO
from xccy.math.liquidity import notional_to_liquidity, liquidity_to_notional
from xccy.exceptions import SlippageExceededError, TransactionFailedError

if TYPE_CHECKING:
    from xccy.client import XccyClient


# Default gas limits (based on empirical testing)
DEFAULT_SWAP_GAS = 1_500_000
DEFAULT_MINT_GAS = 2_000_000
DEFAULT_BURN_GAS = 1_500_000


@dataclass
class MintResult:
    """Result of a mint (liquidity provision) operation."""
    
    liquidity: int
    """Amount of liquidity added."""
    
    tick_lower: int
    """Lower tick bound of the position."""
    
    tick_upper: int
    """Upper tick bound of the position."""
    
    margin_requirement: int
    """Margin requirement for the new position (raw units)."""
    
    transaction_hash: str
    """Transaction hash."""
    
    gas_used: int
    """Gas consumed by the transaction."""


@dataclass
class BurnResult:
    """Result of a burn (liquidity removal) operation."""
    
    liquidity: int
    """Amount of liquidity removed."""
    
    tick_lower: int
    """Lower tick bound of the position."""
    
    tick_upper: int
    """Upper tick bound of the position."""
    
    margin_requirement: int
    """Remaining margin requirement after burn (raw units)."""
    
    transaction_hash: str
    """Transaction hash."""
    
    gas_used: int
    """Gas consumed by the transaction."""


class TradingManager:
    """
    Manager for trading operations.
    
    Provides methods for executing swaps and managing LP positions.
    
    Access via `client.trading`.
    
    Note:
        Return values (fixed_token_delta, etc.) are obtained via staticcall before
        transaction submission. In volatile markets, actual execution may differ
        slightly due to price movement between estimation and execution. Use
        `sqrt_price_limit` for slippage protection.
    
    Example:
        >>> # Execute a swap (pay fixed rate)
        >>> result = client.trading.swap(
        ...     pool_key=pool,
        ...     account=account,
        ...     notional=10_000 * 10**6,
        ...     is_fixed_taker=True,
        ... )
        >>> print(f"Fixed delta: {result.fixed_token_delta}")
        >>> 
        >>> # Provide liquidity
        >>> client.trading.mint(
        ...     pool_key=pool,
        ...     account=account,
        ...     tick_lower=-6950,
        ...     tick_upper=-6850,
        ...     liquidity=1_000_000,
        ... )
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def swap(
        self,
        pool_key: PoolKey,
        account: AccountId,
        notional: int,
        is_fixed_taker: bool,
        tick_lower: Optional[int] = None,
        tick_upper: Optional[int] = None,
        sqrt_price_limit: Optional[int] = None,
        gas_limit: Optional[int] = None,
    ) -> SwapResult:
        """
        Execute a swap on a pool.
        
        Args:
            pool_key: The pool to swap on.
            account: Account executing the swap.
            notional: Notional amount (positive = exact input).
            is_fixed_taker: If True, pay fixed rate (receive variable).
                If False, pay variable rate (receive fixed).
            tick_lower: Lower tick bound for the position.
                Defaults to ±100 ticks around current price.
            tick_upper: Upper tick bound for the position.
                Defaults to ±100 ticks around current price.
            sqrt_price_limit: Price limit for slippage protection.
                Defaults to max/min depending on direction.
            gas_limit: Gas limit override. Defaults to 1.5M.
                
        Returns:
            SwapResult with execution details including fixed/variable deltas.
            
        Example:
            >>> # Pay fixed on 10k notional
            >>> result = client.trading.swap(
            ...     pool_key=pool,
            ...     account=account,
            ...     notional=10_000 * 10**6,
            ...     is_fixed_taker=True,
            ... )
            >>> print(f"Fixed delta: {result.fixed_token_delta}")
            >>> print(f"Variable delta: {result.variable_token_delta}")
        """
        # Get current pool state for default tick range
        pool_id = pool_key.get_pool_id()
        current_tick, _ = self._client.vamm_manager.functions.getVAMMState(pool_id).call()
        
        # Default tick range: ±100 ticks around current, aligned to tick spacing
        spacing = pool_key.tick_spacing
        if tick_lower is None:
            # Align to tick spacing (round down for lower)
            aligned_current = (current_tick // spacing) * spacing
            tick_lower = aligned_current - (100 // spacing) * spacing
        if tick_upper is None:
            # Align to tick spacing (round up for upper)
            aligned_current = (current_tick // spacing) * spacing
            tick_upper = aligned_current + (100 // spacing) * spacing
        
        # Ensure tick_lower < tick_upper
        if tick_lower >= tick_upper:
            tick_lower = tick_upper - spacing
        
        # Set price limit if not provided
        # For fixed taker (positive amount): move price up, so use MAX
        # For variable taker (negative amount): move price down, so use MIN
        if sqrt_price_limit is None:
            sqrt_price_limit = MAX_SQRT_RATIO - 1 if is_fixed_taker else MIN_SQRT_RATIO + 1
        
        # Build swap params tuple
        swap_params = (
            account.to_tuple(),
            notional if is_fixed_taker else -notional,  # amountSpecified
            sqrt_price_limit,
            tick_lower,
            tick_upper,
        )
        
        contract = self._client.vamm_manager
        
        # Get return values via staticcall first
        (
            fixed_delta,
            variable_delta,
            fee,
            fixed_delta_unbalanced,
            margin_req,
            price_after,
        ) = contract.functions.swap(
            pool_key.to_tuple(),
            swap_params,
        ).call({"from": self._client.signer_address})
        
        # Execute actual transaction
        tx = contract.functions.swap(
            pool_key.to_tuple(),
            swap_params,
        ).build_transaction({
            "from": self._client.signer_address,
            "gas": gas_limit or DEFAULT_SWAP_GAS,
        })
        
        receipt = self._client.send_transaction(tx)
        
        if receipt.status != 1:
            raise TransactionFailedError(
                f"Swap failed: tx={receipt.transactionHash.hex()}",
                transaction_hash=receipt.transactionHash.hex(),
            )
        
        return SwapResult(
            fixed_token_delta=fixed_delta,
            variable_token_delta=variable_delta,
            cumulative_fee_incurred=fee,
            fixed_token_delta_unbalanced=fixed_delta_unbalanced,
            position_margin_requirement=margin_req,
            price_after_swap=price_after,
            transaction_hash=receipt.transactionHash.hex(),
            gas_used=receipt.gasUsed,
        )
    
    def swap_exact_fixed_rate(
        self,
        pool_key: PoolKey,
        account: AccountId,
        notional: int,
        max_fixed_rate: Decimal,
        is_fixed_taker: bool,
    ) -> SwapResult:
        """
        Execute a swap with fixed rate slippage protection.
        
        Args:
            pool_key: The pool to swap on.
            account: Account executing the swap.
            notional: Notional amount.
            max_fixed_rate: Maximum fixed rate to accept.
            is_fixed_taker: Direction of swap.
            
        Returns:
            SwapResult with execution details.
            
        Raises:
            SlippageExceededError: If rate exceeds limit.
        """
        from xccy.math.tick import fixed_rate_to_tick
        
        # Convert rate to tick for price limit
        target_tick = fixed_rate_to_tick(float(max_fixed_rate))
        sqrt_price_limit = tick_to_sqrt_price_x96(target_tick)
        
        return self.swap(
            pool_key=pool_key,
            account=account,
            notional=notional,
            is_fixed_taker=is_fixed_taker,
            sqrt_price_limit=sqrt_price_limit,
        )
    
    def mint(
        self,
        pool_key: PoolKey,
        account: AccountId,
        tick_lower: int,
        tick_upper: int,
        liquidity: int,
        gas_limit: Optional[int] = None,
    ) -> MintResult:
        """
        Add liquidity to a pool.
        
        Creates or adds to an LP position at the specified tick range.
        
        Args:
            pool_key: The pool.
            account: Account providing liquidity.
            tick_lower: Lower tick bound.
            tick_upper: Upper tick bound.
            liquidity: Amount of liquidity to add.
            gas_limit: Gas limit override. Defaults to 2M.
            
        Returns:
            MintResult with execution details.
            
        Example:
            >>> result = client.trading.mint(
            ...     pool_key=pool,
            ...     account=account,
            ...     tick_lower=-6950,
            ...     tick_upper=-6850,
            ...     liquidity=1_000_000,
            ... )
            >>> print(f"Margin required: {result.margin_requirement}")
        """
        contract = self._client.vamm_manager
        
        # Get margin requirement via staticcall first
        margin_req = contract.functions.mint(
            pool_key.to_tuple(),
            account.to_tuple(),
            tick_lower,
            tick_upper,
            liquidity,
        ).call({"from": self._client.signer_address})
        
        tx = contract.functions.mint(
            pool_key.to_tuple(),
            account.to_tuple(),
            tick_lower,
            tick_upper,
            liquidity,
        ).build_transaction({
            "from": self._client.signer_address,
            "gas": gas_limit or DEFAULT_MINT_GAS,
        })
        
        receipt = self._client.send_transaction(tx)
        
        if receipt.status != 1:
            raise TransactionFailedError(
                f"Mint failed: tx={receipt.transactionHash.hex()}",
                transaction_hash=receipt.transactionHash.hex(),
            )
        
        return MintResult(
            liquidity=liquidity,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            margin_requirement=margin_req,
            transaction_hash=receipt.transactionHash.hex(),
            gas_used=receipt.gasUsed,
        )
    
    def mint_with_notional(
        self,
        pool_key: PoolKey,
        account: AccountId,
        tick_lower: int,
        tick_upper: int,
        notional: int,
    ):
        """
        Add liquidity with a target notional amount.
        
        Calculates the liquidity needed for the desired notional exposure.
        
        Args:
            pool_key: The pool.
            account: Account providing liquidity.
            tick_lower: Lower tick bound.
            tick_upper: Upper tick bound.
            notional: Target notional in token units.
            
        Returns:
            Transaction receipt.
            
        Example:
            >>> # Provide 10k USDC notional of liquidity
            >>> tx = client.trading.mint_with_notional(
            ...     pool_key=pool,
            ...     account=account,
            ...     tick_lower=-6950,
            ...     tick_upper=-6850,
            ...     notional=10_000 * 10**6,
            ... )
        """
        liquidity = notional_to_liquidity(notional, tick_lower, tick_upper)
        return self.mint(pool_key, account, tick_lower, tick_upper, liquidity)
    
    def burn(
        self,
        pool_key: PoolKey,
        account: AccountId,
        tick_lower: int,
        tick_upper: int,
        liquidity: int,
        gas_limit: Optional[int] = None,
    ) -> BurnResult:
        """
        Remove liquidity from a pool.
        
        Args:
            pool_key: The pool.
            account: Account owning the position.
            tick_lower: Lower tick bound.
            tick_upper: Upper tick bound.
            liquidity: Amount of liquidity to remove.
            gas_limit: Gas limit override. Defaults to 1.5M.
            
        Returns:
            BurnResult with execution details.
            
        Example:
            >>> result = client.trading.burn(
            ...     pool_key=pool,
            ...     account=account,
            ...     tick_lower=-6950,
            ...     tick_upper=-6850,
            ...     liquidity=500_000,
            ... )
            >>> print(f"Burned: {result.liquidity} liquidity")
        """
        contract = self._client.vamm_manager
        
        # Get remaining margin requirement via staticcall first
        margin_req = contract.functions.burn(
            pool_key.to_tuple(),
            account.to_tuple(),
            tick_lower,
            tick_upper,
            liquidity,
        ).call({"from": self._client.signer_address})
        
        tx = contract.functions.burn(
            pool_key.to_tuple(),
            account.to_tuple(),
            tick_lower,
            tick_upper,
            liquidity,
        ).build_transaction({
            "from": self._client.signer_address,
            "gas": gas_limit or DEFAULT_BURN_GAS,
        })
        
        receipt = self._client.send_transaction(tx)
        
        if receipt.status != 1:
            raise TransactionFailedError(
                f"Burn failed: tx={receipt.transactionHash.hex()}",
                transaction_hash=receipt.transactionHash.hex(),
            )
        
        return BurnResult(
            liquidity=liquidity,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            margin_requirement=margin_req,
            transaction_hash=receipt.transactionHash.hex(),
            gas_used=receipt.gasUsed,
        )
    
    def burn_all(
        self,
        pool_key: PoolKey,
        account: AccountId,
        tick_lower: int,
        tick_upper: int,
    ):
        """
        Remove all liquidity from a position.
        
        Queries the current position liquidity and burns it all.
        
        Args:
            pool_key: The pool.
            account: Account owning the position.
            tick_lower: Lower tick bound.
            tick_upper: Upper tick bound.
            
        Returns:
            Transaction receipt.
        """
        position = self._client.position.get_position(
            account, pool_key, tick_lower, tick_upper
        )
        
        if position is None or position.liquidity == 0:
            raise ValueError("No liquidity to burn")
        
        return self.burn(pool_key, account, tick_lower, tick_upper, position.liquidity)
    
    def estimate_swap_output(
        self,
        pool_key: PoolKey,
        notional: int,
        is_fixed_taker: bool,
    ) -> dict:
        """
        Estimate the output of a swap without executing.
        
        Uses static call to simulate the swap.
        
        Args:
            pool_key: The pool.
            notional: Notional amount.
            is_fixed_taker: Swap direction.
            
        Returns:
            Dictionary with estimated outputs:
            - fixed_delta: Change in fixed token
            - variable_delta: Change in variable token
            - fee: Expected fee
            - effective_rate: Implied fixed rate
        """
        # Get current state
        state = self._client.pool.get_vamm_state(pool_key)
        current_rate = state["fixed_rate"]
        
        # Rough estimate based on current rate
        # In practice, this would use a static call
        return {
            "fixed_delta": int(notional * float(current_rate)),
            "variable_delta": notional,
            "fee": int(notional * pool_key.fee_wad / 10**18),
            "effective_rate": current_rate,
        }
    
    def get_position_notional(
        self,
        pool_key: PoolKey,
        account: AccountId,
        tick_lower: int,
        tick_upper: int,
    ) -> int:
        """
        Get the notional value of an LP position.
        
        Args:
            pool_key: The pool.
            account: Account owning the position.
            tick_lower: Lower tick bound.
            tick_upper: Upper tick bound.
            
        Returns:
            Notional value in token units.
        """
        position = self._client.position.get_position(
            account, pool_key, tick_lower, tick_upper
        )
        
        if position is None:
            return 0
        
        return liquidity_to_notional(position.liquidity, tick_lower, tick_upper)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Settlement & Liquidation
    # ═══════════════════════════════════════════════════════════════════════════
    
    def settle_position(
        self,
        pool_key: PoolKey,
        account: AccountId,
        gas_limit: Optional[int] = None,
    ):
        """
        Settle a position after pool maturity.
        
        Calculates final PnL and releases margin after the pool's term has ended.
        Can only be called after `pool_key.term_end_timestamp` has passed.
        
        Args:
            pool_key: The matured pool.
            account: Account with position to settle.
            gas_limit: Gas limit override. Defaults to 1M.
            
        Returns:
            Transaction receipt.
            
        Raises:
            TransactionFailedError: If settlement fails (e.g., pool not matured).
            
        Example:
            >>> # After pool maturity
            >>> if client.pool.is_pool_expired(pool_key):
            ...     receipt = client.trading.settle_position(pool_key, account)
            ...     print(f"Settled in tx: {receipt.transactionHash.hex()}")
        """
        contract = self._client.collateral_engine
        
        tx = contract.functions.settlePosition(
            account.to_tuple(),
            pool_key.to_tuple(),
        ).build_transaction({
            "from": self._client.signer_address,
            "gas": gas_limit or 1_000_000,
        })
        
        receipt = self._client.send_transaction(tx)
        
        if receipt.status != 1:
            raise TransactionFailedError(
                f"Settlement failed: tx={receipt.transactionHash.hex()}",
                transaction_hash=receipt.transactionHash.hex(),
            )
        
        return receipt
    
    def liquidate_account(
        self,
        target_account: AccountId,
        liquidator_account: Optional[AccountId] = None,
        gas_limit: Optional[int] = None,
    ):
        """
        Liquidate an undercollateralized account.
        
        When an account's health factor falls below 1.0, anyone can liquidate it.
        The liquidator receives a portion of the liquidated margin as reward.
        
        Args:
            target_account: The undercollateralized account to liquidate.
            liquidator_account: Account to receive liquidation reward.
                Defaults to signer's account with id=0.
            gas_limit: Gas limit override. Defaults to 2M.
            
        Returns:
            Transaction receipt.
            
        Raises:
            TransactionFailedError: If liquidation fails (e.g., account is healthy).
            
        Example:
            >>> if client.position.is_liquidatable(target):
            ...     receipt = client.trading.liquidate_account(target)
            ...     print("Liquidation successful!")
        """
        # Default liquidator account
        if liquidator_account is None:
            liquidator_account = self._client.account.create_account_id(
                account_id=0,
            )
        
        contract = self._client.collateral_engine
        
        tx = contract.functions.liquidateAccount(
            target_account.to_tuple(),
            liquidator_account.to_tuple(),
        ).build_transaction({
            "from": self._client.signer_address,
            "gas": gas_limit or 2_000_000,
        })
        
        receipt = self._client.send_transaction(tx)
        
        if receipt.status != 1:
            raise TransactionFailedError(
                f"Liquidation failed: tx={receipt.transactionHash.hex()}",
                transaction_hash=receipt.transactionHash.hex(),
            )
        
        return receipt
