#!/usr/bin/env python3
"""
Local MySQL Data Deletion Script for HaqNow.com
===============================================

This script safely deletes the local MySQL data directory after successful
migration to EXOscale DBaaS and thorough testing. It includes:
- Multiple safety checks and confirmations
- Complete data directory backup before deletion
- Service verification checks
- Disk space reclamation reporting
- Emergency recovery preparation

⚠️  CRITICAL WARNING: This script will permanently delete local MySQL data.
Only run this after:
1. ✅ Successful migration to EXOscale database
2. ✅ Extensive application testing with EXOscale database (minimum 1 week)
3. ✅ Confirmed data integrity and performance
4. ✅ Multiple recent backups completed and verified
5. ✅ MySQL service already disabled
6. ✅ All stakeholders approval

This is a DESTRUCTIVE operation and CANNOT be undone easily.

Usage:
    python3 delete_local_database_data.py --confirm --i-understand-this-is-permanent
"""

import os
import sys
import subprocess
import time
import json
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import argparse

class LocalMySQLDataDeleter:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"mysql_data_deletion_log_{self.timestamp}.txt"
        self.final_backup_dir = Path(f"./mysql_final_backup_{self.timestamp}")
        self.mysql_data_dir = Path("/var/lib/mysql")
        self.mysql_config_dir = Path("/etc/mysql")
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        # Also write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def run_command(self, cmd, check=True):
        """Run a shell command and return the result."""
        try:
            self.log(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Command failed: {cmd}", "ERROR")
            self.log(f"Error: {e.stderr}", "ERROR")
            return None
    
    def check_prerequisites(self):
        """Check all prerequisites before allowing data deletion."""
        self.log("🔍 Checking prerequisites for data deletion...")
        
        checks_passed = 0
        total_checks = 6
        
        # Check 1: Verify MySQL service is disabled
        self.log("1️⃣ Checking MySQL service status...")
        try:
            result = self.run_command("systemctl is-enabled mysql", check=False)
            if result:
                status = result.stdout.strip()
                if status in ["disabled", "masked"]:
                    self.log("✅ MySQL service is disabled")
                    checks_passed += 1
                else:
                    self.log(f"❌ MySQL service is not disabled (status: {status})", "ERROR")
            else:
                self.log("❌ Could not check MySQL service status", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking MySQL service: {e}", "ERROR")
        
        # Check 2: Verify MySQL service is not running
        self.log("2️⃣ Checking MySQL service is not running...")
        try:
            result = self.run_command("systemctl is-active mysql", check=False)
            if result:
                status = result.stdout.strip()
                if status in ["inactive", "failed"]:
                    self.log("✅ MySQL service is not running")
                    checks_passed += 1
                else:
                    self.log(f"❌ MySQL service is running (status: {status})", "ERROR")
            else:
                self.log("❌ Could not check MySQL service active status", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking MySQL service active status: {e}", "ERROR")
        
        # Check 3: Verify application is using EXOscale database
        self.log("3️⃣ Checking application database configuration...")
        try:
            status_file = Path("/opt/foi-archive/.db_status")
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status_content = f.read()
                
                if "DATABASE_TYPE=exoscale" in status_content:
                    self.log("✅ Application is configured for EXOscale database")
                    checks_passed += 1
                else:
                    self.log("❌ Application is not configured for EXOscale database", "ERROR")
            else:
                self.log("❌ Database status file not found", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking database configuration: {e}", "ERROR")
        
        # Check 4: Verify EXOscale database connectivity
        self.log("4️⃣ Checking EXOscale database connectivity...")
        try:
            check_script = Path("/opt/foi-archive/check_database.py")
            if check_script.exists():
                result = self.run_command(f"cd /opt/foi-archive && python3 check_database.py", check=False)
                if result and result.returncode == 0:
                    self.log("✅ EXOscale database is accessible")
                    checks_passed += 1
                else:
                    self.log("❌ EXOscale database is not accessible", "ERROR")
            else:
                self.log("❌ Database check script not found", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking EXOscale database: {e}", "ERROR")
        
        # Check 5: Verify recent backups exist
        self.log("5️⃣ Checking for recent database backups...")
        try:
            backup_dir = Path("./database_backups")
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.gz"))
                if backup_files:
                    # Check if there's a recent backup (within last 7 days)
                    recent_backups = []
                    week_ago = time.time() - (7 * 24 * 60 * 60)
                    
                    for backup in backup_files:
                        if backup.stat().st_mtime > week_ago:
                            recent_backups.append(backup)
                    
                    if recent_backups:
                        self.log(f"✅ Found {len(recent_backups)} recent backup(s)")
                        checks_passed += 1
                    else:
                        self.log("❌ No recent backups found (within 7 days)", "ERROR")
                else:
                    self.log("❌ No backup files found", "ERROR")
            else:
                self.log("❌ Backup directory not found", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking backups: {e}", "ERROR")
        
        # Check 6: Verify disk space for final backup
        self.log("6️⃣ Checking disk space for final backup...")
        try:
            # Get size of MySQL data directory
            if self.mysql_data_dir.exists():
                result = self.run_command(f"du -sb {self.mysql_data_dir}", check=False)
                if result:
                    mysql_size = int(result.stdout.split()[0])
                    mysql_size_mb = mysql_size / (1024 * 1024)
                    
                    # Get available disk space
                    result = self.run_command("df -B1 .", check=False)
                    if result:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            free_space = int(lines[1].split()[3])
                            free_space_mb = free_space / (1024 * 1024)
                            
                            # Need at least 2x the MySQL data size for safe backup
                            needed_space = mysql_size * 2
                            
                            if free_space > needed_space:
                                self.log(f"✅ Sufficient disk space (MySQL: {mysql_size_mb:.1f}MB, Available: {free_space_mb:.1f}MB)")
                                checks_passed += 1
                            else:
                                self.log(f"❌ Insufficient disk space for backup (MySQL: {mysql_size_mb:.1f}MB, Available: {free_space_mb:.1f}MB)", "ERROR")
                        else:
                            self.log("❌ Could not parse disk space output", "ERROR")
                    else:
                        self.log("❌ Could not check disk space", "ERROR")
                else:
                    self.log("❌ Could not get MySQL data directory size", "ERROR")
            else:
                self.log("❌ MySQL data directory does not exist", "ERROR")
        except Exception as e:
            self.log(f"❌ Error checking disk space: {e}", "ERROR")
        
        # Summary
        self.log(f"📊 Prerequisites check: {checks_passed}/{total_checks} passed")
        
        if checks_passed == total_checks:
            self.log("✅ All prerequisites passed")
            return True
        else:
            self.log("❌ Prerequisites check failed", "ERROR")
            self.log("   Data deletion is not safe to proceed.", "ERROR")
            return False
    
    def calculate_space_to_be_freed(self):
        """Calculate how much disk space will be freed."""
        self.log("📏 Calculating disk space to be freed...")
        
        total_size = 0
        directories_to_check = [
            self.mysql_data_dir,
            self.mysql_config_dir,
            Path("/var/log/mysql")
        ]
        
        for directory in directories_to_check:
            if directory.exists():
                try:
                    result = self.run_command(f"du -sb {directory}", check=False)
                    if result:
                        size = int(result.stdout.split()[0])
                        size_mb = size / (1024 * 1024)
                        total_size += size
                        self.log(f"   {directory}: {size_mb:.1f} MB")
                except Exception as e:
                    self.log(f"⚠️ Could not calculate size for {directory}: {e}", "WARNING")
        
        total_size_mb = total_size / (1024 * 1024)
        total_size_gb = total_size_mb / 1024
        
        self.log(f"📊 Total space to be freed: {total_size_mb:.1f} MB ({total_size_gb:.2f} GB)")
        return total_size
    
    def create_final_backup(self):
        """Create a final comprehensive backup before deletion."""
        self.log("📦 Creating final comprehensive backup...")
        
        try:
            # Create backup directory
            self.final_backup_dir.mkdir(exist_ok=True)
            
            # Create tarball of MySQL data directory
            mysql_backup_path = self.final_backup_dir / "mysql_data_final.tar.gz"
            self.log(f"Creating compressed backup: {mysql_backup_path}")
            
            with tarfile.open(mysql_backup_path, "w:gz") as tar:
                if self.mysql_data_dir.exists():
                    tar.add(self.mysql_data_dir, arcname="mysql_data")
                    self.log("✅ MySQL data directory backed up")
                
                if self.mysql_config_dir.exists():
                    tar.add(self.mysql_config_dir, arcname="mysql_config")
                    self.log("✅ MySQL config directory backed up")
                
                # Also backup any MySQL logs
                mysql_log_dir = Path("/var/log/mysql")
                if mysql_log_dir.exists():
                    tar.add(mysql_log_dir, arcname="mysql_logs")
                    self.log("✅ MySQL logs backed up")
            
            # Verify backup was created
            if mysql_backup_path.exists() and mysql_backup_path.stat().st_size > 0:
                backup_size_mb = mysql_backup_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Final backup created: {mysql_backup_path} ({backup_size_mb:.1f} MB)")
                
                # Create backup metadata
                metadata = {
                    'backup_timestamp': self.timestamp,
                    'backup_date': datetime.now().isoformat(),
                    'backup_type': 'final_mysql_deletion_backup',
                    'backup_file': str(mysql_backup_path),
                    'backup_size_bytes': mysql_backup_path.stat().st_size,
                    'backup_size_mb': backup_size_mb,
                    'directories_backed_up': [
                        str(self.mysql_data_dir),
                        str(self.mysql_config_dir),
                        '/var/log/mysql'
                    ],
                    'purpose': 'Final backup before MySQL data deletion after EXOscale migration'
                }
                
                metadata_file = self.final_backup_dir / "backup_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.log(f"✅ Backup metadata saved: {metadata_file}")
                return mysql_backup_path
            else:
                self.log("❌ Backup file was not created or is empty", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to create final backup: {e}", "ERROR")
            return None
    
    def delete_mysql_data(self):
        """Delete the MySQL data directories."""
        self.log("🗑️ Starting MySQL data deletion...")
        
        deleted_directories = []
        failed_deletions = []
        
        directories_to_delete = [
            self.mysql_data_dir,
            Path("/var/log/mysql")
        ]
        
        for directory in directories_to_delete:
            if directory.exists():
                try:
                    self.log(f"Deleting: {directory}")
                    shutil.rmtree(directory)
                    
                    # Verify deletion
                    if not directory.exists():
                        self.log(f"✅ Successfully deleted: {directory}")
                        deleted_directories.append(str(directory))
                    else:
                        self.log(f"❌ Failed to delete: {directory}", "ERROR")
                        failed_deletions.append(str(directory))
                        
                except Exception as e:
                    self.log(f"❌ Error deleting {directory}: {e}", "ERROR")
                    failed_deletions.append(str(directory))
            else:
                self.log(f"ℹ️ Directory does not exist: {directory}")
        
        # Note about config directory (usually keep this)
        self.log(f"ℹ️ MySQL config directory preserved: {self.mysql_config_dir}")
        
        return deleted_directories, failed_deletions
    
    def remove_mysql_package(self, remove_package=False):
        """Optionally remove MySQL package."""
        if not remove_package:
            self.log("ℹ️ MySQL package removal skipped (keeping for potential future use)")
            return True
        
        self.log("📦 Removing MySQL package...")
        
        try:
            # Remove MySQL server package
            result = self.run_command("apt-get remove --purge -y mysql-server mysql-server-8.0", check=False)
            if result and result.returncode == 0:
                self.log("✅ MySQL server package removed")
                
                # Clean up any remaining dependencies
                self.run_command("apt-get autoremove -y", check=False)
                self.run_command("apt-get autoclean", check=False)
                
                return True
            else:
                self.log("⚠️ MySQL package removal had issues", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Error removing MySQL package: {e}", "ERROR")
            return False
    
    def create_recovery_instructions(self, backup_path):
        """Create detailed recovery instructions."""
        self.log("📋 Creating recovery instructions...")
        
        try:
            recovery_file = f"mysql_recovery_instructions_{self.timestamp}.md"
            
            instructions = f"""# MySQL Data Recovery Instructions
            
**Created:** {datetime.now().isoformat()}
**Backup File:** {backup_path}
**Log File:** {self.log_file}

## ⚠️ EMERGENCY RECOVERY PROCEDURE

If you need to recover the deleted MySQL data, follow these steps:

### 1. Reinstall MySQL Server
```bash
sudo apt-get update
sudo apt-get install -y mysql-server
```

### 2. Stop MySQL Service
```bash
sudo systemctl stop mysql
```

### 3. Extract Backup
```bash
# Navigate to the backup location
cd {Path.cwd()}

# Extract the backup
sudo tar -xzf {backup_path} -C /

# This will restore:
# - /var/lib/mysql/ (MySQL data directory)
# - /etc/mysql/ (MySQL configuration)
# - /var/log/mysql/ (MySQL logs)
```

### 4. Fix Permissions
```bash
sudo chown -R mysql:mysql /var/lib/mysql
sudo chown -R mysql:mysql /var/log/mysql
sudo chmod 750 /var/lib/mysql
```

### 5. Start MySQL Service
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

### 6. Verify Recovery
```bash
# Test MySQL connection
mysql -u foi_user -p

# Check databases
SHOW DATABASES;

# Verify data
USE foi_archive;
SHOW TABLES;
SELECT COUNT(*) FROM documents;
```

### 7. Update Application Configuration
If recovering to local MySQL, update `/opt/foi-archive/.env`:
```
DATABASE_TYPE=local
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=foi_user
MYSQL_PASSWORD=***REMOVED***
MYSQL_DATABASE=foi_archive
DATABASE_URL=mysql+pymysql://foi_user:***REMOVED***@localhost:3306/foi_archive
```

### 8. Restart Application
```bash
sudo systemctl restart foi-archive
```

## Important Notes

- This recovery should only be used as a last resort
- The backup was created at: {datetime.now().isoformat()}
- Always verify data integrity after recovery
- Consider this backup as your final safety net

## Support

If you encounter issues during recovery:
1. Check the log file: {self.log_file}
2. Verify backup integrity: `tar -tzf {backup_path} | head -20`
3. Ensure sufficient disk space for extraction
"""

            with open(recovery_file, 'w') as f:
                f.write(instructions)
            
            self.log(f"✅ Recovery instructions saved: {recovery_file}")
            return recovery_file
            
        except Exception as e:
            self.log(f"❌ Failed to create recovery instructions: {e}", "ERROR")
            return None
    
    def create_deletion_report(self, deleted_dirs, failed_deletions, space_freed, backup_path, recovery_file):
        """Create a detailed deletion report."""
        report = {
            'deletion_timestamp': self.timestamp,
            'deletion_date': datetime.now().isoformat(),
            'operation': 'mysql_data_deletion',
            'success': len(failed_deletions) == 0,
            'deleted_directories': deleted_dirs,
            'failed_deletions': failed_deletions,
            'space_freed_bytes': space_freed,
            'space_freed_mb': space_freed / (1024 * 1024),
            'space_freed_gb': space_freed / (1024 * 1024 * 1024),
            'final_backup': str(backup_path) if backup_path else None,
            'recovery_instructions': recovery_file,
            'log_file': self.log_file,
            'notes': 'MySQL data deleted after successful migration to EXOscale DBaaS'
        }
        
        report_file = f"mysql_deletion_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📋 Deletion report saved: {report_file}")
        return report_file
    
    def run_deletion_sequence(self, remove_package=False):
        """Execute the complete MySQL data deletion sequence."""
        self.log("🚀 Starting MySQL data deletion sequence...")
        self.log("⚠️ THIS IS A DESTRUCTIVE OPERATION")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.log("❌ Prerequisites check failed - aborting deletion", "ERROR")
            return False
        
        # Step 2: Calculate space to be freed
        space_to_free = self.calculate_space_to_be_freed()
        
        # Step 3: Create final backup
        backup_path = self.create_final_backup()
        if not backup_path:
            self.log("❌ Final backup failed - aborting deletion", "ERROR")
            return False
        
        # Step 4: Final confirmation
        self.log("⚠️ FINAL CONFIRMATION REQUIRED")
        self.log("You are about to PERMANENTLY DELETE local MySQL data.")
        self.log(f"Space to be freed: {space_to_free / (1024*1024):.1f} MB")
        self.log(f"Backup created at: {backup_path}")
        
        # Step 5: Delete MySQL data
        deleted_dirs, failed_deletions = self.delete_mysql_data()
        
        # Step 6: Optionally remove package
        if remove_package:
            self.remove_mysql_package(remove_package=True)
        
        # Step 7: Create recovery instructions
        recovery_file = self.create_recovery_instructions(backup_path)
        
        # Step 8: Create final report
        self.create_deletion_report(deleted_dirs, failed_deletions, space_to_free, backup_path, recovery_file)
        
        # Summary
        if len(failed_deletions) == 0:
            self.log("🎉 MySQL data deletion completed successfully!")
            self.log("")
            self.log("📁 Files created:")
            self.log(f"   📦 Final backup: {backup_path}")
            self.log(f"   📋 Recovery instructions: {recovery_file}")
            self.log(f"   📊 Log file: {self.log_file}")
            self.log("")
            self.log("💡 What was deleted:")
            for directory in deleted_dirs:
                self.log(f"   🗑️ {directory}")
            self.log("")
            self.log(f"💾 Disk space freed: {space_to_free / (1024*1024):.1f} MB")
            self.log("")
            self.log("⚠️ IMPORTANT:")
            self.log("   • Local MySQL data has been permanently deleted")
            self.log("   • Application should continue using EXOscale database")
            self.log("   • Keep the backup and recovery files safe")
            self.log("   • Monitor application performance closely")
            
            return True
        else:
            self.log("❌ MySQL data deletion completed with errors", "ERROR")
            self.log("Failed to delete:")
            for directory in failed_deletions:
                self.log(f"   ❌ {directory}")
            return False

def main():
    """Main deletion process."""
    parser = argparse.ArgumentParser(description='Delete local MySQL data after EXOscale migration')
    parser.add_argument('--confirm', action='store_true', help='Confirm that you want to delete MySQL data')
    parser.add_argument('--i-understand-this-is-permanent', action='store_true', help='Acknowledge permanent deletion')
    parser.add_argument('--remove-package', action='store_true', help='Also remove MySQL package')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without deleting')
    
    args = parser.parse_args()
    
    if not args.confirm or not args.i_understand_this_is_permanent:
        if not args.dry_run:
            print("❌ This script will PERMANENTLY DELETE local MySQL data!")
            print("")
            print("🚨 CRITICAL WARNING:")
            print("   This operation CANNOT be undone easily!")
            print("   Only proceed if you are ABSOLUTELY CERTAIN that:")
            print("")
            print("   ✅ EXOscale database migration was successful")
            print("   ✅ Application has been running on EXOscale for at least 1 week")
            print("   ✅ All features have been tested thoroughly")
            print("   ✅ Multiple recent backups exist and are verified")
            print("   ✅ MySQL service has been disabled")
            print("   ✅ All stakeholders have approved this action")
            print("")
            print("To proceed, run:")
            print("python3 delete_local_database_data.py --confirm --i-understand-this-is-permanent")
            print("")
            print("To test without changes:")
            print("python3 delete_local_database_data.py --dry-run")
            sys.exit(1)
    
    # Create deleter
    deleter = LocalMySQLDataDeleter()
    
    if args.dry_run:
        print("🧪 DRY RUN - No data will be deleted")
        print("")
        deleter.log("📊 DRY RUN: Checking prerequisites...")
        
        prereqs_ok = deleter.check_prerequisites()
        space_to_free = deleter.calculate_space_to_be_freed()
        
        print("")
        print("📊 Deletion Summary (DRY RUN):")
        print(f"   Prerequisites: {'✅ Passed' if prereqs_ok else '❌ Failed'}")
        print(f"   Space to free: {space_to_free / (1024*1024):.1f} MB")
        print(f"   MySQL data dir: {deleter.mysql_data_dir}")
        print(f"   MySQL config dir: {deleter.mysql_config_dir} (preserved)")
        print("")
        
        if prereqs_ok:
            print("✅ System appears ready for data deletion")
            print("   Run with --confirm --i-understand-this-is-permanent to proceed")
        else:
            print("⚠️ System is not ready for data deletion")
            print("   Fix prerequisite issues before proceeding")
        
        sys.exit(0)
    
    # Final safety check
    print("🚨 FINAL SAFETY CHECK")
    print("You are about to permanently delete local MySQL data.")
    print("Type 'DELETE ALL MYSQL DATA' to confirm:")
    confirmation = input().strip()
    
    if confirmation != 'DELETE ALL MYSQL DATA':
        print("❌ Confirmation failed - operation cancelled")
        sys.exit(1)
    
    # Run the deletion sequence
    try:
        success = deleter.run_deletion_sequence(remove_package=args.remove_package)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 MySQL data deletion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ MySQL data deletion failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 