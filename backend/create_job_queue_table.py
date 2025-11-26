#!/usr/bin/env python3
"""
Migration script to create job_queue table for document processing queue.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import DATABASE_URL, fall back to environment variable
try:
    from app.database.database import DATABASE_URL
except ImportError:
    import os
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found. Set it in environment or ensure app.database.database is importable.")
        sys.exit(1)

def create_job_queue_table():
    """Create the job_queue table for document processing queue."""
    print("🔧 Creating job_queue table for document processing queue...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if job_queue table already exists
                result = conn.execute(text("SHOW TABLES LIKE 'job_queue'"))
                if result.fetchone():
                    print("ℹ️  job_queue table already exists, skipping creation")
                    trans.commit()
                    return
                
                print("📝 Creating job_queue table...")
                
                # Create the job_queue table
                create_table_sql = """
                CREATE TABLE job_queue (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id INT NOT NULL,
                    job_type VARCHAR(50) NOT NULL DEFAULT 'process_document',
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    priority INT NOT NULL DEFAULT 0,
                    current_step VARCHAR(100) NULL,
                    progress_percent INT NULL DEFAULT 0,
                    error_message TEXT NULL,
                    retry_count INT NOT NULL DEFAULT 0,
                    max_retries INT NOT NULL DEFAULT 3,
                    started_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    failed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_status (status),
                    INDEX idx_priority_status (priority DESC, status, created_at),
                    INDEX idx_document_id (document_id),
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
                
                conn.execute(text(create_table_sql))
                print("✅ Successfully created job_queue table")
                
                trans.commit()
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error creating job_queue table: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    create_job_queue_table()
    print("✅ Migration completed successfully!")

