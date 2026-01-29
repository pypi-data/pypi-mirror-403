# API Reference

Complete API documentation auto-generated from source code.

## Client

::: xccy.client.XccyClient
    options:
      show_source: false
      members:
        - __init__
        - account
        - margin
        - trading
        - position
        - oracle
        - pool
        - backend

## Account Management

::: xccy.account.AccountManager
    options:
      show_source: false

## Margin Operations

::: xccy.margin.MarginManager
    options:
      show_source: false

## Trading

::: xccy.trading.TradingManager
    options:
      show_source: false

## Position Queries

::: xccy.position.PositionManager
    options:
      show_source: false

## Oracle Data

::: xccy.oracle.OracleManager
    options:
      show_source: false

## Pool Information

::: xccy.pool.PoolManager
    options:
      show_source: false

## Data Types

::: xccy.types.AccountId
    options:
      show_source: false

::: xccy.types.PoolKey
    options:
      show_source: false

::: xccy.types.SwapParams
    options:
      show_source: false

::: xccy.types.SwapResult
    options:
      show_source: false

::: xccy.types.PositionInfo
    options:
      show_source: false

::: xccy.types.HealthStatus
    options:
      show_source: false

## Math Utilities

### Tick Math

::: xccy.math.tick
    options:
      show_source: false
      members:
        - tick_to_sqrt_price_x96
        - sqrt_price_x96_to_tick
        - tick_to_fixed_rate
        - fixed_rate_to_tick
        - align_tick_to_spacing

### Liquidity Math

::: xccy.math.liquidity
    options:
      show_source: false
      members:
        - liquidity_to_notional
        - notional_to_liquidity
        - get_amount0_delta
        - get_amount1_delta

### Fixed-Point Math

::: xccy.math.fixed_point
    options:
      show_source: false
      members:
        - wad_to_decimal
        - decimal_to_wad
        - ray_to_decimal
        - decimal_to_ray

## Token Constants

::: xccy.tokens.PolygonTokens
    options:
      show_source: false

## Exceptions

::: xccy.exceptions
    options:
      show_source: false
