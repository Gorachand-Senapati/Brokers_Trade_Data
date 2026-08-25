
````markdown
# Multi-Broker Market Data

A Python-based market data service that connects to multiple broker WebSocket feeds, receives live trade data for dynamically configured symbols, normalizes the data into a common payload format, and writes the selected market data to a Redis Stream for further processing.

## Features

* Supports multiple market-data brokers.

* Currently supports CoinDCX and Binance.

* Multiple brokers can run simultaneously.

* Supports multiple trading symbols.

* Brokers and symbols can be configured through `config.yaml`.

* Receives live trade data continuously.

* Converts broker-specific trade data into a common `MarketTick` format.

* Converts trade timestamps to IST.

* Tracks broker connection status.

* Supports configurable broker priority.

* Writes normalized market data to a Redis Stream.

* Redis runs through Docker.

* Designed for downstream consumers such as a candle builder.

## Data Flow

```text
config.yaml
      ↓
   main.py
      ↓
 Feed Manager
      ↓
 Broker Factory
      ↓
 ┌──────────────┬──────────────┐
 ↓              ↓
CoinDCX       Binance
WebSocket     WebSocket
 ↓              ↓
 └───────┬──────┘
         ↓
    MarketTick
         ↓
 Priority Selection
         ↓
 Redis Stream: market:ticks
         ↓
Candle Builder / Other Consumers
````

## Configuration

Broker and symbol selection is controlled through `config.yaml`.

Example:

```yaml
brokers:
  - coindcx
  - binance

symbols:
  - BTC
  - ETH
  - SOL

priority:
  - binance
  - coindcx
```

### Brokers

The `brokers` list determines which broker WebSocket feeds are started.

```yaml
brokers:
  - coindcx
  - binance
```

Both brokers will run simultaneously.

### Symbols

The `symbols` list determines which markets are subscribed to.

```yaml
symbols:
  - BTC
  - ETH
  - SOL
```

### Priority

The `priority` list determines the preferred broker when the same market is available from multiple brokers.

```yaml
priority:
  - binance
  - coindcx
```

In this example, Binance has higher priority than CoinDCX.

If both providers are available for the same market:

```text
Binance  → Priority 1 → Preferred
CoinDCX  → Priority 2 → Fallback
```

## Payload Format

All broker data is normalized into a common format:

```json
{
  "symbol": "BTCUSDT",
  "ltt": "2026-08-25 15:30:12.108 IST",
  "ltp": 43000.25,
  "volume": 0.002,
  "provider": "Binance"
}
```

### Fields

| Field      | Description                           |
| ---------- | ------------------------------------- |
| `symbol`   | Trading symbol provided by the broker |
| `ltt`      | Last trade time in IST                |
| `ltp`      | Last traded price                     |
| `volume`   | Trade volume                          |
| `provider` | Market data provider                  |

## Requirements

* Python 3.12+

* Docker

* Redis

* Internet connection

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Redis Setup

Start Redis using Docker:

```bash
docker run -d --name market-data-redis -p 6379:6379 redis:latest
```

Check that Redis is running:

```bash
docker ps
```

Test Redis:

```bash
docker exec -it market-data-redis redis-cli ping
```

Expected output:

```text
PONG
```

## Run the Application

The application is started through `main.py`.

The brokers and symbols are selected from `config.yaml`.

Example configuration:

```yaml
brokers:
  - coindcx
  - binance

symbols:
  - BTC
  - ETH
  - SOL

priority:
  - binance
  - coindcx
```

Run:

```bash
python main.py
```

Example output:

```text
Loaded config: {
    'brokers': ['coindcx', 'binance'],
    'symbols': ['BTC', 'ETH', 'SOL'],
    'priority': ['binance', 'coindcx']
}

Started broker: coindcx
Started broker: binance

Connected to CoinDCX
coindcx is ACTIVE

Connected to Binance
binance is ACTIVE
```

Both broker WebSocket connections run simultaneously.

## Redis Subscriber

A test subscriber is included to verify that market data is successfully written to Redis.

Run:

```bash
python subscriber.py
```

The subscriber reads from the Redis Stream:

```text
market:ticks
```

Example:

```text
Waiting for market data from stream: market:ticks

Received: {
    "symbol": "BTCUSDT",
    "ltt": "2026-08-25 15:30:12.108 IST",
    "ltp": 43000.25,
    "volume": 0.002,
    "provider": "Binance"
}
```

## Project Structure

```text
multi-broker-market-data/

│
├── main.py
├── config.yaml
├── redis_client.py
├── subscriber.py
├── requirements.txt
├── .gitignore
└── README.md
│
├── brokers/
│   ├── __init__.py
│   ├── base.py
│   ├── coindcx.py
│   └── binance.py
│
└── core/
    ├── __init__.py
    ├── schemas.py
    ├── config_loader.py
    ├── broker_factory.py
    ├── feed_manager.py
    ├── redis_publisher.py
    └── priority_manager.py
```

## Files

* `main.py` — Application entry point that loads the configuration and starts the feed manager.

* `config.yaml` — Contains the configured brokers, symbols, and broker priority.

* `brokers/base.py` — Defines the common interface for broker adapters.

* `brokers/coindcx.py` — Connects to CoinDCX WebSocket and converts trade data into the common `MarketTick` format.

* `brokers/binance.py` — Connects to Binance WebSocket and converts trade data into the common `MarketTick` format.

* `core/schemas.py` — Defines the common `MarketTick` data structure.

* `core/config_loader.py` — Loads configuration from `config.yaml`.

* `core/broker_factory.py` — Creates the required broker adapter based on the configured broker name.

* `core/feed_manager.py` — Starts and manages multiple broker feeds simultaneously.

* `core/redis_publisher.py` — Publishes normalized market ticks to the Redis Stream.

* `redis_client.py` — Creates the Redis connection.

* `subscriber.py` — Test subscriber that receives data from the Redis Stream.

* `requirements.txt` — Python dependencies.

* `.gitignore` — Files and folders excluded from Git.

* `README.md` — Project documentation.

## Redis Stream

Market data is published to:

```text
market:ticks
```

The Redis Stream provides a common data interface for downstream consumers.

```text
Broker Feeds
     ↓
MarketTick
     ↓
Priority Selection
     ↓
market:ticks
     ↓
Candle Builder / Other Consumers
```

## Dependencies

```text
python-socketio[client]
websocket-client
redis
python-dotenv
tzdata
PyYAML
```

## Adding a New Broker

The project uses a common broker architecture so additional brokers can be added without changing the common payload format.

A new broker should:

1. Implement the `BaseBroker` interface.
2. Connect to the broker WebSocket.
3. Subscribe to configured symbols.
4. Receive live trade data.
5. Convert the raw data into `MarketTick`.
6. Emit the tick through the broker callback.
7. Report connection status.
8. Be registered in `core/broker_factory.py`.

After adding a broker, it can be enabled through `config.yaml`.

Example:

```yaml
brokers:
  - coindcx
  - binance
  - new_broker
```

## Next Step

The normalized market data from Redis can be consumed by downstream services such as a configurable candle builder for generating different candle timeframes, such as 1-minute and 5-minute candles.

## Author

Gorachand Senapati
