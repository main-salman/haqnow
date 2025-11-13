#!/usr/bin/env python3
"""
Migration script to add view tracking columns to documents table.
Adds:
- view_count: Integer column to track document views
- hidden_from_top_viewed: Boolean flag for admin control
"""

import sys
from sqlalchemy import text
from app.database.database import engine
import structlog

logger = structlog.get_logger()

def add_view_tracking_columns():
    """Add view_count and hidden_from_top_viewed columns to documents table."""
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'documents'
                AND COLUMN_NAME IN ('view_count', 'hidden_from_top_viewed')
            """))
            existing_count = result.fetchone()[0]
            
            if existing_count == 2:
                logger.info("View tracking columns already exist, skipping migration")
                return True
            
            # Add view_count column
            if existing_count == 0 or existing_count == 1:
                try:
                    conn.execute(text("""
                        ALTER TABLE documents
                        ADD COLUMN view_count INT NOT NULL DEFAULT 0
                    """))
                    logger.info("Added view_count column")
                except Exception as e:
                    if "Duplicate column name" not in str(e):
                        raise
                    logger.info("view_count column already exists")
                
                # Add hidden_from_top_viewed column
                try:
                    conn.execute(text("""
                        ALTER TABLE documents
                        ADD COLUMN hidden_from_top_viewed BOOLEAN NOT NULL DEFAULT FALSE
                    """))
                    logger.info("Added hidden_from_top_viewed column")
                except Exception as e:
                    if "Duplicate column name" not in str(e):
                        raise
                    logger.info("hidden_from_top_viewed column already exists")
            
            # Add indexes for performance
            try:
                conn.execute(text("""
                    CREATE INDEX idx_documents_view_count ON documents(view_count)
                """))
                logger.info("Added index on view_count")
            except Exception as e:
                if "Duplicate key name" not in str(e):
                    raise
                logger.info("Index on view_count already exists")
            
            try:
                conn.execute(text("""
                    CREATE INDEX idx_documents_hidden_from_top_viewed ON documents(hidden_from_top_viewed)
                """))
                logger.info("Added index on hidden_from_top_viewed")
            except Exception as e:
                if "Duplicate key name" not in str(e):
                    raise
                logger.info("Index on hidden_from_top_viewed already exists")
            
            conn.commit()
            logger.info("✅ View tracking migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting view tracking migration...")
    success = add_view_tracking_columns()
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)

