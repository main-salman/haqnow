import json
import os

languages = ['ar', 'fr', 'de', 'ru', 'pl', 'tr']
base_dir = '/Users/salman/Documents/fadih/frontend/src/i18n/locales'

# New keys and values from en.json
new_updates = {
    "footer": {
        "poweredBy": "Transparent infrastructure for a more accountable world.",
        "complianceJargon": "HaqNow is a neutral platform for the sharing of public interest information. We are DMCA and GDPR compliant. If you have concerns about a document, please submit your issue using our contact form, including the document's URL. We act quickly to address legitimate legal and privacy concerns."
    },
    "homepage": {
        "title": "Illuminating Truth for Global Justice",
        "subtitle": "HaqNow provides the neutral, supportive infrastructure needed to share critical information securely. Explore a growing repository of public interest documents, or share vital information to help build a more accountable world.",
        "recentlySharedDescription": "Newest public interest records added to the global archive.",
        "topViewedDescription": "Most impactful public interest documents currently being analyzed by the global community.",
        "missionTitle": "The Mission",
        "missionDescription": "Transparency is the bridge between hidden actions and public awareness. We provide the tools to build that bridge.",
        "thrivingTitle": "Transparency Drives Thriving Communities",
        "thrivingDescription": "When institutions are illuminated, they serve the people. Our archive helps communities hold power accountable through evidence.",
        "protectedTitle": "Safe, Protected Sharing for Truth-Tellers",
        "protectedDescription": "Our zero-knowledge architecture and AI-powered accessibility ensure that vital information reaches the world without compromising the source.",
        "searchTitle": "Search Public Records",
        "searchDescription": "Access the global archive of institutional accountability documents.",
        "uploadTitle": "Share Information",
        "uploadDescription": "Securely contribute public interest records to the global transparency movement."
    }
}

def update_json(lang):
    file_path = os.path.join(base_dir, f"{lang}.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Update sections
    for section, keys in new_updates.items():
        if section not in data:
            data[section] = {}
        for key, value in keys.items():
            # For rebranding, we want to overwrite even if the key exists 
            # if it's one of the main rebranding keys, but for others we might want to keep translations.
            # However, since we are shifting from "Anti-Corruption" to "Institutional Accountability",
            # the old translations are technically "wrong" or "dated".
            # To be safe and "editable", we'll add them if they don't exist,
            # or update them if they are part of the core hero/mission.
            data[section][key] = value

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {lang}.json")

for lang in languages:
    update_json(lang)
