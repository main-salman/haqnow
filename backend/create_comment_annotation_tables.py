#!/usr/bin/env python3
"""
Migration script to create comment, annotation, and banned words tables.
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

def create_tables():
    """Create comment, annotation, and banned words tables."""
    print("🔧 Creating comment, annotation, and banned words tables...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Create document_comments table
                print("📋 Creating document_comments table...")
                try:
                    conn.execute(text("""
                        CREATE TABLE document_comments (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            document_id INT NOT NULL,
                            parent_comment_id INT NULL,
                            comment_text TEXT NOT NULL,
                            session_id VARCHAR(64) NOT NULL,
                            status VARCHAR(20) NOT NULL DEFAULT 'pending',
                            flag_count INT NOT NULL DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_document_id (document_id),
                            INDEX idx_parent_comment_id (parent_comment_id),
                            INDEX idx_session_id (session_id),
                            INDEX idx_status (status),
                            INDEX idx_created_at (created_at),
                            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                            FOREIGN KEY (parent_comment_id) REFERENCES document_comments(id) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """))
                    print("✅ Created document_comments table")
                except Exception as e:
                    if "already exists" in str(e).lower() or "Duplicate table" in str(e):
                        print("ℹ️  document_comments table already exists")
                    else:
                        raise
                
                # Create document_annotations table
                print("📋 Creating document_annotations table...")
                try:
                    conn.execute(text("""
                        CREATE TABLE document_annotations (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            document_id INT NOT NULL,
                            session_id VARCHAR(64) NOT NULL,
                            page_number INT NOT NULL,
                            x FLOAT NOT NULL,
                            y FLOAT NOT NULL,
                            width FLOAT NOT NULL,
                            height FLOAT NOT NULL,
                            highlighted_text TEXT NULL,
                            annotation_note TEXT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_document_id (document_id),
                            INDEX idx_session_id (session_id),
                            INDEX idx_page_number (page_number),
                            INDEX idx_created_at (created_at),
                            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """))
                    print("✅ Created document_annotations table")
                except Exception as e:
                    if "already exists" in str(e).lower() or "Duplicate table" in str(e):
                        print("ℹ️  document_annotations table already exists")
                    else:
                        raise
                
                # Create banned_words table
                print("📋 Creating banned_words table...")
                try:
                    conn.execute(text("""
                        CREATE TABLE banned_words (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            word VARCHAR(200) NOT NULL UNIQUE,
                            reason TEXT NULL,
                            banned_by VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_word (word)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """))
                    print("✅ Created banned_words table")
                except Exception as e:
                    if "already exists" in str(e).lower() or "Duplicate table" in str(e):
                        print("ℹ️  banned_words table already exists")
                    else:
                        raise
                
                # Insert initial banned words
                print("📝 Inserting initial banned words...")
                initial_words = [
                    "fuck", "shit", "damn", "bitch", "asshole", "bastard",
                    "click here", "buy now", "free money", "make money fast",
                    "viagra", "casino", "lottery winner", "nigerian prince",
                    "kill yourself", "you should die", "hate you",
                ]
                
                for word in initial_words:
                    try:
                        conn.execute(text("""
                            INSERT INTO banned_words (word, reason, banned_by)
                            VALUES (:word, 'Initial best practices list', 'system')
                        """), {"word": word.lower()})
                    except Exception as e:
                        if "Duplicate entry" in str(e) or "UNIQUE constraint" in str(e):
                            pass  # Already exists
                        else:
                            print(f"⚠️  Warning: Could not insert '{word}': {e}")
                
                trans.commit()
                print("✅ Migration completed successfully!")
                return True
                
            except Exception as e:
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
    print("🔄 Starting comment/annotation tables migration...")
    success = create_tables()
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
