"""Print a small sample of the latest raw ticks from market:ticks.

Usage:
    python sample_ticks.py [count]

This is a read-only, one-shot peek at Gorachand's tick output -- it does not
block or stream forever, so it won't flood the terminal like running his
main.py directly. Default sample size is 5.
"""

from __future__ import annotations

import json
import os
import sys

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TICK_STREAM = os.getenv("TICK_STREAM", "market:ticks")


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    client.ping()

    entries = client.xrevrange(TICK_STREAM, count=count)
    if not entries:
        print(f"No ticks found yet in stream: {TICK_STREAM}")
        return

    print(f"Latest {len(entries)} ticks from {TICK_STREAM}:\n")
    for entry_id, fields in reversed(entries):
        tick = json.loads(fields["payload"])
        print(f"[{entry_id}] {json.dumps(tick)}")


if __name__ == "__main__":
    main()
