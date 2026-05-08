import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
# Default to localhost if REDIS_URL isn't in .env
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    print("Connected to Redis successfully")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None
