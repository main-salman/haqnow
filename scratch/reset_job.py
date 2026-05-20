import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def reset_job(job_id: int):
    db = SessionLocal()
    try:
        print(f"Resetting job {job_id} to pending...")
        
        # We will reset status to 'pending', started_at/completed_at/failed_at to None,
        # progress_percent to 0, current_step to None, and error_message to None
        result = db.execute(text("""
            UPDATE job_queue
            SET status = 'pending',
                started_at = NULL,
                completed_at = NULL,
                failed_at = NULL,
                progress_percent = 0,
                current_step = NULL,
                error_message = NULL
            WHERE id = :job_id
        """), {"job_id": job_id})
        
        db.commit()
        print(f"Job {job_id} successfully reset to pending! Rows affected: {result.rowcount}")
        
    except Exception as e:
        db.rollback()
        print(f"Error resetting job: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_job(95)
