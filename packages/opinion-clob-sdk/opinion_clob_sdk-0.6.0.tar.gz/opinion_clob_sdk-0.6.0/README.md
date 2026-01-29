# Opinion CLOB SDK (Tech Preview)

**Technology Preview Release - BNB Chain Support**

Python SDK for interacting with Opinion prediction markets via the CLOB (Central Limit Order Book) API.

**Latest Version: 0.6.0**

## Overview

The Opinion CLOB SDK provides a Python interface for:

- Querying prediction market data
- Placing and managing orders
- Tracking positions and balances
- Interacting with smart contracts (split, merge, redeem)

Supports BNB Chain mainnet (chain ID 56).

## Installation

```bash
pip install opinion_clob_sdk
```

## Quick Start

```python
from opinion_clob_sdk import Client

# Initialize client
client = Client(
    host='https://proxy.opinion.trade:8443',
    apikey='your_api_key',
    chain_id=56,  # BNB Chain mainnet
    rpc_url='your_rpc_url',
    private_key='your_private_key',
    multi_sig_addr='your_multi_sig_address'
)

# Get markets
markets = client.get_markets(page=1, limit=10)

# Get market detail
market = client.get_market(market_id=123)

# Get orderbook
orderbook = client.get_orderbook(token_id='token_123')

# Get latest price
price = client.get_latest_price(token_id='token_123')
```

## Core Features

### Market Data

```python
# Get all markets with filters
from opinion_clob_sdk.model import TopicType, TopicStatusFilter

markets = client.get_markets(
    topic_type=TopicType.BINARY,
    status=TopicStatusFilter.ACTIVATED,
    page=1,
    limit=20
)

# Get specific market
market = client.get_market(market_id=123)

# Get categorical market
categorical = client.get_categorical_market(market_id=456)

# Get supported currencies
currencies = client.get_currencies()
```

### Token Data

```python
# Get orderbook
orderbook = client.get_orderbook(token_id='token_123')

# Get latest price
price = client.get_latest_price(token_id='token_123')

# Get price history
history = client.get_price_history(
    token_id='token_123',
    interval='1hour',
    bars=24
)

# Get fee rates
fees = client.get_fee_rates(token_id='token_123')
```

### Trading

```python
from opinion_clob_sdk.chain.py_order_utils.model.order import PlaceOrderDataInput
from opinion_clob_sdk.chain.py_order_utils.model.sides import OrderSide
from opinion_clob_sdk.chain.py_order_utils.model.order_type import LIMIT_ORDER, MARKET_ORDER

# Place a limit order
order_data = PlaceOrderDataInput(
    marketId=123,
    tokenId='token_yes',
    side=OrderSide.BUY,
    orderType=LIMIT_ORDER,
    price='0.5',
    makerAmountInQuoteToken=10  # 10 USDC
)
result = client.place_order(order_data)

# Place a market order
market_order = PlaceOrderDataInput(
    marketId=123,
    tokenId='token_yes',
    side=OrderSide.SELL,
    orderType=MARKET_ORDER,
    price='0',  # Market orders don't need price
    makerAmountInBaseToken=5  # 5 YES tokens
)
result = client.place_order(market_order)

# Cancel an order
client.cancel_order(trans_no='order_trans_no')

# Get my orders
my_orders = client.get_my_orders(market_id=123, limit=10)

# Get order by ID
order = client.get_order_by_id(order_id='order_123')
```

### User Data

```python
# Get balances
balances = client.get_my_balances()

# Get positions
positions = client.get_my_positions(page=1, pageSize=10)

# Get trade history
trades = client.get_my_trades(market_id=123, limit=20)

# Get user auth info
auth = client.get_user_auth()
```

### Smart Contract Operations

```python
# Enable trading (approve tokens)
client.enable_trading()

# Split collateral into outcome tokens
tx_hash = client.split(market_id=123, amount=1000000)  # amount in wei

# Merge outcome tokens back to collateral
tx_hash = client.merge(market_id=123, amount=1000000)

# Redeem winning positions
tx_hash = client.redeem(market_id=123)
```

### WebSocket (Real-time Updates)

#### Basic Usage

```python
# Create WebSocket client using the REST client
ws = client.create_websocket_client(
    on_open=lambda: print("Connected"),
    on_close=lambda: print("Disconnected"),
    on_error=lambda err: print(f"Error: {err}"),
    heartbeat_interval=30
)

# Connect and run in background thread (non-blocking)
ws.connect()
ws.start()

# Keep running to receive messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.close()
```

#### Subscribing to Market Data (Recommended)

The SDK provides convenient subscription methods that automatically parse messages into typed objects:

```python
from opinion_clob_sdk import Client, MarketDepthDiffMessage

client = Client(...)
ws = client.create_websocket_client()

ws.connect()
ws.start()
time.sleep(2)  # Wait for connection

# Subscribe to market depth updates
def handle_depth_update(msg: MarketDepthDiffMessage):
    print(f"Market {msg.market_id}: {msg.side} {msg.price} @ {msg.size}")

ws.subscribe_market_depth_diff(market_id=1274, callback=handle_depth_update)

# Keep running to receive messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.unsubscribe_market_depth_diff(market_id=1274)
    ws.close()
```

You can also subscribe to market last price updates:

