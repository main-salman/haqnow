#!/usr/bin/env python3
"""
Update mission statement translations in database with new content.
This script updates the database translations to match the updated JSON files.
"""

import os
import sys
import json
import dotenv
from sqlalchemy import create_engine, text

# Load environment variables
dotenv.load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to individual components
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_user = os.getenv("MYSQL_USER", "foi_user")
    mysql_password = os.getenv("MYSQL_PASSWORD", "password")
    mysql_database = os.getenv("MYSQL_DATABASE", "foi_archive")
    
    DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

# Load translations from JSON files
TRANSLATION_FILES = {
    "en": "../frontend/src/i18n/locales/en.json",
    "ar": "../frontend/src/i18n/locales/ar.json",
    "fr": "../frontend/src/i18n/locales/fr.json",
    "de": "../frontend/src/i18n/locales/de.json",
    "ru": "../frontend/src/i18n/locales/ru.json",
    "tr": "../frontend/src/i18n/locales/tr.json",
    "pl": "../frontend/src/i18n/locales/pl.json"
}

def load_json_file(file_path):
    """Load JSON file and return the data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in {file_path}: {e}")
        return None

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

def determine_section(key):
    """Determine section based on key prefix."""
    if key.startswith('navigation.'):
        return 'navigation'
    elif key.startswith('about.mission'):
        return 'about'
    elif key.startswith('about.'):
        return 'about'
    elif key.startswith('homepage.'):
        return 'homepage'
    elif key.startswith('search.'):
        return 'search'
    elif key.startswith('upload.'):
        return 'upload'
    elif key.startswith('privacy.'):
        return 'privacy'
    else:
        return 'general'

def update_translations():
    """Update mission statement translations in database."""
    print("🔄 Updating mission statement translations in database...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                total_updated = 0
                total_created = 0
                
                # Mission statement keys to update
                mission_keys = [
                    'about.missionTitle',
                    'about.missionAuthor',
                    'about.missionIntro',
                    'about.missionRealization',
                    'about.missionPurpose',
                    'about.missionNotLeakSite',
                    'about.missionWhoWeServeTitle',
                    'about.missionWhoWeServeDesc',
                    'about.missionWhistleblower',
                    'about.missionJournalist',
                    'about.missionResearcher',
                    'about.missionLawyer',
                    'about.missionOathTitle',
                    'about.missionOathDesc',
                    'about.missionOathNo',
                    'about.missionOathYes',
                    'about.missionPrivacyTitle',
                    'about.missionPrivacyDesc',
                    'about.missionPrivacyNoTracking',
                    'about.missionPrivacyEthicalAI',
                    'about.missionGovernanceTitle',
                    'about.missionGovernanceDesc',
                    'about.missionHaqMeaning',
                    'about.missionWelcome',
                    'about.missionSignature',
                    'about.missionFounder'
                ]
                
                for language_code, file_path in TRANSLATION_FILES.items():
                    translations = load_json_file(file_path)
                    if not translations:
                        continue
                    
                    flattened = flatten_dict(translations)
                    language_count = 0
                    
                    for key in mission_keys:
                        if key in flattened:
                            value = flattened[key]
                            if isinstance(value, str) and value.strip():
                                section = determine_section(key)
                                
                                # Check if translation exists
                                result = conn.execute(text("""
                                    SELECT id FROM translations 
                                    WHERE `key` = :key AND language = :lang
                                """), {'key': key, 'lang': language_code})
                                
                                existing = result.fetchone()
                                
                                if existing:
                                    # Update existing
                                    conn.execute(text("""
                                        UPDATE translations 
                                        SET value = :value, 
                                            section = :section,
                                            updated_by = 'system_migration',
                                            updated_at = NOW()
                                        WHERE `key` = :key AND language = :lang
                                    """), {
                                        'value': value,
                                        'section': section,
                                        'key': key,
                                        'lang': language_code
                                    })
                                    total_updated += 1
                                else:
                                    # Create new
                                    conn.execute(text("""
                                        INSERT INTO translations (`key`, language, value, section, updated_by, created_at, updated_at)
                                        VALUES (:key, :lang, :value, :section, 'system_migration', NOW(), NOW())
                                    """), {
                                        'key': key,
                                        'lang': language_code,
                                        'value': value,
                                        'section': section
                                    })
                                    total_created += 1
                                
                                language_count += 1
                    
                    print(f"  ✅ Processed {language_count} translations for {language_code.upper()}")
                
                trans.commit()
                print(f"\n🎉 Successfully updated mission statement translations!")
                print(f"   Updated: {total_updated}")
                print(f"   Created: {total_created}")
                print(f"   Total: {total_updated + total_created}")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error updating translations: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_translations()

