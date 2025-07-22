#!/usr/bin/env python3
"""
Populate disclaimer translations via API
"""

import requests
import json
import os
import sys

# API Configuration
BASE_URL = "https://www.haqnow.com"
# You'll need to provide admin credentials
ADMIN_EMAIL = "salman.naqvi@gmail.com"
ADMIN_PASSWORD = "***REMOVED***"

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary with dot notation."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def login_admin():
    """Login and get JWT token"""
    login_url = f"{BASE_URL}/api/auth/login"
    
    response = requests.post(login_url, json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('requires_2fa'):
            print("❌ 2FA is enabled. You'll need to handle 2FA verification.")
            print("Please disable 2FA temporarily or implement 2FA handling.")
            return None
        return data.get('access_token')
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def populate_disclaimer_translations():
    """Populate disclaimer translations via API"""
    print("🚀 API-based Disclaimer Translations Population")
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
    
    # Flatten and filter disclaimer translations
    flat_translations = flatten_dict(data)
    disclaimer_translations = {k: v for k, v in flat_translations.items() if k.startswith('disclaimer.')}
    
    if not disclaimer_translations:
        print("❌ No disclaimer translations found")
        return False
    
    print(f"📝 Found {len(disclaimer_translations)} disclaimer translations")
    
    # Use bulk update API
    update_url = f"{BASE_URL}/api/translations/admin/bulk-update/en/disclaimer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(update_url, 
                              json={"translations": disclaimer_translations},
                              headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully populated disclaimer translations!")
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
    success = populate_disclaimer_translations()
    if success:
        print("\n🎉 Disclaimer translations populated successfully!")
    else:
        print("\n❌ Failed to populate disclaimer translations!")
        sys.exit(1) 