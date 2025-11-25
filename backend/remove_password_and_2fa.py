#!/usr/bin/env python3
"""
Migration script to remove password_hash and 2FA fields from Admin table.
This enables passwordless OTP authentication.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database.database import engine
from sqlalchemy import text

def remove_password_and_2fa():
    """Remove password_hash and 2FA columns from admins table."""
    print("🔄 Starting password and 2FA removal migration...")
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check MySQL version and get column info
                print("📝 Checking existing columns...")
                
                # Get all columns in admins table
                result = conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'admins'
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                
                columns_to_remove = []
                
                # Check and mark columns for removal
                if 'password_hash' in existing_columns:
                    columns_to_remove.append('password_hash')
                    print("   Found password_hash column")
                
                if 'two_factor_enabled' in existing_columns:
                    columns_to_remove.append('two_factor_enabled')
                    print("   Found two_factor_enabled column")
                
                if 'two_factor_secret' in existing_columns:
                    columns_to_remove.append('two_factor_secret')
                    print("   Found two_factor_secret column")
                
                if 'backup_codes' in existing_columns:
                    columns_to_remove.append('backup_codes')
                    print("   Found backup_codes column")
                
                if not columns_to_remove:
                    print("ℹ️  No password/2FA columns found, migration not needed")
                    trans.commit()
                    return True
                
                # Remove columns
                print(f"\n🗑️  Removing {len(columns_to_remove)} column(s)...")
                for column in columns_to_remove:
                    try:
                        conn.execute(text(f"ALTER TABLE admins DROP COLUMN {column}"))
                        print(f"   ✅ Removed {column} column")
                    except Exception as e:
                        print(f"   ⚠️  Error removing {column}: {e}")
                        # Continue with other columns
                
                # Commit transaction
                trans.commit()
                print("\n✅ Migration completed successfully!")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = remove_password_and_2fa()
    sys.exit(0 if success else 1)

