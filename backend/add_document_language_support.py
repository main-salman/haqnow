#!/usr/bin/env python3
"""
Document Language Support Migration for Fadih.org
===================================================

This script adds document language support to the MySQL database for:
1. Language selection during upload
2. Arabic OCR processing via Mistral API  
3. Arabic to English translation
4. Bilingual search capabilities
5. Bilingual download options

Database Changes:
- document_language: Language of the original document (default: 'english')
- ocr_text_original: OCR text in the original language
- ocr_text_english: OCR text translated to English (for non-English documents)

Usage:
    python add_document_language_support.py
"""

import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to individual components
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_user = os.getenv("MYSQL_USER", "foi_user")
    mysql_password = os.getenv("MYSQL_PASSWORD", "password")
    mysql_database = os.getenv("MYSQL_DATABASE", "foi_archive")
    
    DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

def add_document_language_support():
    """Add document language support to the documents table."""
    print("🌍 Starting Document Language Support Migration...")
    print("=" * 60)
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("📊 Checking current database structure...")
            
            # Check if new columns already exist
            columns_to_add = [
                ('document_language', "VARCHAR(10) NOT NULL DEFAULT 'english'"),
                ('ocr_text_original', "TEXT"),
                ('ocr_text_english', "TEXT")
            ]
            
            existing_columns = []
            for column_name, _ in columns_to_add:
                try:
                    result = conn.execute(text(f"SHOW COLUMNS FROM documents LIKE '{column_name}'"))
                    if result.fetchone():
                        existing_columns.append(column_name)
                except Exception as e:
                    print(f"❌ Error checking {column_name} column: {e}")
                    return False
            
            if existing_columns:
                print(f"ℹ️  Found existing columns: {', '.join(existing_columns)}")
            
            try:
                # Add new columns if they don't exist
                for column_name, column_definition in columns_to_add:
                    if column_name not in existing_columns:
                        print(f"📝 Adding {column_name} column...")
                        
                        sql = f"""
                        ALTER TABLE documents 
                        ADD COLUMN {column_name} {column_definition}
                        COMMENT 'Language support for multilingual document processing'
                        """
                        
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✅ Added {column_name} column")
                    else:
                        print(f"ℹ️  Column {column_name} already exists")
                
                # Add index on document_language for efficient filtering
                print("📊 Creating index on document_language...")
                try:
                    # Check if index already exists
                    index_check = conn.execute(text("""
                        SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_NAME = 'documents' 
                        AND TABLE_SCHEMA = DATABASE()
                        AND INDEX_NAME = 'idx_document_language'
                    """))
                    
                    if not index_check.fetchone():
                        conn.execute(text("""
                            ALTER TABLE documents 
                            ADD INDEX idx_document_language (document_language)
                        """))
                        conn.commit()
                        print("✅ Created index on document_language")
                    else:
                        print("ℹ️  Index idx_document_language already exists")
                        
                except Exception as idx_error:
                    print(f"⚠️  Warning: Could not create index on document_language: {idx_error}")
                
                # Update existing documents to have default language
                print("🔄 Updating existing documents with default language...")
                
                # Count documents that need updating
                count_result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM documents 
                    WHERE document_language IS NULL OR document_language = ''
                """))
                update_count = count_result.fetchone()[0]
                
                if update_count > 0:
                    print(f"📚 Updating {update_count} documents with default language 'english'...")
                    
                    # Update documents with default language
                    conn.execute(text("""
                        UPDATE documents 
                        SET document_language = 'english'
                        WHERE document_language IS NULL OR document_language = ''
                    """))
                    conn.commit()
                    print(f"✅ Updated {update_count} documents with default language")
                else:
                    print("ℹ️  All documents already have language set")
                
                # Copy existing OCR text to original language field for backward compatibility
                print("🔄 Copying existing OCR text to language-specific fields...")
                
                copy_count_result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM documents 
                    WHERE ocr_text IS NOT NULL 
                    AND ocr_text != ''
                    AND (ocr_text_original IS NULL OR ocr_text_original = '')
                """))
                copy_count = copy_count_result.fetchone()[0]
                
                if copy_count > 0:
                    print(f"📚 Copying OCR text for {copy_count} documents...")
                    
                    # Copy existing OCR text to original language field
                    # For existing documents, assume they are English since that was the default
                    conn.execute(text("""
                        UPDATE documents 
                        SET 
                            ocr_text_original = ocr_text,
                            ocr_text_english = ocr_text
                        WHERE ocr_text IS NOT NULL 
                        AND ocr_text != ''
                        AND (ocr_text_original IS NULL OR ocr_text_original = '')
                    """))
                    conn.commit()
                    print(f"✅ Copied OCR text for {copy_count} documents")
                else:
                    print("ℹ️  OCR text already copied or no OCR text to copy")
                
                print("✅ Document Language Support Migration Completed Successfully!")
                print("🌍 The system now supports:")
                print("   • Language selection during document upload")
                print("   • Arabic OCR processing via Mistral API")
                print("   • Arabic to English translation")
                print("   • Bilingual search capabilities")
                print("   • Bilingual download options")
                
                return True
                
            except Exception as migration_error:
                print(f"❌ Migration failed: {migration_error}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    if add_document_language_support():
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1) 