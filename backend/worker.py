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
from app.database import Document
# NOTE: rag_service import removed - it loads PyTorch + transformers (~1GB)
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
            
            # Force garbage collection to free Tesseract/OCR PDF image memory immediately
            import gc
            gc.collect()
            
            # Refresh document to get latest state after processing
            document = db.query(Document).filter(Document.id == job.document_id).first()
            if document:
                db.refresh(document)
            
            if result:
                # Verify document was actually updated
                if document and document.ocr_text and document.ocr_text.strip():
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
                        document_id=job.document_id,
                        ocr_length=len(document.ocr_text) if document.ocr_text else 0,
                        has_summary=bool(document.ai_summary)
                    )
                    
                    # NOTE: RAG indexing skipped in worker to prevent OOM.
                    # The all-MiniLM-L6-v2 model + PyTorch (~1GB) exceeds the
                    # worker's 2Gi limit when combined with OCR + AI summary.
                    # RAG indexing happens lazily when users access documents.
                    logger.info("Skipping RAG indexing in worker to prevent OOM",
                               document_id=job.document_id)
                        
                    return True
                else:
                    # Processing returned result but document wasn't updated
                    logger.warning(
                        "Processing returned result but document not updated",
                        job_id=job.id,
                        document_id=job.document_id
                    )
                    queue_service.fail_job(
                        db,
                        job.id,
                        "Document processing completed but document not updated in database",
                        retry=True
                    )
                    return False
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
    
    # Recover any stale jobs on startup (handles pod restart during processing)
    db = SessionLocal()
    try:
        recovered = queue_service.recover_stale_jobs(db, timeout_minutes=10)
        if recovered > 0:
            logger.info("Recovered stale jobs on startup", count=recovered)
        else:
            logger.info("No stale jobs found on startup")
    except Exception as e:
        logger.error("Error recovering stale jobs on startup", error=str(e))
    finally:
        db.close()
    
    # Track time for periodic stale job recovery
    import time as _time
    last_recovery_check = _time.time()
    RECOVERY_INTERVAL_SECONDS = 300  # Check every 5 minutes
    
    # Main processing loop
    while not shutdown_requested:
        db = SessionLocal()
        try:
            # Periodic stale job recovery
            now = _time.time()
            if now - last_recovery_check >= RECOVERY_INTERVAL_SECONDS:
                try:
                    recovered = queue_service.recover_stale_jobs(db, timeout_minutes=10)
                    if recovered > 0:
                        logger.info("Periodic stale job recovery", count=recovered)
                except Exception as e:
                    logger.error("Error in periodic stale job recovery", error=str(e))
                last_recovery_check = now
            
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

