#!/usr/bin/env python3
"""
Populate database with disclaimer translations from frontend JSON file.
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
    """Flatten nested dictionary with dot notation."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def determine_section(key):
    """Determine which section a translation key belongs to."""
    if key.startswith('disclaimer.'):
        return 'disclaimer'
    elif key.startswith('navigation.'):
        return 'navigation'
    elif key.startswith('homepage.'):
        return 'homepage'
    elif key.startswith('search.'):
        return 'search'
    elif key.startswith('upload.'):
        return 'upload'
    elif key.startswith('privacy.'):
        return 'privacy'
    elif key.startswith('general.'):
        return 'general'
    elif key.startswith('about.'):
        return 'about'
    elif key.startswith('foi.'):
        return 'foi'
    else:
        return 'general'

def populate_disclaimer_translations():
    """Populate database with disclaimer translations."""
    print("🌍 Starting disclaimer translations population...")
    
    # Load English translations
    en_file = "frontend/src/i18n/locales/en.json"
    print(f"📖 Loading {en_file}...")
    
    en_data = load_json_file(en_file)
    if not en_data:
        print(f"❌ Failed to load {en_file}")
        return False
    
    # Flatten the JSON structure
    flat_translations = flatten_dict(en_data)
    
    # Filter only disclaimer translations
    disclaimer_translations = {k: v for k, v in flat_translations.items() if k.startswith('disclaimer.')}
    
    if not disclaimer_translations:
        print("❌ No disclaimer translations found in English file")
        return False
    
    print(f"📝 Found {len(disclaimer_translations)} disclaimer translation keys")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                total_inserted = 0
                total_updated = 0
                
                for key, value in disclaimer_translations.items():
                    section = determine_section(key)
                    
                    # Insert or update translation
                    insert_sql = """
                    INSERT INTO translations (`key`, language, value, section, updated_by) 
                    VALUES (:key, 'en', :value, :section, 'populate_disclaimer_script')
                    ON DUPLICATE KEY UPDATE 
                    value = VALUES(value),
                    section = VALUES(section),
                    updated_by = VALUES(updated_by),
                    updated_at = CURRENT_TIMESTAMP
                    """
                    
                    result = conn.execute(text(insert_sql), {
                        'key': key,
                        'value': value,
                        'section': section
                    })
                    
                    if result.rowcount == 1:
                        total_inserted += 1
                    else:
                        total_updated += 1
                    
                    print(f"  ✅ {key} = {value[:50]}{'...' if len(value) > 50 else ''}")
                
                # Commit transaction
                trans.commit()
                
                print(f"✅ Successfully populated disclaimer translations!")
                print(f"   📊 Inserted: {total_inserted}")
                print(f"   📊 Updated: {total_updated}")
                print(f"   📊 Total: {len(disclaimer_translations)}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during translation insertion: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Disclaimer Translations Population Script")
    print("=" * 50)
    
    success = populate_disclaimer_translations()
    
    if success:
        print("\n🎉 Disclaimer translations population completed successfully!")
        print("✅ You can now manage disclaimer translations in the admin panel")
    else:
        print("\n❌ Disclaimer translations population failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 