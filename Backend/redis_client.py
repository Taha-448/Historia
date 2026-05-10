import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print(f"DEBUG: Connected to Redis at {REDIS_URL.split('@')[-1]}")
except Exception as e:
    print(f"CRITICAL: Redis connection failed: {e}")
    redis_client = None

def check_rate_limit(identifier: str, limit: int = 30, window: int = 60):
    """
    Checks if a user has exceeded their message limit (default 30/min for testing).
    """
    if not redis_client:
        print("DEBUG: Redis client not available, skipping rate limit.")
        return True
        
    key = f"ratelimit:{identifier}"
    try:
        current = redis_client.get(key)
        
        if current and int(current) >= limit:
            print(f"ALERT: Rate limit HIT for {identifier}")
            return False
            
        new_val = redis_client.incr(key)
        if new_val == 1:
            redis_client.expire(key, window)
            
        print(f"DEBUG: Redis Rate Limit - {identifier}: {new_val}/{limit}")
        return True
    except Exception as e:
        print(f"ERROR: Redis rate limit check failed: {e}")
        return True

def cache_chat_history(session_id: int, history_text: str):
    if not redis_client: return
    key = f"chat_cache:{session_id}"
    print(f"DEBUG: Caching chat history in Redis for session {session_id}")
    redis_client.setex(key, 600, history_text)

def get_cached_chat_history(session_id: int):
    if not redis_client: return None
    key = f"chat_cache:{session_id}"
    data = redis_client.get(key)
    if data:
        print(f"DEBUG: Redis CACHE HIT for session {session_id}")
    else:
        print(f"DEBUG: Redis CACHE MISS for session {session_id}")
    return data
