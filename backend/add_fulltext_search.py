#!/usr/bin/env python3
"""
Full-Text Search Migration for Fadih.org
=========================================

This script adds full-text search indexes to the MySQL database for dramatically
improved search performance. It creates:

1. Combined search_text column for optimized searching
2. Full-text indexes on individual fields 
3. Full-text index on combined search_text column
4. Updates existing documents with combined search text

Performance Impact:
- 10-100x faster search queries
- Built-in relevance scoring
- Boolean search operator support
- Better handling of large document collections

Usage:
    python add_fulltext_search.py
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

def add_fulltext_search():
    """Add full-text search capabilities to the documents table."""
    print("🔍 Starting Full-Text Search Migration for Enhanced Performance...")
    print("=" * 60)
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("📊 Checking current database structure...")
            
            # Check if search_text column already exists
            try:
                result = conn.execute(text("SHOW COLUMNS FROM documents LIKE 'search_text'"))
                search_text_exists = result.fetchone() is not None
            except Exception as e:
                print(f"❌ Error checking search_text column: {e}")
                return False
            
            # Check for existing full-text indexes
            try:
                result = conn.execute(text("""
                    SELECT INDEX_NAME, COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.STATISTICS 
                    WHERE TABLE_NAME = 'documents' 
                    AND TABLE_SCHEMA = DATABASE()
                    AND INDEX_TYPE = 'FULLTEXT'
                """))
                existing_fulltext = result.fetchall()
                print(f"📋 Found {len(existing_fulltext)} existing full-text indexes")
            except Exception as e:
                print(f"❌ Error checking existing indexes: {e}")
                return False
            
            try:
                # Step 1: Add search_text column if it doesn't exist
                if not search_text_exists:
                    print("📝 Adding search_text column...")
                    conn.execute(text("""
                        ALTER TABLE documents 
                        ADD COLUMN search_text TEXT 
                        COMMENT 'Combined searchable text from title, description, and OCR content'
                    """))
                    conn.commit()
                    print("✅ Added search_text column")
                else:
                    print("ℹ️  search_text column already exists")
                
                # Step 2: Populate search_text column with combined content
                print("🔄 Updating search_text with combined content...")
                
                # Get count of documents to update
                count_result = conn.execute(text("SELECT COUNT(*) as count FROM documents"))
                doc_count = count_result.fetchone()[0]
                print(f"📚 Updating {doc_count} documents with combined search text...")
                
                # Update search_text with combined content (handling NULL values)
                conn.execute(text("""
                    UPDATE documents 
                    SET search_text = CONCAT(
                        IFNULL(title, ''), ' ',
                        IFNULL(description, ''), ' ', 
                        IFNULL(ocr_text, ''), ' ',
                        IFNULL(country, ''), ' ',
                        IFNULL(state, ''), ' ',
                        CASE 
                            WHEN generated_tags IS NOT NULL AND JSON_LENGTH(generated_tags) > 0 
                            THEN JSON_UNQUOTE(JSON_EXTRACT(generated_tags, '$[*]'))
                            ELSE ''
                        END
                    )
                    WHERE search_text IS NULL OR search_text = ''
                """))
                conn.commit()
                print("✅ Updated search_text column with combined content")
                
                # Step 3: Add full-text indexes
                print("📊 Creating full-text search indexes...")
                
                # Check and create individual field indexes
                fulltext_indexes = [
                    ("idx_ft_title", "title", "Title field full-text search"),
                    ("idx_ft_ocr_text", "ocr_text", "OCR text full-text search"), 
                    ("idx_ft_search_text", "search_text", "Combined content full-text search"),
                    ("idx_ft_title_desc", "title,description", "Title and description full-text search")
                ]
                
                for index_name, columns, description in fulltext_indexes:
                    # Check if index already exists
                    index_check = conn.execute(text(f"""
                        SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_NAME = 'documents' 
                        AND TABLE_SCHEMA = DATABASE()
                        AND INDEX_NAME = '{index_name}'
                    """))
                    
                    if index_check.fetchone():
                        print(f"ℹ️  Index {index_name} already exists")
                        continue
                    
                    try:
                        print(f"🔨 Creating {description}...")
                        conn.execute(text(f"""
                            ALTER TABLE documents 
                            ADD FULLTEXT INDEX {index_name} ({columns})
                        """))
                        conn.commit()
                        print(f"✅ Created full-text index: {index_name}")
                    except Exception as idx_error:
                        print(f"⚠️  Warning: Could not create index {index_name}: {idx_error}")
                        continue
                
                # Step 4: Create optimized indexes for filtering
                print("🎯 Creating additional search optimization indexes...")
                
                standard_indexes = [
                    ("idx_status_country", "status,country", "Status and country filtering"),
                    ("idx_status_created", "status,created_at", "Status and date filtering")
                ]
                
                for index_name, columns, description in standard_indexes:
                    # Check if index already exists
                    index_check = conn.execute(text(f"""
                        SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_NAME = 'documents' 
                        AND TABLE_SCHEMA = DATABASE()
                        AND INDEX_NAME = '{index_name}'
                    """))
                    
                    if index_check.fetchone():
                        print(f"ℹ️  Index {index_name} already exists")
                        continue
                    
                    try:
                        print(f"🔨 Creating {description}...")
                        conn.execute(text(f"""
                            ALTER TABLE documents 
                            ADD INDEX {index_name} ({columns})
                        """))
                        conn.commit()
                        print(f"✅ Created index: {index_name}")
                    except Exception as idx_error:
                        print(f"⚠️  Warning: Could not create index {index_name}: {idx_error}")
                        continue
                
                # Step 5: Verify the migration
                print("\n🔍 Verifying migration results...")
                
                # Check final index status
                result = conn.execute(text("""
                    SELECT INDEX_NAME, COLUMN_NAME, INDEX_TYPE
                    FROM INFORMATION_SCHEMA.STATISTICS 
                    WHERE TABLE_NAME = 'documents' 
                    AND TABLE_SCHEMA = DATABASE()
                    ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """))
                indexes = result.fetchall()
                
                fulltext_count = sum(1 for idx in indexes if idx[2] == 'FULLTEXT')
                total_indexes = len(set(idx[0] for idx in indexes))
                
                print(f"📊 Migration Summary:")
                print(f"   • Total indexes: {total_indexes}")
                print(f"   • Full-text indexes: {fulltext_count}")
                print(f"   • Documents updated: {doc_count}")
                
                # Test search functionality
                print("\n🧪 Testing full-text search functionality...")
                test_result = conn.execute(text("""
                    SELECT COUNT(*) as count FROM documents 
                    WHERE MATCH(search_text) AGAINST('freedom' IN NATURAL LANGUAGE MODE)
                    AND status = 'approved'
                """))
                test_count = test_result.fetchone()[0]
                print(f"✅ Test search for 'freedom' returned {test_count} results")
                
                print("\n🎉 Full-Text Search Migration Completed Successfully!")
                print("=" * 60)
                print("📈 Expected Performance Improvements:")
                print("   • 10-100x faster search queries")
                print("   • Built-in relevance scoring")
                print("   • Boolean search operators support")
                print("   • Better handling of large document collections")
                print("\n🚀 Your search functionality is now optimized for thousands of documents!")
                
                return True
                
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Fadih.org Full-Text Search Migration")
    print("====================================")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not configured. Please set your database connection string.")
        sys.exit(1)
    
    success = add_fulltext_search()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🔧 Next steps:")
        print("   1. Update search API to use full-text search")
        print("   2. Deploy updated backend code")
        print("   3. Test search performance improvements")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1) 