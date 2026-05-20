import sys
from sqlalchemy import text

from app.database.database import get_db
from app.database.models import JobQueue

print("Checking JobQueue for Document 139...")
db = next(get_db())
try:
    jobs = db.query(JobQueue).filter(JobQueue.document_id == 139).all()
    if jobs:
        print(f"Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"  ID: {job.id}")
            print(f"  Type: {job.job_type}")
            print(f"  Status: {job.status}")
            print(f"  Progress: {job.progress_percent}%")
            print(f"  Step: {job.current_step}")
            print(f"  Error: {job.error_message}")
            print(f"  Retries: {job.retry_count}/{job.max_retries}")
            print(f"  Created: {job.created_at}")
            print(f"  Started: {job.started_at}")
            print(f"  Completed: {job.completed_at}")
            print(f"  Failed: {job.failed_at}")
    else:
        print("No jobs found in JobQueue for Document 139.")
except Exception as e:
    print(f"Failed: {e}")
finally:
    db.close()
