# Margin Management Example

Margin operations: deposit, check balance, withdraw.

## Setup

```python
import os
from xccy import XccyClient, parse_amount, format_amount
from xccy.tokens import PolygonTokens

client = XccyClient(
    rpc_url=os.environ["POLYGON_RPC"],
    private_key=os.environ["PK"],
    backend_url="https://api.xccy.finance",
)

# Create account
account = client.account.create_account_id(
    account_id=0,
    isolated_margin_token=PolygonTokens.USDT,
)

print(f"Wallet: {client.signer_address}")
print(f"Account: {account.account_id}, margin: {account.isolated_margin_token[:10]}...")
```

## Approve Token

```python
# Approve (one-time)
print("Approving USDT...")
tx = client.margin.approve_token(PolygonTokens.USDT)
print(f"Approved: {tx.transactionHash.hex()}")
```

## Deposit

```python
# Deposit 10 USDT
amount = parse_amount(10, "USDT")
print(f"Depositing {format_amount(amount, 'USDT')} USDT...")

tx = client.margin.deposit(
    account=account,
    token=PolygonTokens.USDT,
    amount=amount,
)

print(f"Deposited: {tx.transactionHash.hex()}")
```

## Check Balance

```python
# Balance in protocol
balance = client.margin.get_balance(account, PolygonTokens.USDT)
print(f"Protocol balance: {format_amount(balance, 'USDT')} USDT")
```

## Withdraw

```python
# Withdraw 5 USDT
withdraw_amount = parse_amount(5, "USDT")
print(f"Withdrawing {format_amount(withdraw_amount, 'USDT')} USDT...")

tx = client.margin.withdraw(
    account=account,
    token=PolygonTokens.USDT,
    amount=withdraw_amount,
)

print(f"Withdrawn: {tx.transactionHash.hex()}")
```

## Check Obligations

```python
# How much margin is used by positions (in WAD)
obligations = client.position.get_obligations(account)
print(f"Obligations: ${obligations:.4f}")
```

## Full Example

```python
import os
from xccy import XccyClient, parse_amount, format_amount
from xccy.tokens import PolygonTokens

def main():
    client = XccyClient(
        rpc_url=os.environ["POLYGON_RPC"],
        private_key=os.environ["PK"],
        backend_url="https://api.xccy.finance",
    )
    
    account = client.account.create_account_id(
        account_id=0,
        isolated_margin_token=PolygonTokens.USDT,
    )
    
    print("=" * 50)
    print("MARGIN MANAGEMENT")
    print("=" * 50)
    
    # Approve
    print("\n1. Approve")
    client.margin.approve_token(PolygonTokens.USDT)
    print("   ✓ Approved")
    
    # Deposit
    print("\n2. Deposit 10 USDT")
    tx = client.margin.deposit(account, PolygonTokens.USDT, parse_amount(10, "USDT"))
    print(f"   ✓ TX: {tx.transactionHash.hex()[:20]}...")
    
    # Balance
    print("\n3. Check balance")
    balance = client.margin.get_balance(account, PolygonTokens.USDT)
    print(f"   Balance: {format_amount(balance, 'USDT')} USDT")
    
    # Withdraw
    print("\n4. Withdraw 5 USDT")
    tx = client.margin.withdraw(account, PolygonTokens.USDT, parse_amount(5, "USDT"))
    print(f"   ✓ TX: {tx.transactionHash.hex()[:20]}...")
    
    # Final balance
    print("\n5. Final balance")
    balance = client.margin.get_balance(account, PolygonTokens.USDT)
    print(f"   Balance: {format_amount(balance, 'USDT')} USDT")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
```

## Output

```
==================================================
MARGIN MANAGEMENT
==================================================

1. Approve
   ✓ Approved

2. Deposit 10 USDT
   ✓ TX: 0x1234567890abcdef...

3. Check balance
   Balance: 10.0000 USDT

4. Withdraw 5 USDT
   ✓ TX: 0xabcdef1234567890...

5. Final balance
   Balance: 5.0000 USDT

==================================================
```
