import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Testing connection to: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
    print("Connecting...")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
