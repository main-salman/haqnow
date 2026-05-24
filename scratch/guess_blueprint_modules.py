import requests
import json

api_key = "REDACTED_MAKE_API_KEY"
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json"
}

scenario_id = 5842657
url = f"https://eu1.make.com/api/v2/scenarios/{scenario_id}"

# We will try multiple common RSS module names
rss_module_guesses = [
    "rss:watch-feed-items",
    "rss:WatchFeedItems",
    "rss:watch-rss-feed-items",
    "rss:watch"
]

for guess in rss_module_guesses:
    print(f"\nTrying RSS module: {guess}...")
    blueprint_data = {
        "name": "HaqNow Social Sync (YouTube to Telegram)",
        "flow": [
            {
                "id": 1,
                "module": guess,
                "version": 1,
                "parameters": {},
                "mapper": {},
                "metadata": {
                    "designer": {
                        "x": 0,
                        "y": 0
                    }
                }
            }
        ],
        "metadata": {
            "instant": False,
            "version": 1,
            "scenario": {
                "roundtrips": 1
            }
        }
    }
    
    body = {
        "blueprint": json.dumps(blueprint_data)
    }
    
    try:
        response = requests.patch(url, headers=headers, json=body, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(response.text)
        if "Module not found" not in response.text:
            print(f"SUCCESS! Valid RSS module found: {guess}")
            break
    except Exception as e:
        print(f"Error: {e}")
