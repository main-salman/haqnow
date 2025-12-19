#!/usr/bin/env python3
"""
Migration script to add 'type' column to collaborators table.
This script:
1. Adds type column with default value 'collaborator'
2. Updates all existing records to have type='collaborator'
3. Adds index on type column
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def main():
    """Add type column to collaborators table."""
    print("🔧 Adding 'type' column to collaborators table...")
    
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
                # Step 1: Add type column with default value
                print("📋 Step 1: Adding 'type' column...")
                conn.execute(text("""
                    ALTER TABLE collaborators 
                    ADD COLUMN type VARCHAR(50) NOT NULL DEFAULT 'collaborator' AFTER website_url
                """))
                print("✅ 'type' column added")
                
                # Step 2: Update all existing records to have type='collaborator' (redundant but safe)
                print("📋 Step 2: Setting type='collaborator' for all existing records...")
                conn.execute(text("""
                    UPDATE collaborators 
                    SET type = 'collaborator' 
                    WHERE type IS NULL OR type = ''
                """))
                print("✅ Existing records updated")
                
                # Step 3: Add index on type column
                print("📋 Step 3: Adding index on 'type' column...")
                try:
                    conn.execute(text("""
                        CREATE INDEX idx_collaborators_type ON collaborators(type)
                    """))
                    print("✅ Index added")
                except Exception as e:
                    # Index might already exist
                    print(f"⚠️  Index creation skipped (might already exist): {e}")
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                print("")
                print("🎯 Next steps:")
                print("   1. Use the admin dashboard to add investigative research partners")
                print("   2. Set type='investigative_research_partner' when creating new partners")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during migration: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

if __name__ == "__main__":
    main()
