#!/usr/bin/env python3
"""
Fix database schema: Change TEXT columns to MEDIUMTEXT for large documents
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database.database import engine
from sqlalchemy import text

def fix_text_columns():
    """Update TEXT columns to MEDIUMTEXT"""
    conn = engine.connect()
    
    try:
        print("🔧 Updating text columns to MEDIUMTEXT...")
        
        # Alter columns
        queries = [
            "ALTER TABLE documents MODIFY COLUMN ocr_text MEDIUMTEXT",
            "ALTER TABLE documents MODIFY COLUMN search_text MEDIUMTEXT",
            "ALTER TABLE documents MODIFY COLUMN ocr_text_original MEDIUMTEXT",
            "ALTER TABLE documents MODIFY COLUMN ocr_text_english MEDIUMTEXT",
        ]
        
        for query in queries:
            try:
                conn.execute(text(query))
                conn.commit()
                column = query.split("COLUMN")[1].split()[0]
                print(f"✅ Updated {column} to MEDIUMTEXT")
            except Exception as e:
                print(f"⚠️  {query.split('COLUMN')[1].split()[0]}: {e}")
        
        print("\n✅ Schema update complete!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_text_columns()

