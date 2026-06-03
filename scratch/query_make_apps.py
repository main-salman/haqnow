import requests
import json

api_key = "REDACTED_MAKE_API_KEY"
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json"
}

# We will query details for 'rss' and 'telegram-bot' apps
apps = ["rss", "telegram-bot"]

for app in apps:
    url = f"https://eu1.make.com/api/v2/apps/{app}"
    print(f"\nQuerying App: {app}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Print modules inside the app
            print("Modules:")
            for module in data.get("modules", []):
                print(f" - {module.get('name')}: {module.get('label')}")
        else:
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")
