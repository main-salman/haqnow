#!/usr/bin/env python3
"""
Script to populate moderation policy translations to the database via API.
Similar to api_populate_disclaimer.py but for moderation policies.
"""

import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://www.haqnow.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "salman.naqvi@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def login_admin():
    """Login as admin and get JWT token with 2FA support."""
    login_url = f"{BASE_URL}/api/auth/login"
    
    try:
        response = requests.post(login_url, json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('requires_2fa'):
                print("🔐 2FA required. Please enter your 2FA code:")
                twofa_code = input().strip()
                
                verify_url = f"{BASE_URL}/api/auth/login/verify-2fa"
                verify_response = requests.post(verify_url, json={
                    "email": ADMIN_EMAIL,
                    "token": twofa_code
                })
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    return verify_data.get('access_token')
                else:
                    print(f"❌ 2FA verification failed: {verify_response.status_code} - {verify_response.text}")
                    return None
            else:
                return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def populate_moderation_translations():
    """Populate moderation translations via API"""
    print("🚀 API-based Moderation Translations Population")
    print("=" * 50)
    
    # Login first
    print("🔐 Logging in as admin...")
    token = login_admin()
    if not token:
        return False
    
    print("✅ Login successful!")
    
    # Load English translations
    json_file = "frontend/src/i18n/locales/en.json"
    print(f"📖 Loading {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return False
    
    # Flatten and filter moderation translations
    flat_translations = flatten_dict(data)
    moderation_translations = {k: v for k, v in flat_translations.items() if k.startswith('moderation.')}
    
    if not moderation_translations:
        print("❌ No moderation translations found")
        return False
    
    print(f"📝 Found {len(moderation_translations)} moderation translations")
    
    # Use bulk update API
    update_url = f"{BASE_URL}/api/translations/admin/bulk-update/en/moderation"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(update_url, 
                              json={"translations": moderation_translations},
                              headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully populated moderation translations!")
            print(f"   📊 Updated: {result.get('updated', 0)}")
            print(f"   📊 Created: {result.get('created', 0)}")
            return True
        else:
            print(f"❌ API request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making API request: {e}")
        return False

if __name__ == "__main__":
    success = populate_moderation_translations()
    if success:
        print("\n🎉 Moderation translations population completed successfully!")
    else:
        print("\n❌ Moderation translations population failed!")
        exit(1)

