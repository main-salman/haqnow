#!/usr/bin/env python3
"""
Populate Affiliates section translations for the About page.
This adds the new Affiliates section with empty content to be filled by admins.
"""

import sys
import os
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.models import Translation
import structlog

# Load environment variables
dotenv.load_dotenv()

logger = structlog.get_logger()

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

# Supported languages from the frontend
SUPPORTED_LANGUAGES = ['en', 'ar', 'fr', 'de', 'ru', 'pl', 'tr']

def populate_affiliates_translations():
    """Add Affiliates section translations for all supported languages."""
    
    try:
        # Get database connection
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        translations_to_add = []
        
        # Define default translations for each language
        default_translations = {
            'en': {
                'affiliatesTitle': 'Our Affiliates & Partners',
                'affiliatesBody': 'Information about our trusted affiliates and partners will be displayed here. This section is managed by administrators.'
            },
            'ar': {
                'affiliatesTitle': 'الشركاء والمؤسسات التابعة',
                'affiliatesBody': 'سيتم عرض معلومات حول شركائنا والمؤسسات التابعة الموثوقة هنا. يتم إدارة هذا القسم من قبل المديرين.'
            },
            'fr': {
                'affiliatesTitle': 'Nos Affiliés et Partenaires',
                'affiliatesBody': 'Les informations sur nos affiliés et partenaires de confiance seront affichées ici. Cette section est gérée par les administrateurs.'
            },
            'de': {
                'affiliatesTitle': 'Unsere Partner und Affiliates',
                'affiliatesBody': 'Informationen über unsere vertrauenswürdigen Partner und Affiliates werden hier angezeigt. Dieser Bereich wird von Administratoren verwaltet.'
            },
            'ru': {
                'affiliatesTitle': 'Наши Партнеры и Аффилиаты',
                'affiliatesBody': 'Информация о наших доверенных партнерах и аффилиатах будет отображена здесь. Этот раздел управляется администраторами.'
            },
            'pl': {
                'affiliatesTitle': 'Nasi Partnerzy i Afilianci',
                'affiliatesBody': 'Informacje o naszych zaufanych partnerach i afiliowanch będą wyświetlane tutaj. Ta sekcja jest zarządzana przez administratorów.'
            },
            'tr': {
                'affiliatesTitle': 'Ortaklarımız ve Bağlı Kuruluşlarımız',
                'affiliatesBody': 'Güvenilir ortaklarımız ve bağlı kuruluşlarımız hakkında bilgiler burada görüntülenecektir. Bu bölüm yöneticiler tarafından yönetilir.'
            }
        }
        
        # Create translations for each language
        for language in SUPPORTED_LANGUAGES:
            lang_translations = default_translations.get(language, default_translations['en'])
            
            # Add title translation
            title_translation = Translation(
                key='about.affiliatesTitle',
                language=language,
                value=lang_translations['affiliatesTitle'],
                section='about',
                updated_by='system_populate_affiliates'
            )
            translations_to_add.append(title_translation)
            
            # Add body translation
            body_translation = Translation(
                key='about.affiliatesBody', 
                language=language,
                value=lang_translations['affiliatesBody'],
                section='about',
                updated_by='system_populate_affiliates'
            )
            translations_to_add.append(body_translation)
        
        # Check for existing translations and only add new ones
        added_count = 0
        for translation in translations_to_add:
            existing = db.query(Translation).filter(
                Translation.key == translation.key,
                Translation.language == translation.language
            ).first()
            
            if not existing:
                db.add(translation)
                added_count += 1
                print(f"✓ Adding translation: {translation.key} ({translation.language})")
            else:
                print(f"⚠ Translation already exists: {translation.key} ({translation.language})")
        
        # Commit all changes
        db.commit()
        print(f"✅ Successfully populated Affiliates translations. Added: {added_count}")
        
    except Exception as e:
        print(f"❌ Error populating Affiliates translations: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    populate_affiliates_translations()
    print("✅ Affiliates translations populated successfully!")