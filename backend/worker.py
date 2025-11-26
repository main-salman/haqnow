#!/usr/bin/env python3
"""
Background worker for processing document jobs from the queue.
Runs continuously, polling for jobs and processing them.
"""
import os
import sys
import time
import signal
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.services.queue_service import queue_service
from app.apis.document_processing import process_document_internal
import structlog

logger = structlog.get_logger()

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received, finishing current job...")
    shutdown_requested = True

async def process_job(job):
    """Process a single job."""
    db = SessionLocal()
    try:
        logger.info(
            "Processing job",
            job_id=job.id,
            document_id=job.document_id,
            job_type=job.job_type
        )
        
        # Update progress: Starting
        queue_service.update_job_progress(
            db,
            job.id,
            current_step="Starting document processing",
            progress_percent=0
        )
        
        if job.job_type == 'process_document':
            # Update progress: Downloading file
            queue_service.update_job_progress(
                db,
                job.id,
                current_step="Downloading file from storage",
                progress_percent=10
            )
            
            # Update progress: OCR processing
            queue_service.update_job_progress(
                db,
                job.id,
                current_step="Extracting text with OCR",
                progress_percent=30
            )
            
            # Process document (async)
            result = await process_document_internal(job.document_id, db)
            
            if result:
                # Update progress: Generating tags
                queue_service.update_job_progress(
                    db,
                    job.id,
                    current_step="Generating tags and summary",
                    progress_percent=80
                )
                
                # Update progress: Finalizing
                queue_service.update_job_progress(
                    db,
                    job.id,
                    current_step="Finalizing",
                    progress_percent=95
                )
                
                # Mark job as completed
                queue_service.complete_job(db, job.id)
                logger.info(
                    "Job completed successfully",
                    job_id=job.id,
                    document_id=job.document_id
                )
                return True
            else:
                # Processing failed
                queue_service.fail_job(
                    db,
                    job.id,
                    "Document processing returned no result",
                    retry=True
                )
                return False
        else:
            logger.warning("Unknown job type", job_type=job.job_type)
            queue_service.fail_job(
                db,
                job.id,
                f"Unknown job type: {job.job_type}",
                retry=False
            )
            return False
            
    except Exception as e:
        logger.error(
            "Error processing job",
            job_id=job.id,
            document_id=job.document_id,
            error=str(e)
        )
        queue_service.fail_job(
            db,
            job.id,
            str(e),
            retry=True
        )
        return False
    finally:
        db.close()

async def worker_loop():
    """Main async worker loop."""
    global shutdown_requested
    
    logger.info("Document processing worker started")
    
    # Check database connection
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        sys.exit(1)
    finally:
        db.close()
    
    # Main processing loop
    while not shutdown_requested:
        db = SessionLocal()
        try:
            # Get next job
            job = queue_service.get_next_job(db)
            
            if job:
                # Process the job (async)
                await process_job(job)
                # Small delay after processing
                await asyncio.sleep(1)
            else:
                # No jobs available, wait before checking again
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error("Error in worker loop", error=str(e))
            await asyncio.sleep(5)
        finally:
            db.close()
    
    logger.info("Worker shutdown complete")

def main():
    """Main entry point."""
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run async worker loop
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error("Fatal error in worker", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()

