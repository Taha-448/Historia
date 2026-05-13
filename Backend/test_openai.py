import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")
print(f"Testing OpenAI with key: {api_key[:10]}...")

try:
    llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini", openai_api_key=api_key)
    print("Invoking...")
    response = llm.invoke("Hello")
    print(f"Success! Response: {response.content}")
except Exception as e:
    print(f"Failed: {e}")
