# Typed Bitget

> A fully typed, validated async client for the Bitget API

**Use autocomplete instead of documentation.**

```python
from bitget import Bitget

async with Bitget.new() as client:
    assets = await client.spot.account.assets()
    for asset in assets:
        print(f"{asset['coin']}: {asset['available']}")
```

## Why Typed Bitget?

- **🎯 Precise Types**: Literal types, not strings. Your IDE knows exactly what's valid.
- **✅ Automatic Validation**: Pydantic-powered response validation catches API changes instantly.
- **⚡ Async First**: Built on `httpx` for high-performance async operations.
- **🔒 Type Safety**: Full type hints throughout. Catch errors before runtime.
- **🎨 Beautiful DX**: No unnecessary imports, sensible defaults, optional complexity.
- **📦 Batteries Included**: Pagination helpers, decimal precision, timestamp parsing.

## Installation

```bash
pip install typed-bitget
```

## Quick Start

### 1. Set up API credentials

```bash
export BITGET_ACCESS_KEY="your_access_key"
export BITGET_SECRET_KEY="your_secret_key"
export BITGET_PASSPHRASE="your_passphrase"
```

### 2. Start trading

```python
from bitget import Bitget

async with Bitget.new() as client:
    # Get spot account assets
    assets = await client.spot.account.assets()
    
    # Get futures positions
    positions = await client.futures.position.all_positions(
        product_type='USDT-FUTURES'
    )
    
    # Check overall balance
    overview = await client.common.assets.overview()
```

## Features

### No Unnecessary Imports

Notice something? **You never imported `Literal` types.** Just use strings:

```python
# ❌ Other libraries
from some_sdk import ProductType
positions = await client.get_positions(product_type=ProductType.USDT_FUTURES)

# ✅ Typed Bitget
positions = await client.futures.position.all_positions(
    product_type='USDT-FUTURES'  # Your IDE autocompletes this!
)
```

### Precise Type Annotations

Every field is precisely typed. Prices are `Decimal`, timestamps are `datetime`, enums are `Literal` types:

```python
from decimal import Decimal
from datetime import datetime

assets = await client.spot.account.assets()
for asset in assets:
    coin: str = asset['coin']
    available: Decimal = asset['available']  # Not float!
    updated: datetime = asset['uTime']       # Not int!
```

### Automatic Validation

Response validation is **on by default** but can be disabled:

```python
# Validated (default) - throws ValidationError if API response changes
assets = await client.spot.account.assets()

# Skip validation for maximum performance
assets = await client.spot.account.assets(validate=False)
```

### Built-in Pagination

```python
# Manual pagination
response = await client.futures.trade.fills(
    product_type='USDT-FUTURES',
    symbol='BTCUSDT',
    limit=100
)

# Automatic pagination - yields chunks as they arrive
async for chunk in client.futures.trade.fills_paged(
    product_type='USDT-FUTURES',
    symbol='BTCUSDT'
):
    for fill in chunk:
        print(f"Trade: {fill['price']} @ {fill['baseVolume']}")
```

## API Coverage

This library is a **work in progress** with **many missing endpoints**. 

Current implementation includes ~40 methods across spot, futures, margin, earn, and copy trading. However, major functionality like order placement, order management, and WebSocket streams are not yet implemented.

📋 **See [API Overview](docs/api-overview.md) for complete coverage details.**

## Documentation

- [**Quickstart Guide**](docs/quickstart.md) - Get up and running in 5 minutes
- [**Authentication**](docs/authentication.md) - API credentials setup
- [**API Overview**](docs/api-overview.md) - Available endpoints and modules
- [**Examples**](docs/examples.md) - Common use cases and patterns
- [**Design Philosophy**](docs/design-philosophy.md) - Why we built it this way

## Design Philosophy

Typed Bitget follows the principles outlined in [**this blog post**](https://tribulnation.com/blog/clients):

1. **Inputs shouldn't require custom imports** - Use string literals, not enums
2. **Annotate types precisely** - `Literal` types, `Decimal` for prices, `datetime` for timestamps
3. **Avoid unnecessary complication** - Sensible defaults, optional complexity
4. **Provide extra behavior optionally** - Pagination and validation are opt-in

**Details matter. Developer experience matters.**

## Examples

### Portfolio Tracking

```python
async with Bitget.new() as client:
    overview = await client.common.assets.overview()
    
    total_balance = sum(
        account['usdtBalance'] 
        for account in overview
    )
    print(f"Total Portfolio: ${total_balance:,.2f}")
```

### Trading Bot

```python
async with Bitget.new() as client:
    # Get current positions
    positions = await client.futures.position.all_positions(
        product_type='USDT-FUTURES',
        symbol='BTCUSDT'
    )
    
    # Get recent fills
    fills = await client.futures.trade.fills(
        product_type='USDT-FUTURES',
        symbol='BTCUSDT',
        limit=50
    )
```

### Tax Reporting

```python
from datetime import datetime

async with Bitget.new() as client:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    
    records = await client.common.tax.spot_transaction_records(
        start=start,
        end=end
    )
```

## Error Handling

```python
from bitget import Bitget
from bitget.core import ApiError, ValidationError, NetworkError

async with Bitget.new() as client:
    try:
        assets = await client.spot.account.assets()
    except ValidationError:
        # API response doesn't match expected schema
        pass
    except ApiError as e:
        # Bitget API returned an error
        print(f"API Error: {e}")
    except NetworkError:
        # Network/connection issue
        pass
```

## Contributing

This is a work in progress! Contributions are welcome. The codebase is designed to be:

- **Consistent**: All endpoints follow the same patterns
- **Type-safe**: Everything is fully typed
- **Validated**: Pydantic models for all responses

---

Inspired by [this blog post](https://tribulnation.com/blog/clients) on building better API clients.

Built with ❤️ by [Tribulnation](https://tribulnation.com)
