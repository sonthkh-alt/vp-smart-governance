import os
from anthropic import Anthropic

api_key = "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
base_url = "https://api.shopaikey.com"

client = Anthropic(api_key=api_key, base_url=base_url)

models_to_test = [
    "claude-sonnet-4-6",
    "claude-sonnet-4-5",
    "claude-opus-4-6"
]

print("=== START CLAUDE 4.X TEST ===")
for model in models_to_test:
    print(f"\n[TESTING] Model: {model}")
    try:
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "Hi"}],
        )
        print(f"SUCCESS! Response from {model}: {response.content[0].text}")
    except Exception as e:
        print(f"FAILED: {e}")
