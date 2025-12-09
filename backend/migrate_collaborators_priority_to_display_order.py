#!/usr/bin/env python3
"""
Migration script to replace priority field with display_order in collaborators table.
This script:
1. Adds display_order column
2. Populates it based on current priority (or created_at if priority is same)
3. Removes priority column
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def main():
    """Migrate collaborators table from priority to display_order."""
    print("🔧 Migrating collaborators table: priority → display_order...")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Step 1: Add display_order column
                print("📋 Step 1: Adding display_order column...")
                conn.execute(text("""
                    ALTER TABLE collaborators 
                    ADD COLUMN display_order INT NOT NULL DEFAULT 0 AFTER website_url
                """))
                print("✅ display_order column added")
                
                # Step 2: Populate display_order based on priority (descending) and created_at
                print("📋 Step 2: Populating display_order based on priority...")
                conn.execute(text("""
                    UPDATE collaborators c1
                    SET display_order = (
                        SELECT COUNT(*) 
                        FROM collaborators c2 
                        WHERE (c2.priority > c1.priority) 
                           OR (c2.priority = c1.priority AND c2.created_at < c1.created_at)
                    )
                """))
                print("✅ display_order populated")
                
                # Step 3: Remove priority column
                print("📋 Step 3: Removing priority column...")
                conn.execute(text("""
                    ALTER TABLE collaborators 
                    DROP COLUMN priority
                """))
                print("✅ priority column removed")
                
                # Step 4: Update index
                print("📋 Step 4: Updating index...")
                conn.execute(text("""
                    ALTER TABLE collaborators 
                    ADD INDEX idx_display_order (display_order)
                """))
                print("✅ Index updated")
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during migration: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

if __name__ == "__main__":
    main()

