# Monitor Health Example

Monitor positions and health factor.

## Setup

```python
import os
from xccy import XccyClient
from xccy.tokens import PolygonTokens

client = XccyClient(
    rpc_url=os.environ["POLYGON_RPC"],
    private_key=os.environ["PK"],
    backend_url="https://api.xccy.finance",
)

account = client.account.create_account_id(
    account_id=0,
    isolated_margin_token=PolygonTokens.USDT,
)
```

## Get Positions

```python
# Active positions (from backend)
positions = client.position.get_active_positions()

print(f"Active positions: {len(positions)}")
for pos in positions[:5]:  # First 5
    print(f"  {pos.pool_id[:24]}...")
    print(f"    PnL: ${pos.pnl:.4f}")
    print(f"    Notional: ${pos.notional:.2f}")
```

## User Metrics

```python
# Aggregated metrics
metrics = client.position.get_user_metrics()

print(f"Total PnL: ${metrics.total_pnl:.4f}")
print(f"Collateral: ${metrics.total_collateral:.4f}")
print(f"Positions: {metrics.active_position_count}")
```

## Check Health

```python
# Obligations (in WAD)
obligations = client.position.get_obligations(account)
print(f"Obligations: ${obligations:.4f}")

# Health status (if method available)
try:
    status = client.position.get_health_status(account)
    print(f"Health Factor: {status.health_factor:.2f}")
    print(f"Liquidatable: {status.is_liquidatable}")
except Exception as e:
    print(f"Health check: {e}")
```

## Oracle Data

```python
# Current prices and APR
try:
    usdt_price = client.oracle.get_price_usd(PolygonTokens.USDT)
    print(f"USDT: ${usdt_price:.4f}")
except Exception as e:
    print(f"USDT price: {e}")

try:
    apr = client.oracle.get_apr(PolygonTokens.A_USDT)
    print(f"aUSDT APR: {apr * 100:.2f}%")
except Exception as e:
    print(f"aUSDT APR: {e}")
```

## Full Dashboard

```python
import os
from xccy import XccyClient, format_amount
from xccy.tokens import PolygonTokens

def dashboard(client, account):
    """Full account dashboard."""
    
    print("=" * 60)
    print("  ACCOUNT DASHBOARD")
    print("=" * 60)
    print(f"  Owner: {account.owner}")
    print(f"  ID: {account.account_id}")
    print(f"  Mode: {'Isolated ' + account.isolated_margin_token[:10] if account.isolated_margin_token else 'Cross-margin'}")
    print()
    
    # Positions
    print("POSITIONS")
    print("-" * 60)
    try:
        positions = client.position.get_active_positions()
        if positions:
            for pos in positions[:5]:
                print(f"  {pos.pool_id[:24]}... | PnL: ${pos.pnl:+.4f}")
        else:
            print("  No active positions")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Metrics
    print("METRICS")
    print("-" * 60)
    try:
        metrics = client.position.get_user_metrics()
        print(f"  Total PnL:    ${metrics.total_pnl:+.4f}")
        print(f"  Collateral:   ${metrics.total_collateral:.4f}")
        print(f"  Positions:    {metrics.active_position_count}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Oracles
    print("ORACLES")
    print("-" * 60)
    try:
        price = client.oracle.get_price_usd(PolygonTokens.USDT)
        print(f"  USDT:   ${price:.4f}")
    except:
        print("  USDT:   N/A")
    
    try:
        apr = client.oracle.get_apr(PolygonTokens.A_USDT)
        print(f"  aUSDT APR: {apr * 100:.2f}%")
    except:
        print("  aUSDT APR: N/A")
    
    print()
    print("=" * 60)

# Run
client = XccyClient(
    rpc_url=os.environ["POLYGON_RPC"],
    private_key=os.environ["PK"],
    backend_url="https://api.xccy.finance",
)

account = client.account.create_account_id(
    account_id=0,
    isolated_margin_token=PolygonTokens.USDT,
)

dashboard(client, account)
```

## Output

```
============================================================
  ACCOUNT DASHBOARD
============================================================
  Owner: 0x7f5ff301328391930fFfbb1a781CAB47f5Ec48C4
  ID: 0
  Mode: Isolated 0xc2132D05

POSITIONS
------------------------------------------------------------
  0x53b3fb0b1b284fcf6afe7a... | PnL: $+0.0050
  0x8a92b1c3d4e5f6789012ab... | PnL: $-0.0012

METRICS
------------------------------------------------------------
  Total PnL:    $+1.0200
  Collateral:   $9.2000
  Positions:    10

ORACLES
------------------------------------------------------------
  USDT:   $1.0000
  aUSDT APR: 2.98%

============================================================
```
