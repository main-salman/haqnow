#!/usr/bin/env python3
"""
Database migration script to create the Translation table for multilingual support.
This script creates the translations table with proper indexes and constraints.
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

def create_translation_table():
    """Create the Translation table for multilingual support."""
    print("🌍 Starting Translation table creation for multilingual support...")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if translations table already exists
                result = conn.execute(text("SHOW TABLES LIKE 'translations'"))
                if result.fetchone():
                    print("ℹ️  translations table already exists, skipping creation")
                    trans.commit()
                    return
                
                print("📝 Creating translations table...")
                
                # Create the translations table
                create_table_sql = """
                CREATE TABLE translations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    `key` VARCHAR(200) NOT NULL,
                    language VARCHAR(5) NOT NULL,
                    value TEXT NOT NULL,
                    section VARCHAR(50) NOT NULL,
                    updated_by VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_key_language (`key`, language),
                    INDEX idx_key (`key`),
                    INDEX idx_language (language),
                    INDEX idx_section (section)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
                
                conn.execute(text(create_table_sql))
                print("✅ Successfully created translations table")
                
                # Insert initial English translations for navigation
                print("📝 Inserting initial navigation translations...")
                
                initial_translations = [
                    ("navigation.brand", "en", "Fadih.org", "navigation"),
                    ("navigation.search", "en", "Search", "navigation"),
                    ("navigation.upload", "en", "Upload", "navigation"),
                    ("navigation.privacy", "en", "Privacy Guaranteed", "navigation"),
                    ("navigation.admin", "en", "Admin", "navigation"),
                    ("homepage.title", "en", "Expose Corruption Documents Worldwide", "homepage"),
                    ("homepage.subtitle", "en", "Fadih.org is a platform dedicated to collecting, organizing, and providing access to documents that expose corruption from around the globe. Upload anonymously, search freely, and contribute to a growing repository of truth and transparency.", "homepage"),
                    ("general.loading", "en", "Loading...", "general"),
                    ("general.error", "en", "Error", "general"),
                    ("general.success", "en", "Success", "general")
                ]
                
                for key, language, value, section in initial_translations:
                    insert_sql = """
                    INSERT INTO translations (`key`, language, value, section, updated_by) 
                    VALUES (:key, :language, :value, :section, 'system_migration')
                    """
                    conn.execute(text(insert_sql), {
                        'key': key,
                        'language': language, 
                        'value': value,
                        'section': section
                    })
                
                print("✅ Successfully inserted initial translations")
                
                # Commit transaction
                trans.commit()
                print("✅ Translation table migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_translation_table()
    print("🎉 Multilingual support is now ready!") 