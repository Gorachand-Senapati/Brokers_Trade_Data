# Multi-Broker Redis Candle Builder

This project reads normalized trade ticks from Redis and creates candles for
different timeframes, such as 1 minute and 5 minutes. It supports multiple
brokers (for example CoinDCX, Binance, Bybit) at the same time, keeping each
broker's candles separate even when the same canonical symbol (like
`BTC/USDT`) is traded on more than one broker.

## How it works

```text
Broker feeds (CoinDCX, Binance, Bybit, ...)
        ↓ normalized ticks
Redis Stream(s): market:ticks[:<provider>]
        ↓
Candle Builder
        ↓
Redis Stream: market:candles
Redis Pub/Sub: market_candles
```

The candle builder calculates, per `(provider, broker_id, symbol, timeframe)`:

- **Open**: first price in the timeframe
- **High**: highest price in the timeframe
- **Low**: lowest price in the timeframe
- **Close**: latest price in the timeframe
- **Volume**: total traded quantity in the timeframe

Because candles are keyed by provider and broker, a `BTC/USDT` candle from
Binance is never mixed with a `BTC/USDT` candle from CoinDCX.

## Project files

| File | Purpose |
| --- | --- |
| `candle_builder/candle_builder.py` | Calculates candle values (Redis-independent). |
| `candle_builder/redis_candle_builder.py` | Reads ticks from Redis and publishes candles. |
| `run_candle_builder.py` | Entry point to start the service. |
| `tests/test_candle_builder.py` | Tests the candle calculations. |
| `requirements.txt` | Lists the required Python package. |

## Input data

Each broker feed writes normalized trade ticks to a Redis Stream. By
default all brokers can share one stream (`market:ticks`), or each broker
can use its own stream (for example `market:ticks:coindcx`,
`market:ticks:binance`) -- see [Redis settings](#redis-settings).

Example tick:

```json
{
  "provider": "coindcx",
  "broker_id": "coindcx-spot",
  "symbol": "BTC/USDT",
  "ltt": "2026-08-24 17:29:03.123 IST",
  "ltp": 43000.25,
  "volume": 0.002
}
```

| Field | Meaning |
| --- | --- |
| `provider` | Broker or market-data provider name (for example `coindcx`, `binance`, `bybit`). |
| `broker_id` | Optional. Identifies a specific feed configuration when one provider runs more than one (for example `binance-spot` vs `binance-futures`). Defaults to `provider` if omitted. |
| `symbol` | Canonical trading pair (for example `BTC/USDT`). |
| `ltt` | Trade time. Epoch milliseconds, a digit string, or an IST timestamp string (optionally suffixed with ` IST`) are all supported. |
| `ltp` | Latest traded price. |
| `volume` | Quantity traded in this update. |

## Output data

The candle builder writes candle updates to the Redis Stream `market:candles`
and also publishes the same JSON to the Redis Pub/Sub channel `market_candles`.

Example candle:

```json
{
  "provider": "coindcx",
  "broker_id": "coindcx-spot",
  "symbol": "BTC/USDT",
  "timeframe_seconds": 60,
  "start_time": "2026-08-24 17:30:00.000 IST",
  "open": 43000.0,
  "high": 43020.5,
  "low": 42980.25,
  "close": 43000.25,
  "volume": 1.245,
  "is_closed": true
}
```

`is_closed` is `true` when the timeframe has finished. The current candle can
be published multiple times while new trade updates arrive.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv redis_env
.\redis_env\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

Make sure Redis is running locally, or set a different Redis URL:

```powershell
$env:REDIS_URL = "redis://localhost:6379/0"
```

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

## Run the candle builder

The default timeframes are 60 seconds and 300 seconds, reading from the
single stream `market:ticks`:

```powershell
python run_candle_builder.py
```

To use different timeframes, set them in seconds before starting the program:

```powershell
$env:TIMEFRAMES_SECONDS = "60,300,900"
python run_candle_builder.py
```

This creates 1-minute, 5-minute, and 15-minute candles.

To consume multiple broker streams at once (for example CoinDCX and
Binance feeds published to separate streams):

```powershell
$env:TICK_STREAMS = "market:ticks:coindcx,market:ticks:binance"
python run_candle_builder.py
```

## Redis settings

The following settings can be changed through environment variables:

| Variable | Default value | Purpose |
| --- | --- | --- |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL. |
| `TICK_STREAMS` | value of `TICK_STREAM`, or `market:ticks` | Comma-separated list of input streams for trade ticks, one per broker feed (or one shared stream). |
| `TICK_STREAM` | `market:ticks` | Deprecated single-stream alias, kept for backward compatibility. Use `TICK_STREAMS` for new setups. |
| `CANDLE_STREAM` | `market:candles` | Output stream for candles. |
| `CANDLE_CHANNEL` | `market_candles` | Output Pub/Sub channel for candles. |
| `TIMEFRAMES_SECONDS` | `60,300` | Candle timeframes in seconds. |
| `CONSUMER_GROUP` | `candle-builders` | Redis consumer group name. |
| `CONSUMER_NAME` | Computer name | Redis consumer name. |
