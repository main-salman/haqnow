#!/usr/bin/env python3
"""
Populate database with translations from frontend JSON files.
This script reads all translation files and inserts them into the database.
"""

import os
import sys
import json
import dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

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

# Translation files mapping
TRANSLATION_FILES = {
    "en": "../frontend/src/i18n/locales/en.json",
    "ar": "../frontend/src/i18n/locales/ar.json", 
    "fr": "../frontend/src/i18n/locales/fr.json",
    "de": "../frontend/src/i18n/locales/de.json",
    "ru": "../frontend/src/i18n/locales/ru.json",
    "pl": "../frontend/src/i18n/locales/pl.json",
    "tr": "../frontend/src/i18n/locales/tr.json"
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

def flatten_json(data, parent_key='', separator='.'):
    """Flatten nested JSON structure."""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, separator=separator).items())
        else:
            items.append((new_key, v))
    return dict(items)

def determine_section(key):
    """Determine section from translation key."""
    if key.startswith('navigation.'):
        return 'navigation'
    elif key.startswith('homepage.'):
        return 'homepage'
    elif key.startswith('search.'):
        return 'search'
    elif key.startswith('upload.'):
        return 'upload'
    # Affiliates is part of About page; keep under 'about'
    elif key.startswith('about.'):
        return 'about'
    elif key.startswith('foi.'):
        return 'foi'
    elif key.startswith('privacy.'):
        return 'privacy'
    elif key.startswith('disclaimer.'):
        return 'disclaimer'
    elif key.startswith('moderation.'):
        return 'moderation'
    elif key.startswith('general.'):
        return 'general'
    else:
        return 'general'  # default section

def populate_translations():
    """Populate database with translations from JSON files (safe mode).

    - No deletions
    - Insert missing keys
    - Update only rows previously written by scripts (populate_script/system_migration)
    - Never overwrite admin-edited rows
    """
    print("🌍 Starting translation database population (safe, non-destructive)...")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                total_processed = 0
                
                # Process each language
                for language_code, file_path in TRANSLATION_FILES.items():
                    print(f"\n📝 Processing {language_code.upper()} translations...")
                    
                    # Load JSON file
                    translation_data = load_json_file(file_path)
                    if not translation_data:
                        continue
                    
                    # Flatten the JSON structure
                    flattened = flatten_json(translation_data)
                    
                    language_count = 0
                    for key, value in flattened.items():
                        if isinstance(value, str) and value.strip():
                            section = determine_section(key)
                            
                            # Insert or update translation (only update if previously script/system-created)
                            conn.execute(text("""
                                INSERT INTO translations (`key`, language, value, section, updated_by, created_at, updated_at)
                                VALUES (:key, :language, :value, :section, :updated_by, NOW(), NOW())
                                ON DUPLICATE KEY UPDATE
                                value = IF(updated_by IN ('populate_script','system_migration') OR updated_by IS NULL, VALUES(value), value),
                                section = IF(updated_by IN ('populate_script','system_migration') OR updated_by IS NULL, VALUES(section), section),
                                updated_by = IF(updated_by IN ('populate_script','system_migration') OR updated_by IS NULL, VALUES(updated_by), updated_by),
                                updated_at = IF(updated_by IN ('populate_script','system_migration') OR updated_by IS NULL, NOW(), updated_at)
                            """), {
                                'key': key,
                                'language': language_code,
                                'value': value,
                                'section': section,
                                'updated_by': 'populate_script'
                            })
                            
                            language_count += 1
                            total_processed += 1
                    
                    print(f"✅ Processed {language_count} translations for {language_code.upper()} (inserted/updated if safe)")
                
                # Commit transaction
                trans.commit()
                print(f"\n🎉 Successfully processed {total_processed} total translations (safe mode)!")
                
                # Show summary
                print("\n📊 Translation Summary:")
                result = conn.execute(text("""
                    SELECT language, COUNT(*) as count 
                    FROM translations 
                    GROUP BY language 
                    ORDER BY language
                """)).fetchall()
                
                for row in result:
                    print(f"  {row[0].upper()}: {row[1]} translations")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Population failed: {e}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    populate_translations()
    print("\n🌍 Translation population completed successfully!")
    print("✅ All languages are now available in the admin interface!") 