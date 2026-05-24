import requests
import json

api_key = "REDACTED_MAKE_API_KEY"
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json"
}

endpoints = [
    "https://eu1.make.com/api/v2/templates/11432",
    "https://eu1.make.com/api/v2/templates/public/11432"
]

for url in endpoints:
    print(f"\nQuerying: {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS!")
            data = response.json()
            print(json.dumps(data, indent=2)[:2000])
        else:
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")
