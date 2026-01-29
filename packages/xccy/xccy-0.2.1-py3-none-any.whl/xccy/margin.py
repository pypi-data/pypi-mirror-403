"""
Margin management for XCCY Protocol.

Handles depositing, withdrawing, and querying margin balances.
All margin operations go through the CollateralEngine contract.
"""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from xccy.types import AccountId, MarginBalance
from xccy.math.fixed_point import wad_to_decimal
from xccy.tokens import PolygonTokens
from xccy.exceptions import InsufficientMarginError

if TYPE_CHECKING:
    from xccy.client import XccyClient


class MarginManager:
    """
    Manager for margin operations.
    
    Provides methods for depositing and withdrawing margin,
    querying balances, and approving token transfers.
    
    Access via `client.margin`.
    
    Example:
        >>> from xccy.tokens import PolygonTokens
        >>> 
        >>> # Approve token first (one-time)
        >>> client.margin.approve_token(PolygonTokens.USDC)
        >>> 
        >>> # Deposit 1000 USDC
        >>> tx = client.margin.deposit(account, PolygonTokens.USDC, 1000 * 10**6)
        >>> 
        >>> # Check balance
        >>> balance = client.margin.get_balance(account, PolygonTokens.USDC)
        >>> print(f"USDC margin: {balance / 10**6:.2f}")
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def approve_token(
        self,
        token: str,
        amount: Optional[int] = None,
    ):
        """
        Approve CollateralEngine to spend tokens.
        
        Must be called before depositing a token for the first time.
        
        Args:
            token: Token address to approve.
            amount: Amount to approve. Defaults to max uint256 (infinite).
            
        Returns:
            Transaction receipt.
            
        Example:
            >>> # Approve unlimited USDC spending
            >>> client.margin.approve_token(PolygonTokens.USDC)
            >>> 
            >>> # Approve specific amount
            >>> client.margin.approve_token(PolygonTokens.USDC, 10000 * 10**6)
        """
        if amount is None:
            amount = 2**256 - 1  # Max approval
        
        token_contract = self._client.get_erc20(token)
        spender = self._client.config.collateral_engine
        
        tx = token_contract.functions.approve(
            spender,
            amount,
        ).build_transaction({
            "from": self._client.signer_address,
        })
        
        return self._client.send_transaction(tx)
    
    def get_allowance(self, token: str) -> int:
        """
        Get current token allowance for CollateralEngine.
        
        Args:
            token: Token address.
            
        Returns:
            Approved amount.
        """
        token_contract = self._client.get_erc20(token)
        spender = self._client.config.collateral_engine
        
        return token_contract.functions.allowance(
            self._client.signer_address,
            spender,
        ).call()
    
    def deposit(
        self,
        account: AccountId,
        token: str,
        amount: int,
    ):
        """
        Deposit margin into an account.
        
        The token must be approved first via `approve_token()`.
        
        Args:
            account: The account to deposit into.
            token: Token address to deposit.
            amount: Amount to deposit (in token decimals).
            
        Returns:
            Transaction receipt.
            
        Example:
            >>> # Deposit 1000 USDC (6 decimals)
            >>> tx = client.margin.deposit(account, PolygonTokens.USDC, 1000 * 10**6)
            >>> print(f"Deposited in tx: {tx.transactionHash.hex()}")
        """
        contract = self._client.collateral_engine
        
        tx = contract.functions.updateAccountMargin(
            account.to_tuple(),
            token,
            amount,  # Positive = deposit
        ).build_transaction({
            "from": self._client.signer_address,
        })
        
        return self._client.send_transaction(tx)
    
    def withdraw(
        self,
        account: AccountId,
        token: str,
        amount: int,
    ):
        """
        Withdraw margin from an account.
        
        The withdrawal will fail if it would make the account
        undercollateralized (health factor < 1).
        
        Args:
            account: The account to withdraw from.
            token: Token address to withdraw.
            amount: Amount to withdraw (in token decimals).
            
        Returns:
            Transaction receipt.
            
        Raises:
            InsufficientMarginError: If withdrawal would undercollateralize.
            
        Example:
            >>> # Withdraw 500 USDC
            >>> tx = client.margin.withdraw(account, PolygonTokens.USDC, 500 * 10**6)
        """
        contract = self._client.collateral_engine
        
        tx = contract.functions.updateAccountMargin(
            account.to_tuple(),
            token,
            -amount,  # Negative = withdraw
        ).build_transaction({
            "from": self._client.signer_address,
        })
        
        return self._client.send_transaction(tx)
    
    def get_balance(self, account: AccountId, token: str) -> int:
        """
        Get margin balance for a specific token.
        
        Note: The CollateralEngine doesn't expose a direct balance getter.
        This method attempts to fetch balance from the backend API if available.
        For real-time margin health, use check_margin_requirement() instead.
        
        Args:
            account: The account to query.
            token: Token address.
            
        Returns:
            Balance in token decimals (0 if unknown/unavailable).
            
        Example:
            >>> balance = client.margin.get_balance(account, PolygonTokens.USDC)
            >>> print(f"USDC: {balance / 10**6:.2f}")
        """
        # Try backend API first
        if self._client.has_backend:
            try:
                metrics = self._client.backend.get_user_metrics(account.owner)
                # Backend might have balance info in sub-accounts
                for sub in metrics.sub_accounts:
                    if sub.account_id == account.account_id:
                        # Return total margin as approximation
                        return int(sub.total_margin * 10**6)  # Assume 6 decimals
            except Exception:
                pass
        
        # No reliable on-chain way to get balance without events
        return 0
    
    def get_all_balances(self, account: AccountId) -> dict[str, int]:
        """
        Get all margin balances for an account.
        
        Note: The CollateralEngine doesn't expose margin balances directly.
        This returns an empty dict. Use checkMarginRequirement() for health checks.
        
        Args:
            account: The account to query.
            
        Returns:
            Dictionary mapping token address to balance (currently empty).
            
        Example:
            >>> balances = client.margin.get_all_balances(account)
            >>> for token, amount in balances.items():
            ...     print(f"{token[:10]}...: {amount}")
        """
        # The contract stores margin in internal storage mappings.
        # No public getter for balance list. Use backend API for account summaries.
        return {}
    
    def get_total_value_usd(self, account: AccountId) -> Decimal:
        """
        Get total margin value in USD.
        
        Note: The contract doesn't expose a direct balance getter.
        This method uses the backend API for accurate values when available,
        or estimates from on-chain margin requirement checks.
        
        Args:
            account: The account to query.
            
        Returns:
            Total value in USD as Decimal (may be approximate).
            
        Example:
            >>> value = client.margin.get_total_value_usd(account)
            >>> print(f"Total margin: ${value:.2f}")
        """
        # Try backend API first for accurate value
        if self._client.has_backend:
            try:
                metrics = self._client.backend.get_user_metrics(account.owner)
                for sub in metrics.sub_accounts:
                    if sub.account_id == account.account_id:
                        return Decimal(str(sub.total_margin))
                # If sub-account not found, return total
                return Decimal(str(metrics.total_collateral))
            except Exception:
                pass
        
        # Fallback: estimate from on-chain data
        # checkMarginRequirement returns shortfall (obligations - margin) if undercollateralized
        # calculateAccountObligation returns total obligations
        obligations = self._client.position.get_obligations(account)
        shortfall = self._client.position.check_margin_requirement(account)
        
        # If shortfall > 0: margin_value = obligations - shortfall
        # If shortfall == 0: margin_value >= obligations (return obligations as lower bound)
        if shortfall > 0:
            return obligations - shortfall
        else:
            # This is a lower bound; actual margin could be higher
            # but we can't determine exact value without backend
            return obligations
    
    def get_margin_info(self, account: AccountId, token: str) -> MarginBalance:
        """
        Get detailed margin info for a token.
        
        Args:
            account: The account to query.
            token: Token address.
            
        Returns:
            MarginBalance with amount, USD value, and discount factor.
            
        Example:
            >>> info = client.margin.get_margin_info(account, PolygonTokens.USDC)
            >>> print(f"Amount: {info.amount / 10**6:.2f}")
            >>> print(f"Value: ${info.value_usd:.2f}")
        """
        amount = self.get_balance(account, token)
        
        if amount == 0:
            return MarginBalance(token=token, amount=0)
        
        price = self._client.oracle.get_price_usd(token)
        decimals = PolygonTokens.get_decimals(token)
        value = (Decimal(amount) / Decimal(10 ** decimals)) * price
        
        # Discount factors are stored in contract storage (marginTokenDiscountFactorWad).
        # Default to 1.0 for isolated margin or when not queryable.
        discount = Decimal(1)
        
        return MarginBalance(
            token=token,
            amount=amount,
            value_usd=value,
            discount_factor=discount,
        )
    
    def estimate_max_withdrawal(
        self,
        account: AccountId,
        token: str,
    ) -> int:
        """
        Estimate maximum amount that can be withdrawn.
        
        Calculates the maximum withdrawal that would leave
        the account at exactly 100% health factor.
        
        Args:
            account: The account.
            token: Token to withdraw.
            
        Returns:
            Maximum withdrawable amount in token decimals.
            
        Note:
            This is an estimate. The actual max may differ due to
            price movements between estimation and execution.
        """
        # Get current state
        balance = self.get_balance(account, token)
        obligations = self._client.position.get_obligations(account)
        total_value = self.get_total_value_usd(account)
        
        if obligations == 0:
            return balance  # Can withdraw everything
        
        # Calculate how much margin we need to keep
        price = self._client.oracle.get_price_usd(token)
        decimals = PolygonTokens.get_decimals(token)
        token_value = (Decimal(balance) / Decimal(10 ** decimals)) * price
        
        # Excess = total_value - obligations
        excess = total_value - obligations
        
        if excess <= 0:
            return 0  # Can't withdraw anything
        
        # Max withdrawal in USD
        max_withdraw_usd = min(excess, token_value)
        
        # Convert back to token units
        max_withdraw = int((max_withdraw_usd / price) * (10 ** decimals))
        
        return min(max_withdraw, balance)