```python
from opinion_clob_sdk import Client, MarketLastPriceMessage

client = Client(...)
ws = client.create_websocket_client()

ws.connect()
ws.start()
time.sleep(2)  # Wait for connection

# Subscribe to last price updates for binary market
def handle_last_price(msg: MarketLastPriceMessage):
    print(f"Market {msg.market_id}: Last price {msg.price} for token {msg.token_id}")

ws.subscribe_market_last_price(market_id=1274, callback=handle_last_price)

# Or for categorical market
# ws.subscribe_market_last_price(root_market_id=61, callback=handle_last_price)

# Keep running to receive messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.unsubscribe_market_last_price(market_id=1274)  # or root_market_id=61
    ws.close()
```

#### Available Subscription Methods

- `subscribe_market_depth_diff(market_id, callback)` - Subscribe to market depth updates
- `unsubscribe_market_depth_diff(market_id)` - Unsubscribe from market depth updates
- `subscribe_market_last_price(market_id, callback)` - Subscribe to last price updates for binary markets
- `subscribe_market_last_price(root_market_id, callback)` - Subscribe to last price updates for categorical markets
- `unsubscribe_market_last_price(market_id)` - Unsubscribe from last price updates for binary markets
- `unsubscribe_market_last_price(root_market_id)` - Unsubscribe from last price updates for categorical markets
- `subscribe_market_last_trade(market_id, callback)` - Subscribe to last trade updates for binary markets
- `subscribe_market_last_trade(root_market_id, callback)` - Subscribe to last trade updates for categorical markets
- `unsubscribe_market_last_trade(market_id)` - Unsubscribe from last trade updates for binary markets
- `unsubscribe_market_last_trade(root_market_id)` - Unsubscribe from last trade updates for categorical markets
- `subscribe_trade_order_update(market_id, callback)` - Subscribe to trade order updates for binary markets
- `subscribe_trade_order_update(root_market_id, callback)` - Subscribe to trade order updates for categorical markets
- `unsubscribe_trade_order_update(market_id)` - Unsubscribe from trade order updates for binary markets
- `unsubscribe_trade_order_update(root_market_id)` - Unsubscribe from trade order updates for categorical markets
- `subscribe_trade_record_new(market_id, callback)` - Subscribe to new trade records for binary markets
- `subscribe_trade_record_new(root_market_id, callback)` - Subscribe to new trade records for categorical markets
- `unsubscribe_trade_record_new(market_id)` - Unsubscribe from new trade records for binary markets
- `unsubscribe_trade_record_new(root_market_id)` - Unsubscribe from new trade records for categorical markets

#### Message Models

The SDK provides typed message models:
- `MarketDepthDiffMessage` - Market depth update messages with fields: market_id, token_id, outcome_side, side, price, size, etc.
- `MarketLastPriceMessage` - Market last price update messages with fields: market_id, root_market_id (optional), token_id, price, outcome_side, etc.
- `MarketLastTradeMessage` - Market last trade update messages with fields: market_id, root_market_id (optional), token_id, side, outcome_side, price, shares, amount, etc.
- `TradeOrderUpdateMessage` - Trade order update messages with fields: order_update_type, market_id, root_market_id (optional), order_id, side, outcome_side, price, shares, amount, status, trading_method, quote_token, created_at, expires_at, chain_id, filled_shares, filled_amount, etc.
- `TradeRecordNewMessage` - New trade record messages with fields: order_id, trade_no, market_id, root_market_id (optional), tx_hash, side, outcome_side, price, shares, amount, profit, status, quote_token, quote_token_usd_price, usd_amount, fee, chain_id, created_at, etc.

#### Manual Subscription (Advanced)

You can also send custom subscription messages manually. When using manual subscription, you can pass an `on_message` callback to the WebSocket client to receive all messages:

```python
# Create WebSocket client with on_message callback
def handle_message(msg):
    print(f"Received: {msg}")
    # Process the raw message dict here

ws = client.create_websocket_client(
    on_message=handle_message,
    on_open=lambda: print("Connected"),
    on_close=lambda: print("Disconnected")
)

ws.connect()
ws.start()
time.sleep(2)  # Wait for connection

# Send subscription message manually
ws.send({
    "action": "SUBSCRIBE",
    "channel": "market.depth.diff",
    "marketId": 1274
})

# Keep running to receive messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.close()
```

## Configuration

### Environment Variables

Create a `.env` file:

```
API_KEY=your_api_key
RPC_URL=your_rpc_url
PRIVATE_KEY=your_private_key
MULTI_SIG_ADDRESS=your_multi_sig_address
```

### Chain IDs

- **BNB Chain Mainnet**: 56

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run unit tests
pytest -v -m "not integration"

# Run all tests (including integration)
pytest -v

# Run with coverage
pytest --cov=opinion_clob_sdk --cov-report=html
```

### Project Structure

```
opinion_clob_sdk/
├── __init__.py           # Package exports
├── sdk.py                # Main Client class
├── model.py              # Enums and types
├── config.py             # Configuration constants
├── chain/                # Blockchain interactions
│   ├── contract_caller.py
│   ├── py_order_utils/   # Order building and signing
│   └── safe/             # Gnosis Safe integration
└── tests/                # Test suite
    ├── test_sdk.py
    ├── test_model.py
    ├── test_order_calculations.py
    └── test_integration.py
```

## API Reference

See the [full API documentation](https://docs.opinion.trade) for detailed information.

## Support

- Documentation: https://docs.opinion.trade
- Email: support@opinion.trade
- GitHub Issues: https://github.com/opinionlabs/openapi/issues

## License

MIT License - see LICENSE file for details
