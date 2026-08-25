import json

from redis_client import redis_client


STREAM_NAME = "market:ticks"


def publish_tick(tick):

    payload = {
        "symbol": tick.symbol,
        "ltt": tick.ltt,
        "ltp": tick.ltp,
        "volume": tick.volume,
        "provider": tick.provider
    }

    redis_client.xadd(
        STREAM_NAME,
        {
            "payload": json.dumps(payload)
        }
    )

    print("Published:", payload)

