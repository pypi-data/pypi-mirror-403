"""
XCCY Python SDK - Interest Rate Swap AMM on Polygon.

This SDK provides a user-friendly interface to interact with the XCCY Protocol,
enabling margin management, trading (swaps and LP), position monitoring, and oracle queries.

Example:
    >>> from xccy import XccyClient, parse_amount, format_amount
    >>> from xccy.tokens import PolygonTokens
    >>> 
    >>> client = XccyClient(rpc_url="https://polygon-rpc.com")
    >>> account = client.account.create_account_id(account_id=0, isolated_margin_token=PolygonTokens.USDC)
    >>> 
    >>> # Deposit 100 USDC
    >>> client.margin.deposit(account, PolygonTokens.USDC, parse_amount(100, "USDC"))
    >>> 
    >>> # Swap 50 USDC
    >>> result = client.trading.swap(pool, account, parse_amount(50, "USDC"), is_fixed_taker=True)
    >>> print(f"Received: {format_amount(result.fixed_token_delta, 'USDC')} fixed")
"""

from xccy.client import XccyClient
from xccy.types import AccountId, PoolKey, SwapParams, SwapResult, PositionInfo, TradeEvent
from xccy.trading import MintResult, BurnResult
from xccy.backend import UserPosition, UserMetrics, SubAccount, SettlementRecord, PoolSummary, TradeRecord
from xccy.tokens import parse_amount, format_amount, get_decimals, PolygonTokens, Tokens, TokenInfo
from xccy.exceptions import (
    XccyError,
    InsufficientMarginError,
    PoolNotFoundError,
    TransactionFailedError,
)

__version__ = "0.1.5"
__all__ = [
    # Client
    "XccyClient",
    # Types
    "AccountId",
    "PoolKey",
    "SwapParams",
    "SwapResult",
    "MintResult",
    "BurnResult",
    "PositionInfo",
    "TradeEvent",
    "TradeRecord",
    # Backend types
    "UserPosition",
    "UserMetrics",
    "SubAccount",
    "SettlementRecord",
    "PoolSummary",
    # Token utilities
    "parse_amount",
    "format_amount",
    "get_decimals",
    "PolygonTokens",
    "Tokens",
    "TokenInfo",
    # Exceptions
    "XccyError",
    "InsufficientMarginError",
    "PoolNotFoundError",
    "TransactionFailedError",
]
