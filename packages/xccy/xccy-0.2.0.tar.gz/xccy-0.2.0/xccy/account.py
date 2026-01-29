"""
Account management for XCCY Protocol.

Handles account creation, operator approvals, and account discovery.

Key concepts:
- One wallet can own multiple sub-accounts (identified by account_id)
- Each sub-account has independent margin, positions, and health
- Accounts can operate in cross-margin or isolated margin mode
- Operators can be approved to act on behalf of an account
"""

from typing import Optional, TYPE_CHECKING

from xccy.types import AccountId
from xccy.constants import ZERO_ADDRESS

if TYPE_CHECKING:
    from xccy.client import XccyClient


class AccountManager:
    """
    Manager for account-related operations.
    
    Provides methods for creating account identifiers, managing operator
    approvals, and discovering existing accounts.
    
    Access via `client.account`.
    
    Example:
        >>> # Create account ID for sub-account 0 (cross-margin)
        >>> account = client.account.create_account_id(
        ...     owner="0xYourWallet...",
        ...     account_id=0,
        ... )
        >>> 
        >>> # Approve an operator (e.g., Operator.sol router)
        >>> tx = client.account.set_operator(account, operator_address, True)
        >>> 
        >>> # Check if operator is approved
        >>> is_approved = client.account.is_operator(account, operator_address)
    """
    
    def __init__(self, client: "XccyClient"):
        """Initialize with parent client."""
        self._client = client
    
    def create_account_id(
        self,
        owner: Optional[str] = None,
        account_id: int = 0,
        isolated_margin_token: Optional[str] = None,
    ) -> AccountId:
        """
        Create an AccountId for interacting with the protocol.
        
        AccountId is a pure data structure that identifies a sub-account.
        It does not create anything on-chain — accounts are implicitly
        created when you first deposit margin or open a position.
        
        Args:
            owner: Wallet address that owns the account.
                Defaults to the signer address if available.
            account_id: Sub-account index (0, 1, 2, ...).
                Use different IDs to separate positions/strategies.
            isolated_margin_token: Token address for isolated margin mode.
                If None, account operates in cross-margin mode.
                
        Returns:
            AccountId instance.
            
        Raises:
            ValueError: If owner is not provided and no signer is configured.
            
        Example:
            >>> # Default account (ID 0, cross-margin)
            >>> main = client.account.create_account_id()
            >>> 
            >>> # Separate trading account
            >>> trading = client.account.create_account_id(account_id=1)
            >>> 
            >>> # Isolated USDC margin
            >>> isolated = client.account.create_account_id(
            ...     account_id=2,
            ...     isolated_margin_token=PolygonTokens.USDC,
            ... )
        """
        if owner is None:
            if not self._client.has_signer:
                raise ValueError("owner required when no private key configured")
            owner = self._client.signer_address
        
        return AccountId(
            owner=owner,
            account_id=account_id,
            isolated_margin_token=isolated_margin_token,
        )
    
    def set_operator(
        self,
        account: AccountId,
        operator: str,
        approved: bool,
    ):
        """
        Approve or revoke an operator for an account.
        
        Operators can perform actions on behalf of the account,
        such as batched margin updates with swaps (via Operator.sol).
        
        Args:
            account: The account to modify.
            operator: Address to approve/revoke.
            approved: True to approve, False to revoke.
            
        Returns:
            Transaction receipt.
            
        Example:
            >>> # Approve Operator router for batched transactions
            >>> tx = client.account.set_operator(account, operator_address, True)
            >>> print(f"Approved in tx: {tx.transactionHash.hex()}")
        """
        contract = self._client.collateral_engine
        tx = contract.functions.setAccountOperator(
            account.to_tuple(),
            operator,
            approved,
        ).build_transaction({
            "from": self._client.signer_address,
        })
        
        return self._client.send_transaction(tx)
    
    def is_operator(self, account: AccountId, operator: str) -> bool:
        """
        Check if an address is an approved operator for an account.
        
        Args:
            account: The account to check.
            operator: Address to check.
            
        Returns:
            True if the operator is approved, False otherwise.
            
        Example:
            >>> if client.account.is_operator(account, router):
            ...     print("Router can act on behalf of account")
        """
        contract = self._client.collateral_engine
        return contract.functions.isAccountOperator(
            account.to_tuple(),
            operator,
        ).call()
    
    def get_account_hash(self, account: AccountId) -> bytes:
        """
        Compute the storage hash for an account.
        
        This hash is used internally by the protocol to key account data.
        Useful for debugging or direct storage queries.
        
        Args:
            account: The account.
            
        Returns:
            32-byte hash.
        """
        return account.get_hash()
    
    def is_cross_margin(self, account: AccountId) -> bool:
        """
        Check if account operates in cross-margin mode.
        
        Args:
            account: The account to check.
            
        Returns:
            True if cross-margin (no isolated token), False if isolated.
        """
        return account.isolated_margin_token is None
    
    def is_isolated_margin(self, account: AccountId) -> bool:
        """
        Check if account operates in isolated margin mode.
        
        Args:
            account: The account to check.
            
        Returns:
            True if isolated margin, False if cross-margin.
        """
        return account.isolated_margin_token is not None
    
    def get_margin_mode_description(self, account: AccountId) -> str:
        """
        Get human-readable description of account's margin mode.
        
        Args:
            account: The account.
            
        Returns:
            Description string.
        """
        if self.is_cross_margin(account):
            return "Cross-margin (multi-collateral)"
        else:
            return f"Isolated margin ({account.isolated_margin_token[:10]}...)"
    
    def derive_account(
        self,
        base_account: AccountId,
        new_id: int,
    ) -> AccountId:
        """
        Derive a new account with same owner but different ID.
        
        Useful for creating multiple sub-accounts for the same wallet.
        
        Args:
            base_account: Account to derive from.
            new_id: New sub-account ID.
            
        Returns:
            New AccountId with same owner and margin mode.
            
        Example:
            >>> main = client.account.create_account_id()
            >>> alt = client.account.derive_account(main, 1)
        """
        return AccountId(
            owner=base_account.owner,
            account_id=new_id,
            isolated_margin_token=base_account.isolated_margin_token,
        )
    
    def switch_margin_mode(
        self,
        account: AccountId,
        isolated_token: Optional[str] = None,
    ) -> AccountId:
        """
        Create new account ID with different margin mode.
        
        Note: This creates a NEW account ID. You cannot change the margin
        mode of an existing account — you must create a new one.
        
        Args:
            account: Base account.
            isolated_token: Token for isolated mode, or None for cross-margin.
            
        Returns:
            New AccountId with different margin mode.
            
        Example:
            >>> # Switch from cross to isolated USDC
            >>> isolated = client.account.switch_margin_mode(
            ...     account,
            ...     isolated_token=PolygonTokens.USDC,
            ... )
        """
        # Use a new account ID for the different margin mode
        return AccountId(
            owner=account.owner,
            account_id=account.account_id + 100 if isolated_token else account.account_id,
            isolated_margin_token=isolated_token,
        )
