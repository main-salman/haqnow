#!/usr/bin/env python3
"""
Database Backup Script for HaqNow.com
=====================================

This script creates a comprehensive backup of the current local MySQL database
before migrating to EXOscale DBaaS. It includes:
- Full database dump with structure and data
- Verification of backup integrity
- Backup compression and timestamping
- Error handling and logging

Learning from history.txt: Previous external database issues required
fallback to local database. This script ensures we have a reliable backup
before attempting migration to EXOscale managed database.

Usage:
    python3 backup_local_database.py
"""

import os
import sys
import subprocess
import datetime
import gzip
import json
import hashlib
import tempfile
from pathlib import Path

# Configuration
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_USER = "foi_user"
MYSQL_PASSWORD = "***REMOVED***"
MYSQL_DATABASE = "foi_archive"

BACKUP_DIR = Path("./database_backups")
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def log(message):
    """Log messages with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        log(f"❌ Command failed: {cmd}")
        log(f"Error: {e.stderr}")
        return None

def check_mysql_connection():
    """Test MySQL connection before backup."""
    log("🔍 Testing MySQL connection...")
    
    cmd = f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u {MYSQL_USER} -p{MYSQL_PASSWORD} -e 'SELECT 1;' 2>/dev/null"
    result = run_command(cmd, check=False)
    
    if result and result.returncode == 0:
        log("✅ MySQL connection successful")
        return True
    else:
        log("❌ MySQL connection failed")
        log("Please ensure MySQL is running and credentials are correct")
        return False

def get_database_info():
    """Get database information and statistics."""
    log("📊 Gathering database information...")
    
    info = {}
    
    # Get table count
    cmd = f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u {MYSQL_USER} -p{MYSQL_PASSWORD} -e 'SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = \"{MYSQL_DATABASE}\";' --skip-column-names"
    result = run_command(cmd, check=False)
    if result and result.returncode == 0:
        info['table_count'] = result.stdout.strip()
    
    # Get row counts for main tables
    tables = ['documents', 'translations', 'banned_tags']
    for table in tables:
        cmd = f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u {MYSQL_USER} -p{MYSQL_PASSWORD} -e 'SELECT COUNT(*) FROM {MYSQL_DATABASE}.{table};' --skip-column-names 2>/dev/null"
        result = run_command(cmd, check=False)
        if result and result.returncode == 0:
            info[f'{table}_count'] = result.stdout.strip()
    
    # Get database size
    cmd = f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u {MYSQL_USER} -p{MYSQL_PASSWORD} -e 'SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS \"DB Size in MB\" FROM information_schema.tables WHERE table_schema=\"{MYSQL_DATABASE}\";' --skip-column-names"
    result = run_command(cmd, check=False)
    if result and result.returncode == 0:
        info['database_size_mb'] = result.stdout.strip()
    
    return info

def create_backup():
    """Create a complete MySQL database backup."""
    log("📦 Creating database backup...")
    
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Define backup file paths
    backup_filename = f"haqnow_database_backup_{TIMESTAMP}.sql"
    backup_path = BACKUP_DIR / backup_filename
    compressed_path = BACKUP_DIR / f"{backup_filename}.gz"
    
    # Create mysqldump command with comprehensive options
    dump_cmd = f"""mysqldump \
        --host={MYSQL_HOST} \
        --port={MYSQL_PORT} \
        --user={MYSQL_USER} \
        --password={MYSQL_PASSWORD} \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --complete-insert \
        --add-drop-table \
        --add-locks \
        --disable-keys \
        --extended-insert \
        --quick \
        --lock-tables=false \
        {MYSQL_DATABASE} > {backup_path}"""
    
    log(f"📤 Dumping database to: {backup_path}")
    result = run_command(dump_cmd, check=False)
    
    if not result or result.returncode != 0:
        log("❌ Database backup failed")
        return None
    
    # Verify backup file was created and has content
    if not backup_path.exists() or backup_path.stat().st_size == 0:
        log("❌ Backup file is empty or doesn't exist")
        return None
    
    # Compress the backup
    log("🗜️ Compressing backup...")
    try:
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remove uncompressed file
        backup_path.unlink()
        log(f"✅ Compressed backup saved: {compressed_path}")
        
    except Exception as e:
        log(f"❌ Compression failed: {e}")
        return backup_path
    
    return compressed_path

def verify_backup(backup_path):
    """Verify backup integrity and content."""
    log("🔍 Verifying backup integrity...")
    
    if not backup_path.exists():
        log("❌ Backup file doesn't exist")
        return False
    
    file_size = backup_path.stat().st_size
    log(f"📏 Backup file size: {file_size / 1024 / 1024:.2f} MB")
    
    if file_size < 1000:  # Less than 1KB seems suspicious
        log("⚠️ Backup file seems very small")
        return False
    
    # Check if it's a gzipped file and try to read it
    try:
        if backup_path.suffix == '.gz':
            with gzip.open(backup_path, 'rt') as f:
                first_lines = [f.readline() for _ in range(5)]
        else:
            with open(backup_path, 'r') as f:
                first_lines = [f.readline() for _ in range(5)]
        
        # Check for SQL dump headers
        content = ''.join(first_lines)
        if 'mysqldump' in content and 'CREATE TABLE' in content or 'INSERT INTO' in content:
            log("✅ Backup content verification passed")
            return True
        else:
            log("⚠️ Backup content doesn't look like a MySQL dump")
            return False
            
    except Exception as e:
        log(f"❌ Error reading backup file: {e}")
        return False

def generate_backup_metadata(backup_path, db_info):
    """Generate metadata file for the backup."""
    log("📋 Generating backup metadata...")
    
    metadata = {
        'backup_timestamp': TIMESTAMP,
        'backup_date': datetime.datetime.now().isoformat(),
        'source_database': {
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'database': MYSQL_DATABASE,
            'user': MYSQL_USER
        },
        'database_info': db_info,
        'backup_file': {
            'filename': backup_path.name,
            'size_bytes': backup_path.stat().st_size,
            'size_mb': round(backup_path.stat().st_size / 1024 / 1024, 2)
        },
        'migration_purpose': 'EXOscale DBaaS migration',
        'notes': 'Complete database backup before migrating from local MySQL to EXOscale managed database'
    }
    
    # Calculate file hash for integrity checking
    sha256_hash = hashlib.sha256()
    with open(backup_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    metadata['backup_file']['sha256'] = sha256_hash.hexdigest()
    
    # Save metadata
    metadata_path = backup_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    log(f"✅ Metadata saved: {metadata_path}")
    return metadata_path

def main():
    """Main backup process."""
    log("🚀 Starting HaqNow.com database backup process...")
    log(f"Database: {MYSQL_DATABASE} on {MYSQL_HOST}:{MYSQL_PORT}")
    
    # Step 1: Check MySQL connection
    if not check_mysql_connection():
        sys.exit(1)
    
    # Step 2: Gather database information
    db_info = get_database_info()
    log("📊 Database Information:")
    for key, value in db_info.items():
        log(f"   {key}: {value}")
    
    # Step 3: Create backup
    backup_path = create_backup()
    if not backup_path:
        log("❌ Backup creation failed")
        sys.exit(1)
    
    # Step 4: Verify backup
    if not verify_backup(backup_path):
        log("❌ Backup verification failed")
        sys.exit(1)
    
    # Step 5: Generate metadata
    metadata_path = generate_backup_metadata(backup_path, db_info)
    
    # Step 6: Summary
    log("🎉 Backup completed successfully!")
    log("📁 Backup files created:")
    log(f"   📦 Backup: {backup_path}")
    log(f"   📋 Metadata: {metadata_path}")
    log("")
    log("💡 Next steps:")
    log("   1. Test backup restoration (optional)")
    log("   2. Deploy EXOscale database with Terraform")
    log("   3. Run migration script to transfer data")
    log("   4. Test application with new database")
    log("   5. Disable local database when satisfied")
    
    # Create a quick restore command reference
    restore_cmd = f"gunzip -c {backup_path} | mysql -h HOST -u USER -pPASSWORD DATABASE_NAME"
    log("")
    log("🔧 To restore this backup later:")
    log(f"   {restore_cmd}")

if __name__ == "__main__":
    main() 