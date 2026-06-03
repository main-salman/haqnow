#!/usr/bin/env python3
"""
HaqNow Social Sync - Make.com Integration Setup Script
Finds the user's Telegram Chat ID, updates the Make.com scenario blueprint, and activates the sync.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path)

MAKE_API_KEY = os.getenv("MAKE_API_KEY")
TELEGRAM_BOT_TOKEN = "REDACTED_TELEGRAM_BOT_TOKEN"
SCENARIO_ID = 5842657
CONNECTION_ID = 7609773
YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCjnJU7dV6kbYdvseylIklig"

def print_banner():
    print("=" * 60)
    print("🤖  HAQNOW SOCIAL SYNC - MAKE.COM INTEGRATION SETUP  🤖")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Poll your Telegram bot to discover your Chat ID.")
    print("2. Programmatically update your Make.com Scenario blueprint.")
    print("3. Activate the Scenario to start automatic notifications.")
    print("\n" + "=" * 60)

def poll_telegram_chat_id():
    print("\n🔍 Step 1: Discovering your Telegram Chat ID...")
    print("------------------------------------------------------------")
    print(f"👉 Please open Telegram and go to: https://t.me/haqnow_notifier_bot")
    print("👉 Click the 'START' button or type /start in the chat.")
    print("------------------------------------------------------------")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    attempts = 0
    max_attempts = 30  # 30 attempts, 2 seconds each = 60 seconds timeout
    
    while attempts < max_attempts:
        sys.stdout.write(f"\rWaiting for you to click 'Start' (Timeout in {2 * (max_attempts - attempts)}s)...")
        sys.stdout.flush()
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get("result", [])
                for r in results:
                    message = r.get("message") or r.get("edited_message") or r.get("channel_post")
                    if message:
                        chat = message.get("chat")
                        if chat:
                            chat_id = chat.get("id")
                            first_name = chat.get("first_name", "User")
                            username = chat.get("username", "")
                            print(f"\n\n✅ Success! Found your Telegram account:")
                            print(f"   Name: {first_name}")
                            print(f"   Username: @{username}" if username else "   Username: None")
                            print(f"   Chat ID: {chat_id}")
                            return chat_id
        except Exception as e:
            pass
            
        time.sleep(2)
        attempts += 1
        
    print("\n\n❌ Discovery timed out.")
    print("Please make sure you clicked 'Start' on @haqnow_notifier_bot and try running this script again!")
    sys.exit(1)

def update_make_blueprint(chat_id):
    print("\n🔧 Step 2: Updating Make.com Scenario blueprint...")
    if not MAKE_API_KEY:
        print("❌ Error: MAKE_API_KEY is not set in your .env file.")
        print("Please check your .env file and ensure MAKE_API_KEY is present.")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Token {MAKE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"https://eu1.make.com/api/v2/scenarios/{SCENARIO_ID}"
    
    # Define our custom RSS-to-Telegram flow blueprint
    blueprint_data = {
        "name": "HaqNow Social Sync (YouTube to Telegram)",
        "flow": [
            {
                "id": 1,
                "module": "rss:TriggerNewArticle",
                "version": 4,
                "parameters": {
                    "url": YOUTUBE_RSS_URL,
                    "maxResults": 10,
                    "gzip": True,
                    "include": [],
                    "password": "",
                    "username": ""
                },
                "mapper": {},
                "metadata": {
                    "designer": {
                        "x": 0,
                        "y": 0
                    }
                }
            },
            {
                "id": 2,
                "module": "telegram:SendReplyMessage",
                "version": 1,
                "parameters": {
                    "__IMTCONN__": CONNECTION_ID
                },
                "mapper": {
                    "chatId": str(chat_id),
                    "text": "🎥 *New HaqNow Post Alert!*\n\n*Title:* {{1.title}}\n\n*Caption / Description:*\n{{1.summary}}\n\n*Link:* {{1.url}}",
                    "parseMode": "Markdown"
                },
                "metadata": {
                    "designer": {
                        "x": 300,
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
        if response.status_code == 200:
            print("✅ Success! Make.com blueprint updated with your personal Chat ID.")
            return True
        else:
            print(f"❌ Error updating blueprint: Status {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Network error while updating blueprint: {e}")
        sys.exit(1)

def activate_scenario():
    print("\n🚀 Step 3: Activating your Make.com Scenario...")
    headers = {
        "Authorization": f"Token {MAKE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"https://eu1.make.com/api/v2/scenarios/{SCENARIO_ID}/start"
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Success! Your scenario is now ACTIVE and running in the background.")
            print("🎉 Every 15 minutes, Make.com will check your feeds and notify you instantly on Telegram when new content is posted!")
            return True
        else:
            print(f"❌ Error activating scenario: Status {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Network error while activating scenario: {e}")
        sys.exit(1)

def main():
    print_banner()
    chat_id = poll_telegram_chat_id()
    update_make_blueprint(chat_id)
    activate_scenario()
    print("\n" + "=" * 60)
    print("✨ ALL SET! HaqNow Social Sync is fully operational. ✨")
    print("=" * 60)

if __name__ == "__main__":
    main()
