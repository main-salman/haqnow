import requests
import json

api_key = "REDACTED_MAKE_API_KEY"
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json"
}

# Fetch public templates (we can paginate or search if supported, otherwise fetch first page and filter)
url = "https://eu1.make.com/api/v2/templates/public?limit=100"

print("Searching public templates...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        templates = data.get("templatesPublic", [])
        print(f"Found {len(templates)} templates on page 1.")
        
        # Filter for RSS and Telegram
        matching = []
        for t in templates:
            apps = t.get("usedApps", [])
            # check if both 'rss' and 'telegram-bot' are in apps
            if "rss" in apps and ("telegram-bot" in apps or "telegram" in apps):
                matching.append(t)
            # check individually just in case
            elif "rss" in apps or "telegram-bot" in apps:
                pass
                
        print("\nMatching Templates (both RSS and Telegram):")
        for m in matching:
            print(f" - ID: {m.get('id')} | Name: {m.get('name')} | Apps: {m.get('usedApps')}")
            
        # Let's list some templates with 'rss' to see what app name they use
        print("\nTemplates with RSS:")
        for t in templates:
            if "rss" in t.get("usedApps", []):
                print(f" - ID: {t.get('id')} | Name: {t.get('name')} | Apps: {t.get('usedApps')}")
                
        # Let's list some templates with 'telegram-bot' to see what app name they use
        print("\nTemplates with Telegram Bot:")
        for t in templates:
            if "telegram-bot" in t.get("usedApps", []) or "telegram" in t.get("usedApps", []):
                print(f" - ID: {t.get('id')} | Name: {t.get('name')} | Apps: {t.get('usedApps')}")
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
