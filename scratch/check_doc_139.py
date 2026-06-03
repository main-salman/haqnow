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
        print(f"🔧 Resetting job {job_id} to pending...")
        
        # Reset the job state
        db.execute(text("""
            UPDATE job_queue 
            SET status = 'pending', 
                current_step = NULL, 
                progress_percent = 0, 
                started_at = NULL, 
                error_message = NULL, 
                retry_count = 0
            WHERE id = :job_id
        """), {"job_id": job_id})
        
        db.commit()
        print(f"✅ Successfully reset job {job_id} to pending!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting job: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_job(95)
