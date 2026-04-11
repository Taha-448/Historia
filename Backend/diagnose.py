import os
import psycopg2
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path

def diagnose():
    print("--- Diagnostics ---")
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    db_url = os.environ.get("DATABASE_URL")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    print(f"DATABASE_URL: {db_url[:20]}..." if db_url else "DATABASE_URL: Missing")
    print(f"GEMINI_API_KEY: {gemini_key[:10]}..." if gemini_key else "GEMINI_API_KEY: Missing")
    
    # Check DB Connection
    try:
        conn = psycopg2.connect(db_url)
        print("DB Connection: SUCCESS")
        conn.close()
    except Exception as e:
        print(f"DB Connection: FAILED ({e})")
        
    # Check Gemini API
    try:
        llm = ChatGoogleGenerativeAI(temperature=0.2, model="gemini-2.5-flash", google_api_key=gemini_key)
        response = llm.invoke("Hi")
        print("Gemini API: SUCCESS")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Gemini API: FAILED ({e})")

if __name__ == "__main__":
    diagnose()
