#!/usr/bin/env python3
"""
Debug script to test admin translations API
"""

import requests
import json

def get_fresh_token():
    """Get a fresh JWT token with 2FA"""
    # Step 1: Login
    response = requests.post('https://www.haqnow.com/api/auth/login', json={
        'email': 'salman.naqvi@gmail.com',
        'password': '***REMOVED***'
    })

    if response.status_code == 200:
        data = response.json()
        if data.get('requires_2fa'):
            print('Enter 2FA code:')
            twofa = input().strip()
            
            # Step 2: Verify 2FA
            verify_response = requests.post('https://www.haqnow.com/api/auth/login/verify-2fa', json={
                'email': 'salman.naqvi@gmail.com',
                'token': twofa
            })
            
            if verify_response.status_code == 200:
                return verify_response.json().get('access_token')
            else:
                print(f'2FA failed: {verify_response.text}')
                return None
        else:
            return data.get('access_token')
    else:
        print(f'Login failed: {response.text}')
        return None

def test_admin_api():
    """Test the admin translations API"""
    print("🔍 Debug: Admin Translations API")
    print("=" * 40)
    
    # Get token
    token = get_fresh_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Get all translations (no filters)
    print("\n📡 Test 1: All translations (no filters)")
    response = requests.get("https://www.haqnow.com/api/translations/admin/all", headers=headers)
    if response.status_code == 200:
        all_data = response.json()
        print(f"✅ Total translations returned: {len(all_data)}")
        disclaimer_count = len([t for t in all_data if t.get('section') == 'disclaimer'])
        print(f"✅ Disclaimer translations: {disclaimer_count}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return
    
    # Test 2: Get disclaimer translations specifically
    print("\n📡 Test 2: Disclaimer translations only")
    response = requests.get("https://www.haqnow.com/api/translations/admin/all?language=en&section=disclaimer", headers=headers)
    if response.status_code == 200:
        disclaimer_data = response.json()
        print(f"✅ Disclaimer translations returned: {len(disclaimer_data)}")
        
        # Show first few keys
        print("📝 First 10 disclaimer keys:")
        for i, t in enumerate(disclaimer_data[:10]):
            print(f"   {i+1}. {t['key']}")
        
        if len(disclaimer_data) > 10:
            print(f"   ... and {len(disclaimer_data) - 10} more")
            
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 3: Check public API for comparison
    print("\n📡 Test 3: Public API comparison")
    response = requests.get("https://www.haqnow.com/api/translations/languages/en")
    if response.status_code == 200:
        public_data = response.json()
        translations = public_data.get('translations', {})
        disclaimer_keys = [k for k in translations.keys() if k.startswith('disclaimer.')]
        print(f"✅ Public API disclaimer keys: {len(disclaimer_keys)}")
    else:
        print(f"❌ Public API failed: {response.status_code}")

if __name__ == "__main__":
    test_admin_api() 