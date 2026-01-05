#!/usr/bin/env python3
"""
Update navigation.about translations in database to "Our Mission" (and translations).
This script updates the database translations to match the updated JSON files.
"""

import os
import sys
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

# Translations for navigation.about
TRANSLATIONS = {
    "en": "Our Mission",
    "ar": "مهمتنا",
    "fr": "Notre Mission",
    "de": "Unsere Mission",
    "ru": "Наша Миссия",
    "tr": "Misyonumuz",
    "pl": "Nasza Misja"
}

def update_translations():
    """Update navigation.about translations in database."""
    print("🔄 Updating navigation.about translations in database...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                updated_count = 0
                created_count = 0
                
                for language_code, translation_value in TRANSLATIONS.items():
                    # Check if translation exists
                    result = conn.execute(text("""
                        SELECT id FROM translations 
                        WHERE `key` = 'navigation.about' AND language = :lang
                    """), {'lang': language_code})
                    
                    existing = result.fetchone()
                    
                    if existing:
                        # Update existing
                        conn.execute(text("""
                            UPDATE translations 
                            SET value = :value, 
                                updated_by = 'system_migration',
                                updated_at = NOW()
                            WHERE `key` = 'navigation.about' AND language = :lang
                        """), {
                            'value': translation_value,
                            'lang': language_code
                        })
                        updated_count += 1
                        print(f"  ✅ Updated {language_code}: {translation_value}")
                    else:
                        # Create new
                        conn.execute(text("""
                            INSERT INTO translations (`key`, language, value, section, updated_by, created_at, updated_at)
                            VALUES ('navigation.about', :lang, :value, 'navigation', 'system_migration', NOW(), NOW())
                        """), {
                            'lang': language_code,
                            'value': translation_value
                        })
                        created_count += 1
                        print(f"  ✅ Created {language_code}: {translation_value}")
                
                trans.commit()
                print(f"\n🎉 Successfully updated translations!")
                print(f"   Updated: {updated_count}")
                print(f"   Created: {created_count}")
                print(f"   Total: {updated_count + created_count}")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error updating translations: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_translations()

