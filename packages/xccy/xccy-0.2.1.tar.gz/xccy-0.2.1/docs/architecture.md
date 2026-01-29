# Architecture

Understanding the XCCY Protocol architecture and how the SDK interacts with it.

## System Overview

```mermaid
flowchart TB
    subgraph SDK["xccy-py SDK"]
        Client[XccyClient]
        Account[account]
        Margin[margin]
        Trading[trading]
        Position[position]
        Oracle[oracle]
        Pool[pool]
        Math[math]
    end
    
    subgraph Contracts["On-Chain (Polygon)"]
        CE[CollateralEngine]
        VM[VAMMManager]
        OH[OracleHub]
        AO[AprOracle]
        OP[Operator]
    end
    
    subgraph Backend["Backend API (optional)"]
        API[api.xccy.finance]
        DB[(Indexed Data)]
    end
    
    Client --> Account & Margin & Trading & Position & Oracle & Pool
    Margin --> CE
    Trading --> VM & OP
    Oracle --> OH & AO
    Position --> CE
    Pool --> VM
    Position -.-> API
    Pool -.-> API
    API --> DB
```

## Core Components

### 1. XccyClient

The main entry point that aggregates all functionality:

```python
client = XccyClient(
    rpc_url="https://polygon-rpc.com",
    private_key="0x...",  # Optional
    network="polygon",
    backend_url="https://api.xccy.finance",  # Optional
)
```

### 2. Smart Contracts

| Contract | Purpose | SDK Module |
|----------|---------|------------|
| CollateralEngine | Margin, positions, health | `margin`, `position` |
| VAMMManager | Pool state, swaps, LP | `pool`, `trading` |
| OracleHub | Token prices | `oracle` |
| AprOracle | APR/APY data | `oracle` |
| Operator | Batched operations | `trading` |

### 3. Data Flow

```mermaid
sequenceDiagram
    participant User
    participant SDK
    participant Contract
    participant Oracle
    
    User->>SDK: deposit(account, USDC, 1000)
    SDK->>Contract: updateAccountMargin()
    Contract->>Oracle: getPriceUsdWad(USDC)
    Oracle-->>Contract: price
    Contract-->>SDK: success
    SDK-->>User: TxReceipt
```

## Data Source Strategy

The SDK follows a **contracts-first** approach:

```mermaid
flowchart LR
    subgraph RealTime["Real-Time Data (Contracts)"]
        Balances[Margin Balances]
        Health[Health Factor]
        State[Pool State]
        Prices[Oracle Prices]
    end
    
    subgraph Historical["Historical Data (Backend)"]
        PnL[PnL History]
        Charts[Price Charts]
        TVL[Pool Rankings]
        Trades[Trade History]
    end
    
    Contracts[(Polygon)] --> RealTime
    Backend[(API)] --> Historical
```

| Data Type | Source | Reason |
|-----------|--------|--------|
| Margin balances | Contract | Real-time accuracy |
| Health factor | Contract | Critical for liquidation |
| Pool state | Contract | Current price/tick |
| Token prices | Contract | Oracle freshness |
| PnL history | Backend | Requires indexing |
| Price charts | Backend | Aggregated over time |
| Pool rankings | Backend | TVL calculation |

## Module Architecture

```mermaid
classDiagram
    class XccyClient {
        +web3: Web3
        +config: NetworkConfig
        +account: AccountManager
        +margin: MarginManager
        +trading: TradingManager
        +position: PositionManager
        +oracle: OracleManager
        +pool: PoolManager
        +backend: BackendClient
    }
    
    class AccountManager {
        +create_account_id()
        +set_operator()
        +is_operator()
    }
    
    class MarginManager {
        +deposit()
        +withdraw()
        +get_balance()
        +get_total_value_usd()
    }
    
    class TradingManager {
        +swap()
        +mint()
        +burn()
    }
    
    XccyClient --> AccountManager
    XccyClient --> MarginManager
    XccyClient --> TradingManager
```

## Network Configuration

The SDK supports multiple networks through `NetworkConfig`:

```python
from xccy.constants import POLYGON_CONFIG

print(POLYGON_CONFIG.chain_id)        # 137
print(POLYGON_CONFIG.collateral_engine)  # 0x23e2...
print(POLYGON_CONFIG.vamm_manager)       # 0xe8FE...
```

## Error Handling

```mermaid
classDiagram
    class XccyError {
        +message: str
    }
    
    class InsufficientMarginError {
        +required: int
        +available: int
        +shortfall: int
    }
    
    class PoolNotFoundError {
        +pool_id: str
    }
    
    class TransactionFailedError {
        +tx_hash: str
        +revert_reason: str
    }
    
    XccyError <|-- InsufficientMarginError
    XccyError <|-- PoolNotFoundError
    XccyError <|-- TransactionFailedError
```
