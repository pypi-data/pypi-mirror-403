"""
Main XCCY client entry point.

The XccyClient aggregates all SDK functionality into a single interface,
managing web3 connections, contract instances, and optional backend access.
"""

from typing import Optional, TYPE_CHECKING

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from xccy.constants import (
    NetworkConfig,
    get_network_config,
    load_abi,
    DEFAULT_BACKEND_URL,
)
from xccy.backend import BackendClient
from xccy.exceptions import NetworkError

if TYPE_CHECKING:
    from xccy.account import AccountManager
    from xccy.margin import MarginManager
    from xccy.oracle import OracleManager
    from xccy.position import PositionManager
    from xccy.pool import PoolManager
    from xccy.trading import TradingManager
    from xccy.trades import TradesManager
    from xccy.stream import TradeStream


class XccyClient:
    """
    Main client for interacting with the XCCY Protocol.
    
    Provides access to all SDK functionality through sub-managers:
    - account: Account creation and operator management
    - margin: Deposit, withdraw, and query margin balances
    - trading: Swap and LP operations (mint/burn)
    - position: Position queries and health monitoring
    - oracle: Price and rate oracle queries
    - pool: Pool information and state queries
    - trades: Historical trade queries
    - stream: Live trade event streaming (requires ws_rpc_url)
    
    Args:
        rpc_url: Web3 RPC endpoint URL.
        private_key: Optional private key for signing transactions.
            If not provided, only read operations are available.
        network: Network name or chain ID. Defaults to "polygon" (137).
        backend_url: Backend API URL for historical data.
            Set to None to disable backend access.
            Defaults to "https://api.xccy.finance".
        ws_rpc_url: Optional WebSocket RPC URL for live event streaming.
            Required for client.stream to work.
        
    Example:
        >>> from xccy import XccyClient
        >>> 
        >>> # Read-only client
        >>> client = XccyClient(rpc_url="https://polygon-rpc.com")
        >>> price = client.oracle.get_price_usd(token)
        >>> 
        >>> # Full client with signing and streaming
        >>> client = XccyClient(
        ...     rpc_url="https://polygon-rpc.com",
        ...     private_key="0x...",
        ...     ws_rpc_url="wss://polygon-mainnet.g.alchemy.com/v2/KEY",
        ... )
        >>> tx = client.margin.deposit(account, token, amount)
    """
    
    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
        network: str | int = "polygon",
        backend_url: Optional[str] = DEFAULT_BACKEND_URL,
        ws_rpc_url: Optional[str] = None,
    ):
        """Initialize the XCCY client."""
        # Setup Web3
        self._web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add PoA middleware for Polygon
        self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not self._web3.is_connected():
            raise NetworkError(f"Failed to connect to RPC: {rpc_url}")
        
        # Verify network
        self._config = get_network_config(network)
        chain_id = self._web3.eth.chain_id
        if chain_id != self._config.chain_id:
            raise NetworkError(
                f"Chain ID mismatch: expected {self._config.chain_id}, got {chain_id}",
                chain_id=chain_id,
            )
        
        # Setup account
        self._private_key = private_key
        self._account = None
        if private_key:
            self._account = self._web3.eth.account.from_key(private_key)
            self._web3.eth.default_account = self._account.address
        
        # Setup backend (optional)
        self._backend: Optional[BackendClient] = None
        if backend_url:
            self._backend = BackendClient(base_url=backend_url)
        
        # Store WebSocket URL for streaming
        self._ws_rpc_url = ws_rpc_url
        
        # Initialize contracts (lazy)
        self._contracts: dict = {}
        
        # Initialize managers (lazy)
        self._account_manager: Optional["AccountManager"] = None
        self._margin_manager: Optional["MarginManager"] = None
        self._oracle_manager: Optional["OracleManager"] = None
        self._position_manager: Optional["PositionManager"] = None
        self._pool_manager: Optional["PoolManager"] = None
        self._trading_manager: Optional["TradingManager"] = None
        self._trades_manager: Optional["TradesManager"] = None
        self._trade_stream: Optional["TradeStream"] = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Properties
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def web3(self) -> Web3:
        """Web3 instance for direct access."""
        return self._web3
    
    @property
    def config(self) -> NetworkConfig:
        """Network configuration."""
        return self._config
    
    @property
    def signer_address(self) -> Optional[str]:
        """Address of the signer (if private key provided)."""
        return self._account.address if self._account else None
    
    @property
    def has_signer(self) -> bool:
        """True if client can sign transactions."""
        return self._account is not None
    
    @property
    def has_backend(self) -> bool:
        """True if backend API is configured."""
        return self._backend is not None
    
    @property
    def backend(self) -> Optional[BackendClient]:
        """Backend client for historical data (may be None)."""
        return self._backend
    
    @property
    def has_stream(self) -> bool:
        """True if WebSocket streaming is configured."""
        return self._ws_rpc_url is not None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Contract Access
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _get_contract(self, name: str, address: str):
        """Get or create a contract instance."""
        if name not in self._contracts:
            abi = load_abi(name)
            self._contracts[name] = self._web3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=abi,
            )
        return self._contracts[name]
    
    @property
    def collateral_engine(self):
        """CollateralEngine contract instance."""
        return self._get_contract("CollateralEngine", self._config.collateral_engine)
    
    @property
    def vamm_manager(self):
        """VAMMManager contract instance."""
        return self._get_contract("VAMMManager", self._config.vamm_manager)
    
    @property
    def oracle_hub(self):
        """OracleHub contract instance."""
        return self._get_contract("OracleHub", self._config.oracle_hub)
    
    @property
    def apr_oracle(self):
        """AprOracle contract instance."""
        return self._get_contract("AprOracle", self._config.apr_oracle)
    
    def get_erc20(self, token_address: str):
        """
        Get ERC20 contract instance for a token.
        
        Args:
            token_address: Token contract address.
            
        Returns:
            ERC20 contract instance.
        """
        key = f"ERC20_{token_address}"
        if key not in self._contracts:
            abi = load_abi("ERC20")
            self._contracts[key] = self._web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=abi,
            )
        return self._contracts[key]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Managers
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def account(self) -> "AccountManager":
        """
        Account management: create accounts, manage operators.
        
        Example:
            >>> account = client.account.create_account_id(owner, 0)
            >>> client.account.set_operator(account, operator, True)
        """
        if self._account_manager is None:
            from xccy.account import AccountManager
            self._account_manager = AccountManager(self)
        return self._account_manager
    
    @property
    def margin(self) -> "MarginManager":
        """
        Margin operations: deposit, withdraw, query balances.
        
        Example:
            >>> client.margin.deposit(account, token, amount)
            >>> balance = client.margin.get_balance(account, token)
        """
        if self._margin_manager is None:
            from xccy.margin import MarginManager
            self._margin_manager = MarginManager(self)
        return self._margin_manager
    
    @property
    def oracle(self) -> "OracleManager":
        """
        Oracle data: prices, APRs, historical rates.
        
        Example:
            >>> price = client.oracle.get_price_usd(token)
            >>> apr = client.oracle.get_apr(aToken)
        """
        if self._oracle_manager is None:
            from xccy.oracle import OracleManager
            self._oracle_manager = OracleManager(self)
        return self._oracle_manager
    
    @property
    def position(self) -> "PositionManager":
        """
        Position queries: health factor, obligations, margin status.
        
        Example:
            >>> obligations = client.position.get_obligations(account)
            >>> is_safe = client.position.check_margin_requirement(account) == 0
        """
        if self._position_manager is None:
            from xccy.position import PositionManager
            self._position_manager = PositionManager(self)
        return self._position_manager
    
    @property
    def pool(self) -> "PoolManager":
        """
        Pool information: state, existence, pool keys.
        
        Example:
            >>> state = client.pool.get_vamm_state(pool_key)
            >>> exists = client.pool.pool_exists(pool_key)
        """
        if self._pool_manager is None:
            from xccy.pool import PoolManager
            self._pool_manager = PoolManager(self)
        return self._pool_manager
    
    @property
    def trading(self) -> "TradingManager":
        """
        Trading operations: swap, mint (add LP), burn (remove LP).
        
        Example:
            >>> result = client.trading.swap(pool, account, notional, True)
            >>> client.trading.mint(pool, account, tick_lower, tick_upper, liquidity)
        """
        if self._trading_manager is None:
            from xccy.trading import TradingManager
            self._trading_manager = TradingManager(self)
        return self._trading_manager
    
    @property
    def trades(self) -> "TradesManager":
        """
        Historical trade queries: pool trades, user trades.
        
        Requires backend to be configured.
        
        Example:
            >>> trades, cursor = client.trades.get_pool_trades(pool_id)
            >>> my_trades = client.trades.get_user_trades(pool_id, my_address)
        """
        if self._trades_manager is None:
            from xccy.trades import TradesManager
            self._trades_manager = TradesManager(self)
        return self._trades_manager
    
    @property
    def stream(self) -> "TradeStream":
        """
        Live trade event streaming via WebSocket.
        
        Requires ws_rpc_url to be set in client constructor.
        
        Example:
            >>> def on_trade(event):
            ...     print(f"New {event.event_type}: {event.tx_hash}")
            >>> 
            >>> client.stream.subscribe(on_trade, event_types=["Swap"])
            >>> client.stream.start()  # Blocking
        """
        if self._trade_stream is None:
            if not self._ws_rpc_url:
                raise ValueError(
                    "WebSocket RPC URL not configured. "
                    "Pass ws_rpc_url to XccyClient constructor."
                )
            from xccy.stream import TradeStream
            self._trade_stream = TradeStream(
                ws_rpc_url=self._ws_rpc_url,
                vamm_address=self._config.vamm_manager,
            )
        return self._trade_stream
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Transaction Helpers
    # ═══════════════════════════════════════════════════════════════════════════
    
    def send_transaction(
        self,
        tx: dict,
        gas_limit: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        gas_price_multiplier: float = 1.5,
    ):
        """
        Sign and send a transaction.
        
        Args:
            tx: Transaction dictionary (to, data, value, etc.).
                May already contain 'gas' and gas pricing from build_transaction.
            gas_limit: Optional gas limit override.
            max_fee_per_gas: Optional max fee per gas (EIP-1559).
            max_priority_fee_per_gas: Optional priority fee (EIP-1559).
            gas_price_multiplier: Multiplier for gas price (default 1.5 for faster confirms).
            
        Returns:
            Transaction receipt.
            
        Raises:
            ValueError: If no signer is configured.
        """
        if not self._account:
            raise ValueError("No private key configured for signing")
        
        # Build transaction
        tx["from"] = self._account.address
        tx["nonce"] = self._web3.eth.get_transaction_count(self._account.address)
        tx["chainId"] = self._config.chain_id
        
        # Gas limit: use explicit override > existing in tx > estimate
        if gas_limit:
            tx["gas"] = gas_limit
        elif "gas" not in tx:
            tx["gas"] = self._web3.eth.estimate_gas(tx)
        
        # Gas pricing:
        # 1. If explicit max_fee_per_gas provided, use those
        # 2. Else if tx already has EIP-1559 fields, adjust them with multiplier
        # 3. Else use legacy gasPrice
        has_eip1559 = "maxFeePerGas" in tx or "maxPriorityFeePerGas" in tx
        
        if max_fee_per_gas:
            # Clean up any existing pricing
            tx.pop("gasPrice", None)
            tx["maxFeePerGas"] = max_fee_per_gas
            tx["maxPriorityFeePerGas"] = max_priority_fee_per_gas or 1_000_000_000
        elif has_eip1559:
            # Transaction already has EIP-1559 pricing from build_transaction
            # Apply multiplier to ensure faster confirmation
            if "maxFeePerGas" in tx:
                tx["maxFeePerGas"] = int(tx["maxFeePerGas"] * gas_price_multiplier)
            if "maxPriorityFeePerGas" in tx:
                tx["maxPriorityFeePerGas"] = int(tx["maxPriorityFeePerGas"] * gas_price_multiplier)
        else:
            # Use legacy gas price with multiplier
            base_price = self._web3.eth.gas_price
            tx["gasPrice"] = int(base_price * gas_price_multiplier)
        
        # Sign and send
        signed = self._account.sign_transaction(tx)
        tx_hash = self._web3.eth.send_raw_transaction(signed.raw_transaction)
        
        # Wait for receipt
        return self._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Cleanup
    # ═══════════════════════════════════════════════════════════════════════════
    
    def close(self) -> None:
        """Close all connections."""
        if self._backend:
            self._backend.close()
        if self._trade_stream:
            self._trade_stream.stop()
    
    def __enter__(self) -> "XccyClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
