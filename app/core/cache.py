import redis.asyncio as redis
import os

# Load Redis URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create an asynchronous Redis client
redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client
