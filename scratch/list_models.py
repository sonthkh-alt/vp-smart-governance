import requests
import json

api_key = "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
url = "https://api.shopaikey.com/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}"
}

print("=== QUERYING AVAILABLE MODELS ===")
try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        models = [m["id"] for m in data.get("data", [])]
        print(f"Success! Found {len(models)} models:")
        for m in sorted(models):
            print(f" - {m}")
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
