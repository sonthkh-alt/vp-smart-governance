import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
print(f"Testing Key with Gemini 2.5 Flash...")

client = genai.Client(api_key=key)
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'API Key is working!'"
    )
    print("--- RESULT ---")
    print(f"Status: SUCCESS")
    print(f"AI Response: {response.text}")
except Exception as e:
    print(f"--- RESULT ---")
    print(f"Status: FAILED")
    print(f"Error: {e}")
