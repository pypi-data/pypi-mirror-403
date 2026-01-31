# Kuru Market Maker SDK (Python)

A Python SDK for building market maker bots on the Kuru protocol.

## Features

- **Unified Order Types** - Single `Order` class supporting limit, market, and cancel operations
- **Type Safety** - Full validation of Solidity uint bounds (uint32, uint40, uint96, uint256)
- **Order Lifecycle Tracking** - Track orders from creation to fill or cancellation
- **Batch Operations** - Support for batch order updates
- **Web3 Integration** - Direct interaction with Kuru orderbook smart contracts
- **Real-time Orderbook Feed** - WebSocket client for live market data with auto-reconnection

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run examples
PYTHONPATH=. uv run python examples/order_usage.py
```

## Quick Start

### Real-time Orderbook Feed

```python
from src.feed.orderbook_ws import OrderbookWebsocket

async def handle_snapshot(snapshot):
    print(f"Received snapshot for {snapshot.market_address}")
    print(f"Best bid: {snapshot.bids[0]}")
    print(f"Best ask: {snapshot.asks[0]}")

async def handle_update(update):
    print(f"Update: {update.event_type.value}")
    print(f"Order ID: {update.order_id}")

ws = OrderbookWebsocket(
    ws_url="wss://ws.kuru.io/",
    market_address="0x122C0D8683Cab344163fB73E28E741754257e3Fa",
    on_snapshot=handle_snapshot,
    on_update=handle_update,
)

await ws.connect()
```

### Creating Orders

```python
from src.manager.order import create_limit_order, create_market_order, OrderSide

# Create a limit buy order
limit_order = create_limit_order(
    cloid="my-order-001",
    side=OrderSide.BUY,
    price=50000,
    size=1000000,
    post_only=True
)

# Create a market sell order
market_order = create_market_order(
    cloid="my-order-002",
    side=OrderSide.SELL,
    size=500000,
    min_amount_out=24000000,
    is_margin=False,
    is_fill_or_kill=False
)
```

### Order Lifecycle

```python
from src.manager.order import OrderStatus

# Track order status
order.update_status(OrderStatus.ORDER_SENT)
order.update_status(OrderStatus.ORDER_PLACED)
order.set_kuru_order_id(12345)
order.update_status(OrderStatus.ORDER_FULLY_FILLED)

# Create unique ID from transaction hash
tx_hash = "0x1234567890abcdef..."
unique_id = order.create_unique_id(tx_hash)
```

## Configuration

The SDK provides a flexible configuration system with sensible defaults. You can configure everything from RPC endpoints to transaction timeouts, WebSocket reconnection behavior, and order execution preferences.

### Quick Start - Use Defaults

The simplest way to get started is to use the `ConfigManager` which automatically loads from environment variables:

```python
from src.configs import ConfigManager
from src.client import KuruClient
import os

# Load configs (reads from environment variables with defaults)
wallet_config = ConfigManager.load_wallet_config()  # Needs PRIVATE_KEY env var
connection_config = ConfigManager.load_connection_config()  # Uses default public RPC
market_config = ConfigManager.load_market_config(
    market_address=os.getenv("MARKET_ADDRESS"),
    fetch_from_chain=True  # Automatically fetches token info, decimals, precision
)

# Create client with defaults for all behavioral configs
client = await KuruClient.create(
    market_config=market_config,
    connection_config=connection_config,
    wallet_config=wallet_config,
)
```

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
PRIVATE_KEY=0x1234567890abcdef...
MARKET_ADDRESS=0x065C9d28E428A0db40191a54d33d5b7c71a9C394

# Optional - Connection endpoints (defaults provided)
RPC_URL=https://rpc.fullnode.kuru.io/
RPC_WS_URL=wss://rpc.fullnode.kuru.io/
KURU_WS_URL=wss://ws.kuru.io/
KURU_API_URL=https://api.kuru.io/

# Optional - Transaction configuration
KURU_TRANSACTION_TIMEOUT=120  # Seconds to wait for confirmation
KURU_POLL_LATENCY=0.4  # Seconds to wait after confirmation for RPC sync

# Optional - WebSocket configuration
KURU_MAX_RECONNECT_ATTEMPTS=5  # Maximum reconnection tries
KURU_RECONNECT_DELAY=1.0  # Base delay for exponential backoff

# Optional - Order execution defaults
KURU_POST_ONLY=true  # Only place limit orders (maker-only)
KURU_AUTO_APPROVE=true  # Automatically approve tokens if needed
KURU_USE_ACCESS_LIST=true  # Use EIP-2930 for gas optimization
```

### Configuration Classes

The SDK provides 7 configuration classes:

#### 1. ConnectionConfig
Connection endpoints for RPC and API services.

