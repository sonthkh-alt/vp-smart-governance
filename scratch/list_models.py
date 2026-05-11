import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

print("--- Available Models ---")
try:
    models = client.models.list()
    for m in models:
        print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
