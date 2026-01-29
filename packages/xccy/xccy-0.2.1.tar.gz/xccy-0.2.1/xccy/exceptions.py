"""
Custom exceptions for XCCY SDK.

All SDK-specific exceptions inherit from XccyError.
"""


class XccyError(Exception):
    """Base exception for all XCCY SDK errors."""
    
    pass


class ContractError(XccyError):
    """Error from smart contract interaction."""
    
    def __init__(self, message: str, tx_hash: str | None = None):
        super().__init__(message)
        self.tx_hash = tx_hash


class InsufficientMarginError(XccyError):
    """Account has insufficient margin for the operation."""
    
    def __init__(
        self,
        message: str = "Insufficient margin",
        required: int = 0,
        available: int = 0,
    ):
        super().__init__(message)
        self.required = required
        self.available = available
        self.shortfall = required - available


class PoolNotFoundError(XccyError):
    """Requested pool does not exist."""
    
    def __init__(self, pool_id: str | None = None, pool_key: object | None = None):
        if pool_id:
            message = f"Pool not found: {pool_id}"
        elif pool_key:
            message = f"Pool not found for key: {pool_key}"
        else:
            message = "Pool not found"
        super().__init__(message)
        self.pool_id = pool_id


class TransactionFailedError(XccyError):
    """Transaction execution failed."""
    
    def __init__(
        self,
        message: str = "Transaction failed",
        tx_hash: str | None = None,
        revert_reason: str | None = None,
    ):
        super().__init__(message)
        self.tx_hash = tx_hash
        self.revert_reason = revert_reason


class SlippageExceededError(XccyError):
    """Price moved beyond slippage tolerance."""
    
    def __init__(
        self,
        message: str = "Slippage exceeded",
        expected_price: int = 0,
        actual_price: int = 0,
    ):
        super().__init__(message)
        self.expected_price = expected_price
        self.actual_price = actual_price


class AccountNotFoundError(XccyError):
    """Account does not exist (no margin or positions)."""
    
    def __init__(self, account_id: object | None = None):
        message = f"Account not found: {account_id}" if account_id else "Account not found"
        super().__init__(message)
        self.account_id = account_id


class OracleError(XccyError):
    """Error querying oracle data."""
    
    def __init__(self, message: str = "Oracle error", asset: str | None = None):
        super().__init__(message)
        self.asset = asset


class BackendError(XccyError):
    """Error from backend API."""
    
    def __init__(
        self,
        message: str = "Backend error",
        status_code: int | None = None,
        endpoint: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


class NetworkError(XccyError):
    """Network configuration or RPC error."""
    
    def __init__(self, message: str = "Network error", chain_id: int | None = None):
        super().__init__(message)
        self.chain_id = chain_id


class InvalidParameterError(XccyError):
    """Invalid parameter provided to SDK method."""
    
    def __init__(self, param_name: str, message: str = "Invalid parameter"):
        super().__init__(f"{param_name}: {message}")
        self.param_name = param_name