```python
from src.configs import ConfigManager

connection_config = ConfigManager.load_connection_config(
    rpc_url="https://premium-rpc.example.com",  # Custom RPC endpoint
    rpc_ws_url="wss://premium-ws.example.com",  # Custom WebSocket RPC
    kuru_ws_url="wss://ws.kuru.io/",  # Kuru orderbook WebSocket
    kuru_api_url="https://api.kuru.io/",  # Kuru API
    auto_env=False,  # Don't load from environment variables
)
```

**Defaults:** Public Kuru endpoints (free but rate-limited)

#### 2. WalletConfig
Private key and derived wallet address (kept separate for security).

```python
wallet_config = ConfigManager.load_wallet_config(
    private_key=os.getenv("PRIVATE_KEY"),  # Your private key
    auto_env=True,  # Load from PRIVATE_KEY env var if not specified
)
# Automatically derives and checksums user_address from private key
```

**Security Note:** Never hardcode private keys in source code.

#### 3. MarketConfig
Market-specific configuration (contract addresses, token info, precision).

```python
market_config = ConfigManager.load_market_config(
    market_address="0x065C9d28E428A0db40191a54d33d5b7c71a9C394",
    fetch_from_chain=True,  # Fetch token decimals, symbols, precision from blockchain
    rpc_url=connection_config.rpc_url,  # Use custom RPC for fetching
)
```

**Dynamic Fetching:** Automatically retrieves base/quote token addresses, decimals, symbols, and precision from the blockchain.

#### 4. TransactionConfig
Transaction confirmation and gas optimization settings.

```python
transaction_config = ConfigManager.load_transaction_config(
    timeout=300,  # 5 minutes for slow networks (default: 120s)
    poll_latency=1.0,  # 1 second RPC sync delay (default: 0.4s)
    gas_adjustment_per_slot=7000,  # Custom gas adjustment (default: 6500)
    gas_buffer_multiplier=1.05,  # 5% safety buffer (default: 1.1 = 10%)
)
```

**Use Case:** Customize for slow networks or specific RPC providers.

#### 5. WebSocketConfig
WebSocket connection and reconnection behavior.

```python
websocket_config = ConfigManager.load_websocket_config(
    max_reconnect_attempts=10,  # More retries for unstable networks (default: 5)
    reconnect_delay=2.0,  # Base delay with exponential backoff (default: 1.0s)
    heartbeat_interval=15.0,  # More frequent pings (default: 30.0s)
    heartbeat_timeout=5.0,  # Faster timeout detection (default: 10.0s)
)
```

**Use Case:** Tune for network stability and responsiveness.

#### 6. OrderExecutionConfig
Default behavior for order placement.

```python
order_execution_config = ConfigManager.load_order_execution_config(
    post_only=False,  # Allow taker orders (default: True = maker-only)
    auto_approve=True,  # Auto approve tokens (default: True)
    use_access_list=True,  # Gas optimization (default: True)
)
```

**Per-Method Override:** You can override these in individual method calls:
```python
await client.place_orders(orders, post_only=False)  # Override for this call only
```

#### 7. CacheConfig (Advanced)
Internal cache TTL configuration for order tracking.

```python
cache_config = ConfigManager.load_cache_config(
    pending_tx_ttl=10.0,  # Longer timeout callback trigger (default: 5.0s)
    trade_events_ttl=10.0,  # Longer orphaned event cache (default: 5.0s)
    check_interval=0.5,  # More frequent cache checks (default: 1.0s)
)
```

**Use Case:** Performance tuning for high-frequency trading.

### Configuration Patterns

See `examples/config_examples.py` for comprehensive patterns including:

1. **Simple Defaults** - Minimal code for most users
2. **Custom Timeouts** - For slow networks
3. **Power User** - Full customization
4. **Presets** - Use conservative/aggressive/testnet presets
5. **One-Liner** - Convenience method to load all configs at once
6. **Environment Variables** - Different configs for dev/staging/production
7. **Per-Method Overrides** - Override config defaults per method call
8. **Testnet Configuration** - Optimized for testnet deployment

### Configuration Presets

Use pre-configured setups for common scenarios:

```python
from src.configs import ConfigPresets

# Conservative: Longer timeouts, more retries (production)
preset = ConfigPresets.conservative()
client = await KuruClient.create(
    market_config=market_config,
    connection_config=connection_config,
    wallet_config=wallet_config,
    **preset,  # Applies conservative configs
)

# Aggressive: Shorter timeouts, fewer retries (HFT)
preset = ConfigPresets.aggressive()

# Testnet: Optimized for slower testnets
preset = ConfigPresets.testnet()
```

### One-Liner Convenience

Load all configs at once:

```python
configs = ConfigManager.load_all_configs(
    market_address=os.getenv("MARKET_ADDRESS"),
    fetch_from_chain=True,
)
client = await KuruClient.create(**configs)
```

### Migration from Legacy Config

If you're upgrading from an older version that used `KuruMMConfig` or `initialize_kuru_mm_config()`, the old pattern still works but is **deprecated**:

