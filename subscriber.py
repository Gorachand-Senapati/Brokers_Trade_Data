import redis
import time

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

stream_name = "market:ticks"
last_id = "$"

print(f"Waiting for market data from stream: {stream_name}")

while True:
    messages = redis_client.xread(
        {stream_name: last_id},
        count=10,
        block=5000,
    )

    if not messages:
        time.sleep(1)
        continue

    for _stream, stream_messages in messages:
        for message_id, fields in stream_messages:
            last_id = message_id
            print("Received:", fields.get("payload", fields))
