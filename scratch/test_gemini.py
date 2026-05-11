
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GEMINI_API_KEY found in .env")
        return

    client = genai.Client(api_key=api_key)
    print(f"Testing with API Key: {api_key[:5]}...{api_key[-5:]}")
    
    models_to_test = ["gemini-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash"]
    
    for model_id in models_to_test:
        print(f"\nTesting model: {model_id}")
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents="Hi",
            )
            print(f"✅ Success! Response: {resp.text[:50]}...")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_connection()
