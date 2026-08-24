import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

print("Redis connected:", redis_client.ping())

redis_client.set("test", "hello from python")

value = redis_client.get("test")

print("Redis value:", value)