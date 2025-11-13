#!/usr/bin/env python3
"""
Add ai_summary column to documents table
"""
import sys
import os
from sqlalchemy import text, Column, Text, inspect

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import engine, SessionLocal
from app.database.models import Document

def add_ai_summary_column():
    """Add ai_summary column to documents table if it doesn't exist"""
    
    print("🔄 Adding ai_summary column to documents table...")
    
    with SessionLocal() as db:
        try:
            # Check if column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('documents')]
            
            if 'ai_summary' in columns:
                print("✅ ai_summary column already exists")
                return True
            
            # Add the column
            print("📝 Adding ai_summary column...")
            db.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN ai_summary TEXT NULL
                COMMENT 'AI-generated summary (1 paragraph) using Groq API'
            """))
            db.commit()
            
            print("✅ ai_summary column added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error adding ai_summary column: {e}")
            db.rollback()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("AI Summary Column Migration")
    print("=" * 60)
    
    success = add_ai_summary_column()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Documents will now have AI-generated summaries")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

