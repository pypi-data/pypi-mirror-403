# Trade Tracking

The SDK provides two methods for tracking trades:

1. **Historical trades** via backend API
2. **Live streaming** via WebSocket RPC

## Historical Trades

Query past trades from the indexed backend API.

### Get Pool Trades

```python
from xccy import XccyClient

client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    backend_url="https://api.xccy.finance",
)

# Get recent trades for a pool
trades, cursor = client.trades.get_pool_trades(
    pool_id="0x...",
    limit=50,
)

for trade in trades:
    print(f"{trade.timestamp}: {trade.notional} @ {trade.fixed_rate:.2%}")
    print(f"  Trader: {trade.trader}")
    print(f"  Type: {'Fixed Taker' if trade.is_fixed_taker else 'Variable Taker'}")
```

### Filter by User

```python
# Get trades for a specific user
my_trades = client.trades.get_user_trades(
    pool_id="0x...",
    user_address="0x...",
    limit=100,
)

total_volume = sum(t.notional for t in my_trades)
print(f"My total volume: {total_volume}")
```

### Pagination

```python
# Fetch all trades with pagination
all_trades = []
cursor = None

while True:
    trades, cursor = client.trades.get_pool_trades(
        pool_id="0x...",
        cursor=cursor,
        limit=200,
    )
    all_trades.extend(trades)
    
    if not cursor:
        break

print(f"Total trades: {len(all_trades)}")
```

Or use the convenience method:

```python
all_trades = client.trades.get_all_pool_trades(
    pool_id="0x...",
    max_trades=1000,
)
```

## Live Streaming

Subscribe to real-time trade events via WebSocket.

### Setup

```python
import os
from xccy import XccyClient

client = XccyClient(
    rpc_url=os.getenv("POLYGON_RPC"),
    ws_rpc_url=os.getenv("WS_POLYGON_RPC"),  # wss://...
)
```

### Subscribe to Events

```python
from xccy import TradeEvent

def on_trade(event: TradeEvent):
    print(f"New {event.event_type}!")
    print(f"  Pool: {event.pool_id[:16]}...")
    print(f"  User: {event.sender}")
    print(f"  TX: {event.tx_hash}")
    print(f"  Block: {event.block_number}")
    
    if event.event_type == "Swap":
        print(f"  Fixed delta: {event.fixed_token_delta}")
        print(f"  Variable delta: {event.variable_token_delta}")
    elif event.event_type in ("Mint", "Burn"):
        print(f"  Amount: {event.amount}")

# Subscribe to all events
client.stream.subscribe(on_trade)

# Filter by event type
client.stream.subscribe(on_trade, event_types=["Swap"])

# Filter by pool
client.stream.subscribe(on_trade, pool_id="0x...")

# Filter by user (track your own trades)
client.stream.subscribe(on_trade, user_address="0x...")

# Combine filters (my swaps in a specific pool)
client.stream.subscribe(
    on_trade,
    pool_id="0x...",
    user_address="0x...",
    event_types=["Swap"],
)
```

### Start Listening

**Blocking mode (callback-based):**

```python
client.stream.subscribe(on_trade)
client.stream.start()  # Blocks forever
```

**Background mode (callback-based):**

```python
client.stream.subscribe(on_trade)
client.stream.start_background()

# ... do other work ...

client.stream.stop()
```

## Async Iterator (Recommended for Strategies)

For trading strategies, use the async iterator interface instead of callbacks.

### Iterate Over Events

```python
import asyncio

async def trading_strategy():
    # React to every swap
    async for event in client.stream.events(event_types=["Swap"]):
        print(f"New swap: {event.variable_token_delta}")
        
        if should_trade(event):
            await execute_counter_trade(event)

asyncio.run(trading_strategy())
```

### Filter Events

```python
async def my_trades():
    # Only my trades in a specific pool
    async for event in client.stream.events(
        pool_id="0x...",
        user_address=client.signer_address,
        event_types=["Swap"],
    ):
        print(f"My trade filled: {event.tx_hash}")
```

### Wait for Single Event

```python
async def wait_for_fill():
    # Wait for my next swap (with timeout)
    event = await client.stream.next_event(
        user_address=client.signer_address,
        event_types=["Swap"],
        timeout=60.0,  # 60 seconds
    )
    print(f"Order filled: {event.tx_hash}")
```

### Collect Multiple Events

```python
async def analyze_trades():
    # Collect next 100 swaps
    events = await client.stream.collect(
        count=100,
        event_types=["Swap"],
        timeout=300.0,  # 5 minutes
    )
    
    total_volume = sum(abs(e.variable_token_delta) for e in events)
    print(f"Volume in last 100 trades: {total_volume}")
```

### Parallel Processing

```python
import asyncio

async def main():
    # Run strategy alongside other tasks
    strategy_task = asyncio.create_task(trading_strategy())
    monitor_task = asyncio.create_task(monitor_health())
    
    await asyncio.gather(strategy_task, monitor_task)
```

### Event Types

| Event | Description | Key Fields |
|-------|-------------|------------|
| `Swap` | Trader swap | `fixed_token_delta`, `variable_token_delta`, `fee_incurred` |
| `Mint` | LP adds liquidity | `amount`, `tick_lower`, `tick_upper` |
| `Burn` | LP removes liquidity | `amount`, `tick_lower`, `tick_upper` |

### TradeEvent Fields

```python
@dataclass
class TradeEvent:
    event_type: str      # "Swap", "Mint", "Burn"
    pool_id: str         # Pool identifier
    sender: str          # Transaction sender
    block_number: int    # Block number
    tx_hash: str         # Transaction hash
    log_index: int       # Log index
    timestamp: int       # Block timestamp (if available)
    
    # Swap-specific
    fixed_token_delta: int
    variable_token_delta: int
    fee_incurred: int
    
    # Mint/Burn-specific
    amount: int          # Liquidity amount
    tick_lower: int
    tick_upper: int
```

## Example: Trade Monitor

```python
import os
import asyncio
from decimal import Decimal
from xccy import XccyClient, TradeEvent, format_amount

client = XccyClient(
    rpc_url=os.getenv("POLYGON_RPC"),
    ws_rpc_url=os.getenv("WS_POLYGON_RPC"),
    backend_url="https://api.xccy.finance",
)

def on_swap(event: TradeEvent):
    notional = format_amount(abs(event.variable_token_delta), "USDC")
    direction = "Fixed Taker" if event.variable_token_delta > 0 else "Variable Taker"
    print(f"[SWAP] {notional} USDC ({direction})")
    print(f"       TX: {event.tx_hash}")

def on_lp(event: TradeEvent):
    action = "Added" if event.event_type == "Mint" else "Removed"
    print(f"[LP] {action} liquidity: {event.amount}")
    print(f"     Range: [{event.tick_lower}, {event.tick_upper}]")

# Subscribe to events
client.stream.subscribe(on_swap, event_types=["Swap"])
client.stream.subscribe(on_lp, event_types=["Mint", "Burn"])

print("Listening for trades...")
client.stream.start()
```

## WebSocket Providers

The SDK works with any WebSocket RPC provider:

| Provider | URL Format |
|----------|------------|
| Alchemy | `wss://polygon-mainnet.g.alchemy.com/v2/KEY` |
| Infura | `wss://polygon-mainnet.infura.io/ws/v3/KEY` |
| QuickNode | `wss://xxx.polygon.quiknode.pro/KEY` |

Store your WebSocket URL in `.env`:

```bash
WS_POLYGON_RPC=wss://polygon-mainnet.g.alchemy.com/v2/your-api-key
```
