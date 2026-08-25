"""Print candle updates as they arrive, so you can verify the pipeline works.

Usage:
    python check_candles.py

This subscribes to the Redis Pub/Sub channel the candle builder publishes to
(CANDLE_CHANNEL, default "market_candles") and prints every candle update as
readable JSON. Run this in its own terminal alongside `run_candle_builder.py`.

You can also read historical candles from the output stream instead:
    python check_candles.py --stream
"""

from __future__ import annotations

import json
import os
import sys

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CANDLE_CHANNEL = os.getenv("CANDLE_CHANNEL", "market_candles")
CANDLE_STREAM = os.getenv("CANDLE_STREAM", "market:candles")


def watch_pubsub() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    client.ping()
    pubsub = client.pubsub()
    pubsub.subscribe(CANDLE_CHANNEL)
    print(f"Listening on Pub/Sub channel: {CANDLE_CHANNEL}  (Ctrl+C to stop)")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue
        candle = json.loads(message["data"])
        print(json.dumps(candle, indent=2))


def read_stream() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    client.ping()
    print(f"Reading candle stream: {CANDLE_STREAM}")

    entries = client.xrange(CANDLE_STREAM, min="-", max="+")
    if not entries:
        print("No candles found yet in the stream.")
        return

    for entry_id, fields in entries:
        candle = json.loads(fields["payload"])
        print(f"[{entry_id}] {json.dumps(candle, indent=2)}")


def main() -> None:
    if "--stream" in sys.argv:
        read_stream()
    else:
        watch_pubsub()


if __name__ == "__main__":
    main()
