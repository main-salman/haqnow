#!/usr/bin/env python3
"""
Script to remove IP address storage from the database.
This script removes the uploader_ip column from the documents table.
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

def run_migration():
    """Run the IP removal migration."""
    print("🔄 Starting IP address removal migration...")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if uploader_ip column exists
                result = conn.execute(text("SHOW COLUMNS FROM documents LIKE 'uploader_ip'"))
                if result.fetchone():
                    print("📝 Found uploader_ip column, removing it...")
                    
                    # Remove the uploader_ip column
                    conn.execute(text("ALTER TABLE documents DROP COLUMN uploader_ip"))
                    print("✅ Successfully removed uploader_ip column")
                else:
                    print("ℹ️  uploader_ip column not found, migration not needed")
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 