"""Migration script to create OTP codes table for multi-pod support."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_otp_table():
    """Create OTP codes table in MySQL database."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    # Create engine
    engine = create_engine(database_url, echo=True)
    
    # SQL to create OTP table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        code VARCHAR(10) NOT NULL,
        attempts INT NOT NULL DEFAULT 0,
        max_attempts INT NOT NULL DEFAULT 5,
        expires_at DATETIME NOT NULL,
        used BOOLEAN NOT NULL DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_expires_at (expires_at),
        INDEX idx_email_used (email, used)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ OTP codes table created successfully!")
            
            # Verify table exists
            result = conn.execute(text("SHOW TABLES LIKE 'otp_codes'"))
            if result.fetchone():
                print("✅ Table verified: otp_codes exists")
            else:
                print("❌ Table verification failed")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating OTP table: {e}")
        return False


if __name__ == "__main__":
    success = create_otp_table()
    sys.exit(0 if success else 1)

