#!/usr/bin/env python3
"""
Migration script to create the collaborators table.
This script should be run once to set up the collaborators/champions system.
"""

import os
import sys
from sqlalchemy import create_engine

# Add the current directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DATABASE_URL
from app.database.models import Base, Collaborator

def main():
    """Create the collaborators table."""
    print("🔧 Creating collaborators table...")
    
    # Get database URL
    database_url = DATABASE_URL
    engine = create_engine(database_url)
    
    # Create tables
    print("📋 Creating collaborators table...")
    Base.metadata.create_all(bind=engine, tables=[Collaborator.__table__])
    
    print("✅ Successfully created collaborators table!")
    print("")
    print("🎯 Next steps:")
    print("   1. Use the admin dashboard to add collaborators/champions")
    print("   2. Upload logos and add descriptions for each partner")
    print("   3. Set priority (1-10) to control display order")

if __name__ == "__main__":
    main()

