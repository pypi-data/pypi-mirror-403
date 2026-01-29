# xccy-py

Python SDK for the **XCCY Protocol** — an Interest Rate Swap AMM on Polygon.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             xccy-py SDK                                 │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────────┤
│ account │ margin  │ trading │position │ oracle  │ trades  │   stream    │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴──────┬──────┘
     │         │         │         │         │         │           │
     ▼         ▼         ▼         ▼         ▼         ▼           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  On-Chain (Polygon)                     │ Backend │ WebSocket RPC       │
│  CollateralEngine │ VAMMManager │ Oracles│ api.xccy│ wss://...           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install xccy
```

## Quick Start

```python
from xccy import XccyClient
from xccy.tokens import PolygonTokens

# Initialize client
client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    private_key="0x...",  # Optional, for signing transactions
)

# Create account identifier
account = client.account.create_account_id(
    owner="0xYourWallet...",
    account_id=0,
    isolated_margin_token=None  # Cross-margin mode
)

# Deposit margin
tx = client.margin.deposit(
    account=account,
    token=PolygonTokens.USDC,
    amount=1000 * 10**6  # 1000 USDC
)
print(f"Deposit tx: {tx.transactionHash.hex()}")

# Check health
obligations = client.position.get_obligations(account)
margin_value = client.margin.get_total_value_usd(account)
health = margin_value / obligations if obligations > 0 else float('inf')
print(f"Health factor: {health:.2f}")
```

## Features

### Multi-Account System

One wallet can own multiple sub-accounts with independent positions and margin:

```python
# Cross-margin account
main = client.account.create_account_id(owner="0x...", account_id=0)

# Isolated margin account (USDC only)
isolated = client.account.create_account_id(
    owner="0x...", 
    account_id=1,
    isolated_margin_token=PolygonTokens.USDC
)
```

### Trading (Swap & LP)

```python
from xccy.math import fixed_rate_to_tick, notional_to_liquidity

# Execute a swap (pay fixed rate)
result = client.trading.swap(
    pool_key=pool,
    account=account,
    notional=10_000 * 10**6,
    is_fixed_taker=True,
    tick_lower=-6930,
    tick_upper=-6900,
)

# Provide liquidity with notional amount
tick_lower = fixed_rate_to_tick(0.06)  # 6%
tick_upper = fixed_rate_to_tick(0.04)  # 4%
liquidity = notional_to_liquidity(10_000 * 10**6, tick_lower, tick_upper)

client.trading.mint(pool, account, tick_lower, tick_upper, liquidity)
```

### Oracle Data

```python
# Get USD price
price = client.oracle.get_price_usd(PolygonTokens.USDC)

# Get current APR
apr = client.oracle.get_apr(PolygonTokens.A_USDC)

# Get rate between timestamps
rate = client.oracle.get_rate_from_to(
    asset=PolygonTokens.A_USDC,
    from_timestamp=1704067200,
    to_timestamp=1735689600
)
```

### Trade Tracking

```python
# Historical trades from backend
trades, cursor = client.trades.get_pool_trades(pool_id, limit=50)
for trade in trades:
    print(f"{trade.timestamp}: {trade.notional} @ {trade.fixed_rate:.2%}")

# User trades
my_trades = client.trades.get_user_trades(pool_id, my_address)
```

### Live Streaming (WebSocket)

```python
import asyncio
from xccy import XccyClient, TradeEvent

client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    ws_rpc_url="wss://polygon-mainnet.g.alchemy.com/v2/KEY",
)

# Async iterator (recommended for trading strategies)
async def trading_strategy():
    async for event in client.stream.events(event_types=["Swap"]):
        print(f"New swap: {event.variable_token_delta}")
        await react_to_trade(event)

# Wait for specific event
async def wait_for_my_fill():
    event = await client.stream.next_event(
        user_address=my_address,
        event_types=["Swap"],
        timeout=60.0,
    )
    print(f"Filled: {event.tx_hash}")

asyncio.run(trading_strategy())
```

### Math Utilities

```python
from xccy.math import (
    tick_to_fixed_rate,
    fixed_rate_to_tick,
    liquidity_to_notional,
    notional_to_liquidity,
    wad_to_decimal,
)

# Tick ↔ Rate conversions
rate = tick_to_fixed_rate(-6930)  # ~5% APR
tick = fixed_rate_to_tick(0.05)

# Liquidity ↔ Notional
liquidity = notional_to_liquidity(10_000 * 10**6, tick_lower, tick_upper)
notional = liquidity_to_notional(liquidity, tick_lower, tick_upper)
```

## Documentation

Full documentation available at [docs.xccy.finance](https://docs.xccy.finance)

- [Quick Start Guide](docs/quickstart.md)
- [Account System](docs/accounts.md)
- [Margin Operations](docs/margin.md)
- [Trading Guide](docs/trading.md)
- [Trade Tracking](docs/trades.md)
- [Health Monitoring](docs/health.md)
- [API Reference](docs/api-reference.md)

## Development

```bash
# Clone and install
git clone https://github.com/xccy-finance/xccy-sdk.git
cd xccy-sdk
pip install -e ".[dev,docs]"

# Run tests
pytest

# Run linter
ruff check xccy/

# Type check
mypy xccy/

# Build docs
mkdocs serve
```

## License

MIT License
