#!/usr/bin/env python3
"""
Migration script to create the admins table and set up initial admin user.
This script should be run once to set up the admin management system.
Uses passwordless OTP authentication - no password required.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DATABASE_URL
from app.database.models import Base, Admin

def main():
    """Create the admins table and initial admin user."""
    print("🔧 Creating admins table and initial admin user...")
    
    # Get database URL
    database_url = DATABASE_URL
    engine = create_engine(database_url)
    
    # Create tables
    print("📋 Creating admins table...")
    Base.metadata.create_all(bind=engine, tables=[Admin.__table__])
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Check if we already have admins
        existing_admin = session.query(Admin).first()
        if existing_admin:
            print("⚠️  Admin table already has users. Skipping initial admin creation.")
            print(f"   Existing admin: {existing_admin.email}")
            return
        
        # Get admin email from environment
        admin_email = os.getenv("admin_email")
        
        if not admin_email:
            print("❌ Error: admin_email environment variable must be set.")
            print("   Please set this in your .env file or environment.")
            return
        
        # Create initial admin user (passwordless - uses OTP authentication)
        initial_admin = Admin(
            email=admin_email.lower().strip(),
            name="Super Administrator", 
            is_super_admin=True,
            is_active=True,
            created_by=None  # Initial admin has no creator
        )
        
        session.add(initial_admin)
        session.commit()
        
        print("✅ Successfully created admins table and initial admin user!")
        print(f"   📧 Admin email: {admin_email}")
        print(f"   🔐 Authentication: Passwordless OTP (email-based)")
        print(f"   👑 Super Admin: Yes")
        print("")
        print("🎯 Next steps:")
        print("   1. Log in to the admin panel using your email")
        print("   2. You'll receive an OTP code via email")
        print("   3. Enter the code to complete login")
        print("   4. Create additional admin users if needed")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 