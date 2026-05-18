import os
from openai import OpenAI

api_key = "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
base_url = "https://api.shopaikey.com/v1"

client = OpenAI(api_key=api_key, base_url=base_url)

models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

print("=== START OPENAI TEST ===")
for model in models:
    print(f"\n[TESTING] Model: {model}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=50
        )
        print(f"SUCCESS! Response from {model}: {response.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")
