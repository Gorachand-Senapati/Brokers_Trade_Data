# CoinDCX Market Data

A Python-based market data service that connects to the CoinDCX WebSocket, receives live trade data for dynamically selected symbols, normalizes the data into a common payload format, and publishes the data through Redis Pub/Sub for further processing.

## Features

* Connects to CoinDCX WebSocket.
* Supports multiple trading symbols.
* Symbols can be selected dynamically from the command line.
* Receives live trade data continuously.
* Converts CoinDCX trade data into a normalized payload.
* Converts trade timestamps to IST.
* Publishes normalized market data through Redis Pub/Sub.
* Redis runs through Docker.

## Data Flow

```text
CoinDCX WebSocket
       ↓
Live Trade Data
       ↓
Normalize Payload
       ↓
Redis Pub/Sub
       ↓
Candle Builder / Other Consumers
```

## Payload Format

The service publishes market data in the following format:

```json
{
  "symbol": "B-BTC_USDT",
  "ltt": "2026-08-24 15:30:12.108 IST",
  "ltp": 43000.25,
  "volume": 0.002,
  "provider": "CoinDCX"
}
```

### Fields

| Field      | Description            |
| ---------- | ---------------------- |
| `symbol`   | CoinDCX trading symbol |
| `ltt`      | Last trade time in IST |
| `ltp`      | Last traded price      |
| `volume`   | Trade volume           |
| `provider` | Market data provider   |

## Requirements

* Python 3.12+
* Docker
* Redis
* Internet connection

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd coindcx-market-data
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
docker run -d --name coindcx-redis -p 6379:6379 redis:latest
```

Check that Redis is running:

```bash
docker ps
```

Test Redis:

```bash
docker exec -it coindcx-redis redis-cli ping
```

Expected output:

```text
PONG
```

## Run the Application

Symbols are selected dynamically from the command line.

For one symbol:

```bash
python coindcx.py BTC
```

For multiple symbols:

```bash
python coindcx.py BTC ETH SOL
```

The application will dynamically create the corresponding CoinDCX trade channels:

```text
B-BTC_USDT@trades
B-ETH_USDT@trades
B-SOL_USDT@trades
```

Example output:

```text
Selected symbols: ['BTC', 'ETH', 'SOL']
Connected to CoinDCX
Subscribed: B-BTC_USDT@trades
Subscribed: B-ETH_USDT@trades
Subscribed: B-SOL_USDT@trades

Published: {
    'symbol': 'B-BTC_USDT',
    'ltt': '2026-08-24 15:30:12.108 IST',
    'ltp': 43000.25,
    'volume': 0.002,
    'provider': 'CoinDCX'
}
```

## Redis Subscriber

A test subscriber is included to verify that market data is successfully published to Redis.

Run:

```bash
python subscriber.py
```

The subscriber listens to the Redis channel:

```text
market_data
```

Example:

```text
Waiting for market data...

Received: {"symbol":"B-BTC_USDT","ltt":"2026-08-24 15:30:12.108 IST","ltp":43000.25,"volume":0.002,"provider":"CoinDCX"}
```

## Project Structure

```text
coindcx-market-data/
│
├── coindcx.py
├── redis_client.py
├── subscriber.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Files

* `coindcx.py` — Connects to CoinDCX, receives trade data, creates the normalized payload, and publishes it to Redis.
* `redis_client.py` — Creates the Redis connection.
* `subscriber.py` — Test subscriber that receives data from Redis.
* `requirements.txt` — Python dependencies.
* `.gitignore` — Files and folders excluded from Git.
* `README.md` — Project documentation.

## Redis Channel

Market data is published to:

```text
market_data
```

Consumers can subscribe to this channel to process the live trade stream.

## Dependencies

```text
python-socketio[client]
redis
python-dotenv
tzdata
```

## Next Step

The published market data can be consumed by downstream services such as a configurable candle builder for generating different candle timeframes.

## Author

Gorachand Senapati
