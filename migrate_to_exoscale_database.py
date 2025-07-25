#!/usr/bin/env python3
"""
EXOscale Database Migration Script for HaqNow.com
=================================================

This script migrates data from local MySQL to EXOscale DBaaS by:
1. Connecting to EXOscale database
2. Creating the required database schema
3. Importing the local MySQL backup
4. Verifying data integrity

Usage:
    python3 migrate_to_exoscale_database.py --backup-file <backup_file.sql.gz>
"""

import os
import sys
import subprocess
import time
import json
import gzip
from datetime import datetime
from pathlib import Path
import argparse
import pymysql

class EXOscaleMigrator:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"migration_log_{self.timestamp}.txt"
        
        # EXOscale database configuration
        self.exoscale_config = {
            'host': '***REMOVED***',
            'port': 21699,
            'user': 'foi_user',
            'password': '***REMOVED***',
            'database': 'defaultdb',
            'ssl': {'ssl_ca': None, 'ssl_disabled': False},
            'charset': 'utf8mb4',
            'connect_timeout': 60
        }
        
        # Local database configuration
        self.local_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'foi_user',
            'password': '***REMOVED***',
            'database': 'foi_archive'
        }
    
    def log(self, message, level="INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        # Also write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def test_exoscale_connection(self):
        """Test connection to EXOscale database."""
        self.log("🔍 Testing EXOscale database connection...")
        
        try:
            connection = pymysql.connect(**self.exoscale_config)
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION(), DATABASE()")
            result = cursor.fetchone()
            
            self.log(f"✅ EXOscale connection successful")
            self.log(f"   MySQL Version: {result[0]}")
            self.log(f"   Current Database: {result[1]}")
            
            connection.close()
            return True
            
        except Exception as e:
            self.log(f"❌ EXOscale connection failed: {e}", "ERROR")
            return False
    
    def create_target_database(self):
        """Create the foi_archive database on EXOscale."""
        self.log("🏗️ Creating target database on EXOscale...")
        
        try:
            connection = pymysql.connect(**self.exoscale_config)
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS foi_archive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.log("✅ Database 'foi_archive' created/verified")
            
            # Switch to the new database
            cursor.execute("USE foi_archive")
            self.log("✅ Switched to foi_archive database")
            
            connection.commit()
            connection.close()
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create target database: {e}", "ERROR")
            return False
    
    def import_backup_to_exoscale(self, backup_file):
        """Import the backup file to EXOscale database."""
        self.log(f"📥 Importing backup to EXOscale: {backup_file}")
        
        try:
            # Decompress the backup file if it's gzipped
            if backup_file.endswith('.gz'):
                self.log("🗜️ Decompressing backup file...")
                with gzip.open(backup_file, 'rt') as f:
                    sql_content = f.read()
            else:
                with open(backup_file, 'r') as f:
                    sql_content = f.read()
            
            # Connect to EXOscale database
            exo_config = self.exoscale_config.copy()
            exo_config['database'] = 'foi_archive'
            
            connection = pymysql.connect(**exo_config)
            cursor = connection.cursor()
            
            self.log("📤 Executing SQL import...")
            
            # Split SQL content by statements and execute them
            statements = sql_content.split(';')
            successful_statements = 0
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        successful_statements += 1
                    except Exception as e:
                        # Skip some common harmless errors
                        if "already exists" not in str(e).lower():
                            self.log(f"⚠️ Statement {i+1} failed: {e}", "WARNING")
            
            connection.commit()
            connection.close()
            
            self.log(f"✅ Import completed: {successful_statements} statements executed")
            return True
            
        except Exception as e:
            self.log(f"❌ Import failed: {e}", "ERROR")
            return False
    
    def verify_migration(self):
        """Verify the migration by comparing data counts."""
        self.log("🔍 Verifying migration...")
        
        try:
            # Connect to local database
            local_conn = pymysql.connect(**self.local_config)
            local_cursor = local_conn.cursor()
            
            # Connect to EXOscale database
            exo_config = self.exoscale_config.copy()
            exo_config['database'] = 'foi_archive'
            exo_conn = pymysql.connect(**exo_config)
            exo_cursor = exo_conn.cursor()
            
            # Get table list from local
            local_cursor.execute("SHOW TABLES")
            tables = [table[0] for table in local_cursor.fetchall()]
            
            self.log(f"📊 Verifying {len(tables)} tables...")
            
            verification_results = {}
            all_match = True
            
            for table in tables:
                # Count records in local database
                local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                local_count = local_cursor.fetchone()[0]
                
                # Count records in EXOscale database
                try:
                    exo_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    exo_count = exo_cursor.fetchone()[0]
                except Exception as e:
                    self.log(f"❌ Table {table} not found in EXOscale: {e}", "ERROR")
                    exo_count = -1
                    all_match = False
                
                verification_results[table] = {
                    'local_count': local_count,
                    'exoscale_count': exo_count,
                    'match': local_count == exo_count
                }
                
                if local_count == exo_count:
                    self.log(f"✅ {table}: {local_count} records (match)")
                else:
                    self.log(f"❌ {table}: Local={local_count}, EXOscale={exo_count} (mismatch)", "ERROR")
                    all_match = False
            
            local_conn.close()
            exo_conn.close()
            
            # Save verification results
            verification_file = f"migration_verification_{self.timestamp}.json"
            with open(verification_file, 'w') as f:
                json.dump(verification_results, f, indent=2)
            
            self.log(f"📋 Verification results saved: {verification_file}")
            
            if all_match:
                self.log("🎉 Migration verification PASSED - All data migrated successfully!")
                return True
            else:
                self.log("❌ Migration verification FAILED - Data mismatch detected!", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Verification failed: {e}", "ERROR")
            return False
    
    def run_migration(self, backup_file):
        """Execute the complete migration process."""
        self.log("🚀 Starting EXOscale database migration...")
        self.log(f"📁 Backup file: {backup_file}")
        
        # Step 1: Test EXOscale connection
        if not self.test_exoscale_connection():
            self.log("❌ Migration aborted - EXOscale connection failed", "ERROR")
            return False
        
        # Step 2: Create target database
        if not self.create_target_database():
            self.log("❌ Migration aborted - Failed to create target database", "ERROR")
            return False
        
        # Step 3: Import backup
        if not self.import_backup_to_exoscale(backup_file):
            self.log("❌ Migration aborted - Import failed", "ERROR")
            return False
        
        # Step 4: Verify migration
        if not self.verify_migration():
            self.log("❌ Migration completed but verification failed", "ERROR")
            return False
        
        self.log("🎉 EXOscale migration completed successfully!")
        self.log("")
        self.log("📋 Next steps:")
        self.log("  1. Update application configuration to use EXOscale database")
        self.log("  2. Test application thoroughly")
        self.log("  3. Monitor for at least 1 week")
        self.log("  4. Disable local MySQL service")
        self.log("  5. Delete local MySQL data")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Migrate database to EXOscale')
    parser.add_argument('--backup-file', required=True, help='Path to backup file (.sql or .sql.gz)')
    parser.add_argument('--dry-run', action='store_true', help='Test connections without migrating')
    
    args = parser.parse_args()
    
    # Check if backup file exists
    if not Path(args.backup_file).exists():
        print(f"❌ Backup file not found: {args.backup_file}")
        sys.exit(1)
    
    migrator = EXOscaleMigrator()
    
    if args.dry_run:
        print("🧪 DRY RUN - Testing connections...")
        success = migrator.test_exoscale_connection()
        sys.exit(0 if success else 1)
    
    try:
        success = migrator.run_migration(args.backup_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 