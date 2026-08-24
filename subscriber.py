import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

pubsub = redis_client.pubsub()
pubsub.subscribe("market_data")

print("Waiting for market data...")

for message in pubsub.listen():
    if message["type"] == "message":
        print("Recived:", message["data"])