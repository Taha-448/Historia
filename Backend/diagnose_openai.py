import os
import psycopg2
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pathlib import Path

def diagnose_openai():
    print("--- OpenAI Diagnostics ---")
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    db_url = os.environ.get("DATABASE_URL")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    print(f"DATABASE_URL: {db_url[:20]}..." if db_url else "DATABASE_URL: Missing")
    print(f"OPENAI_API_KEY: {openai_key[:10]}..." if openai_key else "OPENAI_API_KEY: Missing")
    
    # Check DB Connection
    try:
        conn = psycopg2.connect(db_url)
        print("DB Connection: SUCCESS")
        conn.close()
    except Exception as e:
        print(f"DB Connection: FAILED ({e})")
        
    # Check OpenAI API
    try:
        llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini", api_key=openai_key)
        response = llm.invoke("Hi")
        print("OpenAI API: SUCCESS")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"OpenAI API: FAILED ({e})")

if __name__ == "__main__":
    diagnose_openai()
