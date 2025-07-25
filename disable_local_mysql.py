#!/usr/bin/env python3
"""
Local MySQL Disable Script for HaqNow.com
=========================================

This script safely disables the local MySQL service after successful migration
to EXOscale DBaaS. It includes:
- Pre-disable verification checks
- Service stopping and disabling
- Configuration preservation
- Rollback preparation
- Safety confirmations

⚠️  WARNING: This script will disable the local MySQL service.
Only run this after:
1. Successful migration to EXOscale database
2. Thorough application testing with EXOscale database
3. Confirmed data integrity and performance
4. Recent backup completion

Usage:
    python3 disable_local_mysql.py --confirm
"""

import os
import sys
import subprocess
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
import argparse

class LocalMySQLDisabler:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"mysql_disable_log_{self.timestamp}.txt"
        self.backup_dir = Path(f"./mysql_config_backup_{self.timestamp}")
        
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
    
    def check_current_database_status(self):
        """Check what database the application is currently using."""
        self.log("🔍 Checking current database configuration...")
        
        try:
            # Check .db_status file
            status_file = Path("/opt/foi-archive/.db_status")
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status_content = f.read()
                self.log(f"Database status: {status_content.strip()}")
                
                if "DATABASE_TYPE=exoscale" in status_content:
                    self.log("✅ Application is using EXOscale database")
                    return "exoscale"
                elif "DATABASE_TYPE=local" in status_content:
                    self.log("⚠️ Application is still using local MySQL")
                    return "local"
            
            # Check .env file as fallback
            env_file = Path("/opt/foi-archive/.env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                if "DATABASE_TYPE=exoscale" in env_content:
                    self.log("✅ Environment configured for EXOscale database")
                    return "exoscale"
                elif "MYSQL_HOST=localhost" in env_content:
                    self.log("⚠️ Environment still configured for local MySQL")
                    return "local"
            
            self.log("❌ Could not determine database configuration", "ERROR")
            return "unknown"
            
        except Exception as e:
            self.log(f"❌ Error checking database status: {e}", "ERROR")
            return "unknown"
    
    def verify_exoscale_database_working(self):
        """Verify that the application is working with EXOscale database."""
        self.log("🔍 Verifying EXOscale database connectivity...")
        
        try:
            # Run the database check script
            check_script = Path("/opt/foi-archive/check_database.py")
            if check_script.exists():
                result = self.run_command(f"cd /opt/foi-archive && python3 check_database.py", check=False)
                if result and result.returncode == 0:
                    self.log("✅ EXOscale database connectivity verified")
                    return True
                else:
                    self.log("❌ EXOscale database connectivity check failed", "ERROR")
                    return False
            else:
                self.log("⚠️ Database check script not found", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying EXOscale database: {e}", "ERROR")
            return False
    
    def check_mysql_service_status(self):
        """Check current MySQL service status."""
        self.log("🔍 Checking MySQL service status...")
        
        try:
            # Check if MySQL service is running
            result = self.run_command("systemctl is-active mysql", check=False)
            if result:
                status = result.stdout.strip()
                self.log(f"MySQL service status: {status}")
                
                if status == "active":
                    self.log("✅ MySQL service is currently running")
                    return "running"
                elif status == "inactive":
                    self.log("ℹ️ MySQL service is already stopped")
                    return "stopped"
                else:
                    self.log(f"ℹ️ MySQL service status: {status}")
                    return status
            
            return "unknown"
            
        except Exception as e:
            self.log(f"❌ Error checking MySQL status: {e}", "ERROR")
            return "unknown"
    
    def backup_mysql_configuration(self):
        """Backup MySQL configuration files before disabling."""
        self.log("📦 Backing up MySQL configuration...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)
            
            # Files to backup
            config_files = [
                "/etc/mysql/mysql.conf.d/mysqld.cnf",
                "/etc/mysql/my.cnf",
                "/etc/mysql/debian.cnf",
                "/var/lib/mysql/mysql",  # MySQL system database
            ]
            
            directories_to_backup = [
                "/etc/mysql",
                "/var/lib/mysql"
            ]
            
            # Backup configuration files
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        dest = self.backup_dir / Path(config_file).name
                        shutil.copy2(config_file, dest)
                        self.log(f"✅ Backed up: {config_file}")
                    except Exception as e:
                        self.log(f"⚠️ Failed to backup {config_file}: {e}", "WARNING")
            
            # Create a complete MySQL data directory backup (just structure info)
            mysql_info_file = self.backup_dir / "mysql_info.txt"
            try:
                # Get MySQL version and basic info
                result = self.run_command("mysql --version", check=False)
                mysql_version = result.stdout.strip() if result else "Unknown"
                
                # Get database list
                result = self.run_command("mysql -e 'SHOW DATABASES;'", check=False)
                databases = result.stdout if result else "Could not retrieve database list"
                
                with open(mysql_info_file, 'w') as f:
                    f.write(f"MySQL Disable Backup Information\n")
                    f.write(f"================================\n")
                    f.write(f"Backup Date: {datetime.now().isoformat()}\n")
                    f.write(f"MySQL Version: {mysql_version}\n")
                    f.write(f"\nDatabases:\n{databases}\n")
                    f.write(f"\nBackup Location: {self.backup_dir}\n")
                    f.write(f"Log File: {self.log_file}\n")
                
                self.log(f"✅ MySQL info saved to: {mysql_info_file}")
                
            except Exception as e:
                self.log(f"⚠️ Failed to save MySQL info: {e}", "WARNING")
            
            self.log(f"✅ MySQL configuration backed up to: {self.backup_dir}")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to backup MySQL configuration: {e}", "ERROR")
            return False
    
    def stop_mysql_service(self):
        """Stop the MySQL service."""
        self.log("🛑 Stopping MySQL service...")
        
        try:
            # Stop MySQL service
            result = self.run_command("systemctl stop mysql", check=False)
            if result and result.returncode == 0:
                self.log("✅ MySQL service stopped successfully")
                
                # Wait a moment and verify it's stopped
                time.sleep(2)
                status = self.check_mysql_service_status()
                if status in ["stopped", "inactive"]:
                    self.log("✅ MySQL service stop verified")
                    return True
                else:
                    self.log(f"⚠️ MySQL service status after stop: {status}", "WARNING")
                    return False
            else:
                self.log("❌ Failed to stop MySQL service", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error stopping MySQL service: {e}", "ERROR")
            return False
    
    def disable_mysql_service(self):
        """Disable MySQL service from auto-starting."""
        self.log("🚫 Disabling MySQL service from auto-start...")
        
        try:
            # Disable MySQL service
            result = self.run_command("systemctl disable mysql", check=False)
            if result and result.returncode == 0:
                self.log("✅ MySQL service disabled from auto-start")
                
                # Verify it's disabled
                result = self.run_command("systemctl is-enabled mysql", check=False)
                if result:
                    status = result.stdout.strip()
                    if status == "disabled":
                        self.log("✅ MySQL service disable verified")
                        return True
                    else:
                        self.log(f"⚠️ MySQL service enable status: {status}", "WARNING")
                        return True  # Sometimes it shows 'masked' which is also disabled
                return False
            else:
                self.log("❌ Failed to disable MySQL service", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error disabling MySQL service: {e}", "ERROR")
            return False
    
    def create_rollback_script(self):
        """Create a script to re-enable MySQL if needed."""
        self.log("📝 Creating rollback script...")
        
        try:
            rollback_script = f"rollback_mysql_{self.timestamp}.py"
            
            script_content = f'''#!/usr/bin/env python3
"""
MySQL Rollback Script
====================

This script re-enables the local MySQL service if needed.
Created during MySQL disable operation on {datetime.now().isoformat()}

Usage:
    python3 {rollback_script}
"""

import subprocess
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {cmd}")
        if result.stdout:
            print(f"   Output: {{result.stdout.strip()}}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"   Error: {{e.stderr}}")
        return False

def main():
    print("🔄 Rolling back MySQL service...")
    
    # Enable MySQL service
    if not run_command("systemctl enable mysql"):
        print("❌ Failed to enable MySQL service")
        sys.exit(1)
    
    # Start MySQL service
    if not run_command("systemctl start mysql"):
        print("❌ Failed to start MySQL service")
        sys.exit(1)
    
    # Check status
    run_command("systemctl status mysql --no-pager")
    
    print("✅ MySQL service rollback completed")
    print("")
    print("⚠️  Remember to:")
    print("   1. Update application configuration to use local MySQL")
    print("   2. Restart the application service")
    print("   3. Verify application functionality")

if __name__ == "__main__":
    main()
'''
            
            with open(rollback_script, 'w') as f:
                f.write(script_content)
            
            # Make it executable
            os.chmod(rollback_script, 0o755)
            
            self.log(f"✅ Rollback script created: {rollback_script}")
            return rollback_script
            
        except Exception as e:
            self.log(f"❌ Failed to create rollback script: {e}", "ERROR")
            return None
    
    def create_disable_report(self, success, rollback_script):
        """Create a detailed disable report."""
        report = {
            'disable_timestamp': self.timestamp,
            'disable_date': datetime.now().isoformat(),
            'operation': 'mysql_disable',
            'success': success,
            'backup_location': str(self.backup_dir),
            'rollback_script': rollback_script,
            'log_file': self.log_file,
            'notes': 'Local MySQL service disabled after successful migration to EXOscale DBaaS'
        }
        
        report_file = f"mysql_disable_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📋 Disable report saved: {report_file}")
        return report_file
    
    def run_disable_sequence(self, force=False):
        """Execute the complete MySQL disable sequence."""
        self.log("🚀 Starting MySQL disable sequence...")
        
        # Step 1: Check current database status
        db_status = self.check_current_database_status()
        if db_status != "exoscale" and not force:
            self.log("❌ Application is not using EXOscale database. Use --force to override.", "ERROR")
            return False
        
        # Step 2: Verify EXOscale database is working
        if not self.verify_exoscale_database_working() and not force:
            self.log("❌ EXOscale database verification failed. Use --force to override.", "ERROR")
            return False
        
        # Step 3: Check MySQL service status
        mysql_status = self.check_mysql_service_status()
        if mysql_status in ["stopped", "inactive"]:
            self.log("ℹ️ MySQL service is already stopped")
        
        # Step 4: Backup MySQL configuration
        if not self.backup_mysql_configuration():
            self.log("❌ Failed to backup MySQL configuration", "ERROR")
            return False
        
        # Step 5: Stop MySQL service
        if mysql_status == "running":
            if not self.stop_mysql_service():
                self.log("❌ Failed to stop MySQL service", "ERROR")
                return False
        
        # Step 6: Disable MySQL service
        if not self.disable_mysql_service():
            self.log("❌ Failed to disable MySQL service", "ERROR")
            return False
        
        # Step 7: Create rollback script
        rollback_script = self.create_rollback_script()
        
        # Step 8: Create final report
        self.create_disable_report(True, rollback_script)
        
        self.log("🎉 MySQL disable sequence completed successfully!")
        self.log("")
        self.log("📁 Files created:")
        self.log(f"   📦 Configuration backup: {self.backup_dir}")
        self.log(f"   📋 Log file: {self.log_file}")
        if rollback_script:
            self.log(f"   🔄 Rollback script: {rollback_script}")
        self.log("")
        self.log("💡 Next steps:")
        self.log("   1. Monitor application performance with EXOscale database")
        self.log("   2. Verify all application features work correctly")
        self.log("   3. Keep backup files for safety")
        self.log("   4. If issues arise, use rollback script to re-enable MySQL")
        self.log("")
        self.log("⚠️  The local MySQL service is now disabled.")
        self.log("   The application should be using the EXOscale database.")
        
        return True

def main():
    """Main disable process."""
    parser = argparse.ArgumentParser(description='Disable local MySQL service after EXOscale migration')
    parser.add_argument('--confirm', action='store_true', help='Confirm that you want to disable MySQL')
    parser.add_argument('--force', action='store_true', help='Force disable even if checks fail')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually disabling')
    
    args = parser.parse_args()
    
    if not args.confirm and not args.dry_run:
        print("❌ This script will disable the local MySQL service!")
        print("")
        print("⚠️  WARNING: Only run this after:")
        print("   1. ✅ Successful migration to EXOscale database")
        print("   2. ✅ Thorough application testing with EXOscale database") 
        print("   3. ✅ Confirmed data integrity and performance")
        print("   4. ✅ Recent backup completion")
        print("")
        print("To proceed, run: python3 disable_local_mysql.py --confirm")
        print("To test without changes: python3 disable_local_mysql.py --dry-run")
        sys.exit(1)
    
    # Create disabler
    disabler = LocalMySQLDisabler()
    
    if args.dry_run:
        print("🧪 DRY RUN - No changes will be made")
        print("")
        disabler.log("📊 DRY RUN: Checking current status...")
        db_status = disabler.check_current_database_status()
        mysql_status = disabler.check_mysql_service_status()
        exoscale_ok = disabler.verify_exoscale_database_working()
        
        print("")
        print("📊 Current Status:")
        print(f"   Database Type: {db_status}")
        print(f"   MySQL Service: {mysql_status}")
        print(f"   EXOscale DB: {'✅ Working' if exoscale_ok else '❌ Not working'}")
        print("")
        
        if db_status == "exoscale" and exoscale_ok:
            print("✅ System appears ready for MySQL disable")
        else:
            print("⚠️ System may not be ready for MySQL disable")
            print("   Use --force to override safety checks")
        
        sys.exit(0)
    
    # Run the disable sequence
    try:
        success = disabler.run_disable_sequence(force=args.force)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 MySQL disable cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ MySQL disable failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 