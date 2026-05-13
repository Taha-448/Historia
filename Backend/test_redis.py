import os
import redis
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

REDIS_URL = os.getenv("REDIS_URL")
print(f"Testing connection to: {REDIS_URL}")

try:
    client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
    print("Pinging...")
    client.ping()
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
