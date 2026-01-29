# Quick Start

Get started with the XCCY Python SDK.

## Installation

```bash
pip install xccy
```

Or install from source:

```bash
git clone https://github.com/xccy-finance/xccy-sdk.git
cd xccy-sdk
pip install -e .
```

## Initialize Client

```python
from xccy import XccyClient
from xccy.tokens import PolygonTokens

# Read-only (no transactions)
client = XccyClient(rpc_url="https://polygon-rpc.com")

# With transaction capability
client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    private_key="0x...",
    backend_url="https://api.xccy.finance",
)
```

## Working with Accounts

```python
# Default account (cross-margin)
account = client.account.create_account_id(account_id=0)

# Isolated margin on USDT
account = client.account.create_account_id(
    account_id=0,
    isolated_margin_token=PolygonTokens.USDT,
)

# Multiple accounts for different strategies
main = client.account.create_account_id(account_id=0)
hedge = client.account.create_account_id(account_id=1)
spec = client.account.create_account_id(account_id=2)
```

## Working with Decimals

The SDK provides utilities for convenient token amount handling:

```python
from xccy import parse_amount, format_amount, get_decimals

# Convert to raw units
raw = parse_amount(100, "USDT")     # 100_000_000 (6 decimals)
raw = parse_amount(0.5, "WETH")     # 500_000_000_000_000_000 (18 decimals)

# Convert back to human-readable format
formatted = format_amount(100_000_000, "USDT")  # "100.0000"
formatted = format_amount(-5000, "USDT")        # "-0.0050"

# Get token decimals
get_decimals("USDT")  # 6
get_decimals("WETH")  # 18
get_decimals("DAI")   # 18
```

## Deposit Margin

```python
from xccy import parse_amount

# Approve token (one-time)
client.margin.approve_token(PolygonTokens.USDT)

# Deposit 100 USDT
tx = client.margin.deposit(
    account=account,
    token=PolygonTokens.USDT,
    amount=parse_amount(100, "USDT"),
)
print(f"Deposited: {tx.transactionHash.hex()}")
```

## Get Pools

```python
# Get active pools from backend
pools = client.pool.list_pools(active_only=True)

for pool in pools:
    print(f"{pool.pool_id[:16]}... | TVL: ${pool.tvl_usd:.0f} | APY: {pool.apy:.2%}")

# Build PoolKey from backend data
from xccy.types import PoolKey
from web3 import Web3

pool_data = pools[0]
pool_key = PoolKey(
    underlying_asset=Web3.to_checksum_address(pool_data.underlying_token),
    compound_token=Web3.to_checksum_address(pool_data.token),
    term_start_timestamp_wad=int(pool_data.term_start_timestamp_wad),
    term_end_timestamp_wad=int(pool_data.term_end_timestamp_wad),
    fee_wad=int(pool_data.fee_wad or "100000000000000"),
    tick_spacing=pool_data.tick_spacing,
)
```

## Swap

```python
from xccy import parse_amount, format_amount

# Swap: pay fixed on 10 USDT
result = client.trading.swap(
    pool_key=pool_key,
    account=account,
    notional=parse_amount(10, "USDT"),
    is_fixed_taker=True,
)

print(f"TX: {result.transaction_hash}")
print(f"Fixed delta: {format_amount(result.fixed_token_delta, 'USDT')} USDT")
print(f"Variable delta: {format_amount(result.variable_token_delta, 'USDT')} USDT")
print(f"Margin req: {format_amount(result.position_margin_requirement, 'USDT')} USDT")
```

## Provide Liquidity

```python
# Get current tick
pool_id = pool_key.get_pool_id()
tick, _ = client.vamm_manager.functions.getVAMMState(pool_id).call()

# Tick range around current
tick_lower = ((tick // pool_key.tick_spacing) - 50) * pool_key.tick_spacing
tick_upper = ((tick // pool_key.tick_spacing) + 50) * pool_key.tick_spacing

# Mint LP
result = client.trading.mint(
    pool_key=pool_key,
    account=account,
    tick_lower=tick_lower,
    tick_upper=tick_upper,
    liquidity=100_000,
)

print(f"TX: {result.transaction_hash}")
print(f"Liquidity: {result.liquidity:,}")
print(f"Margin req: {format_amount(result.margin_requirement, 'USDT')} USDT")

# Burn LP
result = client.trading.burn(
    pool_key=pool_key,
    account=account,
    tick_lower=tick_lower,
    tick_upper=tick_upper,
    liquidity=100_000,
)
```

## Oracle Data

```python
# Token price in USD
price = client.oracle.get_price_usd(PolygonTokens.USDT)
print(f"USDT: ${price:.4f}")

# Yield-bearing token APR
apr = client.oracle.get_apr(PolygonTokens.A_USDT)
print(f"aUSDT APR: {apr * 100:.2f}%")
```

## Monitor Positions

```python
# Active positions (from backend)
positions = client.position.get_active_positions()
print(f"Active positions: {len(positions)}")

# User metrics
metrics = client.position.get_user_metrics()
print(f"Total PnL: ${metrics.total_pnl:.4f}")
print(f"Collateral: ${metrics.total_collateral:.4f}")
```

## Return Values

All transactions return structured results:

| Method | Returns |
|--------|---------|
| `swap()` | `SwapResult` — fixed/variable deltas, fee, margin_req |
| `mint()` | `MintResult` — liquidity, tick range, margin_req |
| `burn()` | `BurnResult` — liquidity, tick range, margin_req |

```python
# SwapResult fields
result.fixed_token_delta          # int: fixed token change (raw)
result.variable_token_delta       # int: variable token change (raw)
result.cumulative_fee_incurred    # int: fee amount
result.position_margin_requirement # int: required margin
result.transaction_hash           # str: tx hash
result.gas_used                   # int: gas consumed
```

## Trade Tracking

### Historical Trades

```python
# Get pool trades from backend
trades, cursor = client.trades.get_pool_trades(pool_id, limit=50)

for trade in trades:
    print(f"{trade.timestamp}: {trade.notional} @ {trade.fixed_rate:.2%}")

# Get user's trades
my_trades = client.trades.get_user_trades(pool_id, client.signer_address)
```

### Live Streaming

```python
import asyncio
from xccy import TradeEvent

# Initialize client with WebSocket URL
client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    private_key="0x...",
    ws_rpc_url="wss://polygon-mainnet.g.alchemy.com/v2/KEY",
)

# Async iterator (recommended)
async def trading_strategy():
    async for event in client.stream.events(event_types=["Swap"]):
        print(f"New swap: {event.tx_hash}")
        await handle_trade(event)

asyncio.run(trading_strategy())

# Or wait for single event
async def wait_for_fill():
    event = await client.stream.next_event(
        user_address=client.signer_address,
        timeout=60.0,
    )
    print(f"My trade: {event.tx_hash}")
```

## Next Steps

- [Account System](accounts.md) — Sub-accounts and margin modes
- [Trading Guide](trading.md) — Swap and LP details
- [Trade Tracking](trades.md) — Historical and live trades
- [Margin Operations](margin.md) — Deposit, withdraw
- [Health Monitoring](health.md) — Risk tracking
