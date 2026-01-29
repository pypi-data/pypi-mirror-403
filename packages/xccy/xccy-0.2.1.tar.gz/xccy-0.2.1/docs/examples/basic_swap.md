# Basic Swap Example

Simple swap operation example.

## Setup

```python
import os
from xccy import XccyClient, parse_amount, format_amount
from xccy.tokens import PolygonTokens
from xccy.types import PoolKey
from web3 import Web3

# Initialize
client = XccyClient(
    rpc_url=os.environ["POLYGON_RPC"],
    private_key=os.environ["PK"],
    backend_url="https://api.xccy.finance",
)

print(f"Wallet: {client.signer_address}")
```

## Get Pool

```python
# Active pools from backend
pools = client.pool.list_pools(active_only=True)
print(f"Found {len(pools)} active pools")

# Select aUSDT pool
usdt_pool = next(
    (p for p in pools if p.token and "6ab707" in p.token.lower()),
    None
)

if not usdt_pool:
    raise ValueError("No aUSDT pool found")

# Build PoolKey
pool_key = PoolKey(
    underlying_asset=Web3.to_checksum_address(usdt_pool.underlying_token),
    compound_token=Web3.to_checksum_address(usdt_pool.token),
    term_start_timestamp_wad=int(usdt_pool.term_start_timestamp_wad),
    term_end_timestamp_wad=int(usdt_pool.term_end_timestamp_wad),
    fee_wad=int(usdt_pool.fee_wad or "100000000000000"),
    tick_spacing=usdt_pool.tick_spacing,
)

print(f"Pool ID: {pool_key.get_pool_id().hex()[:24]}...")
```

## Create Account

```python
# Isolated margin on USDT
account = client.account.create_account_id(
    account_id=0,
    isolated_margin_token=PolygonTokens.USDT,
)

print(f"Account: owner={account.owner[:10]}..., id={account.account_id}")
```

## Swap

```python
# Swap 0.1 USDT, pay fixed
result = client.trading.swap(
    pool_key=pool_key,
    account=account,
    notional=parse_amount(0.1, "USDT"),
    is_fixed_taker=True,
)

print("=" * 50)
print("SWAP RESULT")
print("=" * 50)
print(f"TX: {result.transaction_hash}")
print(f"Gas: {result.gas_used:,}")
print()
print(f"Fixed delta:    {format_amount(result.fixed_token_delta, 'USDT')} USDT")
print(f"Variable delta: {format_amount(result.variable_token_delta, 'USDT')} USDT")
print(f"Fee:            {format_amount(result.cumulative_fee_incurred, 'USDT')} USDT")
print(f"Margin req:     {format_amount(result.position_margin_requirement, 'USDT')} USDT")
```

## Output

```
Wallet: 0x7f5ff301328391930fFfbb1a781CAB47f5Ec48C4
Found 13 active pools
Pool ID: 0x53b3fb0b1b284fcf6afe7a...
Account: owner=0x7f5ff301..., id=0
==================================================
SWAP RESULT
==================================================
TX: 52191271171d27205a121c8230bfafcbc59dc32f...
Gas: 732,485

Fixed delta:    0.0149 USDT
Variable delta: -0.0050 USDT
Fee:            0.0000 USDT
Margin req:     0.0132 USDT
```