**Old Pattern (DEPRECATED - Still works with warnings):**
```python
from src.configs import initialize_kuru_mm_config, market_config_from_market_address

kuru_config = initialize_kuru_mm_config(
    private_key=os.getenv("PRIVATE_KEY")
)
market_config = market_config_from_market_address("0x...")

# This still works but shows deprecation warning
client = await KuruClient.create(market_config, kuru_mm_config=kuru_config)
```

**New Pattern (RECOMMENDED):**
```python
from src.configs import ConfigManager

wallet_config = ConfigManager.load_wallet_config()
connection_config = ConfigManager.load_connection_config()
market_config = ConfigManager.load_market_config(
    market_address=os.getenv("MARKET_ADDRESS"),
    fetch_from_chain=True
)

client = await KuruClient.create(
    market_config=market_config,
    connection_config=connection_config,
    wallet_config=wallet_config,
)
```

**Benefits of migrating to the new system:**
- **Better Security**: Private key is separated from connection config
- **More Control**: Customize timeouts, reconnection behavior, and gas settings
- **Clear Defaults**: All defaults are centralized and documented
- **Environment Variables**: Easy deployment across dev/staging/production
- **No Breaking Changes**: Upgrade at your own pace

## Documentation

- **[Order Types Documentation](docs/ORDER_TYPES.md)** - Complete guide to order types and usage
- **[Orderbook WebSocket Documentation](docs/ORDERBOOK_WEBSOCKET.md)** - Real-time market data feed
- **[Configuration Examples](examples/config_examples.py)** - 8 comprehensive configuration patterns
- **[Order Examples](examples/order_usage.py)** - Usage examples for all order types
- **[Market Making Bot](examples/simple_market_making_bot.py)** - Complete market making bot example
- **[Orderbook WebSocket Examples](examples/orderbook_ws_usage.py)** - WebSocket feed examples

## Order Types

The SDK provides a unified `Order` class that supports:

### Limit Orders
Place orders at specific prices in the orderbook:
```python
create_limit_order(cloid, side, price, size, post_only)
```

### Market Orders
Execute immediately against the best available price:
```python
create_market_order(cloid, side, size, min_amount_out, is_margin, is_fill_or_kill)
```

### Cancel Orders
Cancel multiple orders in batch:
```python
create_cancel_order(cloid, order_ids_to_cancel)
```

### Batch Updates
Pass a list of orders to batch update the orderbook:
```python
batch_orders = [
    create_limit_order("batch-1", OrderSide.BUY, 49500, 100000, True),
    create_limit_order("batch-2", OrderSide.SELL, 51500, 120000, True),
]
# Execute via manager/executor
```

## Order Status Tracking

Orders go through the following lifecycle:
- `ORDER_CREATED` - Created locally
- `ORDER_SENT` - Transaction sent to blockchain
- `ORDER_PLACED` - Confirmed on orderbook
- `ORDER_PARTIALLY_FILLED` - Partially filled
- `ORDER_FULLY_FILLED` - Completely filled
- `ORDER_CANCELLED` - Cancelled
- `ORDER_TIMEOUT` - Timed out

## Project Structure

```
kuru-mm-py/
├── src/
│   ├── manager/
│   │   ├── order.py         # Order types and validation
│   │   └── orders_manager.py # Order management
│   ├── executor/
│   │   └── orders_executor.py # Transaction execution
│   ├── feed/
│   │   ├── rpc_ws.py        # Blockchain WebSocket feeds
│   │   └── orderbook_ws.py  # Orderbook WebSocket client
│   ├── transaction/
│   │   └── transaction.py   # Transaction sending and confirmation
│   ├── user/
│   │   └── user.py          # User account operations
│   ├── utils/
│   │   ├── validation.py    # Config validation utilities
│   │   └── utils.py         # General utilities
│   ├── abis/                # Contract ABIs
│   ├── client.py            # Main KuruClient
│   ├── configs.py           # Configuration classes and ConfigManager
│   └── config_defaults.py   # Centralized default values
├── tests/
│   ├── test_order.py        # Order type tests
│   ├── test_configs.py      # Config tests
│   └── test_orderbook_ws.py # Orderbook WebSocket tests
├── examples/
│   ├── config_examples.py   # Configuration pattern examples
│   ├── simple_market_making_bot.py # Market making bot example
│   ├── order_usage.py       # Order usage examples
│   └── orderbook_ws_usage.py # Orderbook WebSocket examples
└── docs/
    ├── ORDER_TYPES.md       # Order types documentation
    └── ORDERBOOK_WEBSOCKET.md # Orderbook WebSocket documentation
```

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_order.py -v

# Run with coverage
uv run pytest tests/ --cov=src
```

## Requirements

- Python >= 3.14
- Dependencies managed via uv (see `pyproject.toml`)

## License

[Add license information]

## Contributing

[Add contribution guidelines]

## Support

[Add support information]
