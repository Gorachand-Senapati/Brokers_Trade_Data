"""Send a few sample ticks to Redis so you can watch the candle builder work.

Usage:
    python send_test_ticks.py

This writes ticks to the same stream the candle builder reads from
(TICK_STREAM / TICK_STREAMS, default "market:ticks"). Run this in one
terminal while `python run_candle_builder.py` runs in another, and watch
the candle builder's terminal print candle updates (add a print in
process_message, or read the output stream/Pub/Sub channel separately --
see check_candles.py).
"""

from __future__ import annotations

import json
import os
import time

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TICK_STREAM = os.getenv("TICK_STREAM", "market:ticks")


def make_tick(symbol: str, ltp: float, volume: float, provider: str = "coindcx") -> dict:
    return {
        "symbol": symbol,
        "ltt": int(time.time() * 1000),
        "ltp": ltp,
        "volume": volume,
        "provider": provider,
    }


def main() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=False)
    client.ping()
    print(f"Connected to Redis at {REDIS_URL}")
    print(f"Sending ticks to stream: {TICK_STREAM}")

    prices = [43000.0, 43010.5, 42995.0, 43020.0, 43005.5]

    for i, price in enumerate(prices):
        tick = make_tick("BTC/USDT", price, volume=0.01 * (i + 1))
        client.xadd(TICK_STREAM, {"payload": json.dumps(tick)})
        print(f"Sent tick #{i + 1}: {tick}")
        time.sleep(2)

    print("Done. Check the candle builder output or run check_candles.py.")


if __name__ == "__main__":
    main()
