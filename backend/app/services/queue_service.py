"""
Queue Service for managing document processing jobs.
Uses database-backed queue with FIFO ordering.
"""
import structlog
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.database.models import JobQueue, Document
from datetime import datetime

logger = structlog.get_logger()

class QueueService:
    """Service for managing document processing job queue."""
    
    MAX_QUEUE_SIZE = 100
    
    @staticmethod
    def enqueue_job(
        db: Session,
        document_id: int,
        job_type: str = 'process_document',
        priority: int = 0
    ) -> Optional[JobQueue]:
        """
        Add a job to the queue.
        
        Args:
            db: Database session
            document_id: ID of document to process
            job_type: Type of job (default: 'process_document')
            priority: Priority (higher = processed first, default: 0 for FIFO)
        
        Returns:
            JobQueue instance or None if queue is full
        """
        # Check queue size
        pending_count = db.query(JobQueue).filter(
            JobQueue.status.in_(['pending', 'processing'])
        ).count()
        
        if pending_count >= QueueService.MAX_QUEUE_SIZE:
            logger.warning(
                "Queue is full, rejecting new job",
                document_id=document_id,
                queue_size=pending_count
            )
            return None
        
        # Check if job already exists for this document
        existing_job = db.query(JobQueue).filter(
            and_(
                JobQueue.document_id == document_id,
                JobQueue.status.in_(['pending', 'processing'])
            )
        ).first()
        
        if existing_job:
            logger.info(
                "Job already exists for document",
                document_id=document_id,
                job_id=existing_job.id
            )
            return existing_job
        
        # Create new job
        job = JobQueue(
            document_id=document_id,
            job_type=job_type,
            status='pending',
            priority=priority
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(
            "Job enqueued",
            job_id=job.id,
            document_id=document_id,
            queue_position=QueueService.get_queue_position(db, job.id)
        )
        
        return job
    
    @staticmethod
    def get_next_job(db: Session) -> Optional[JobQueue]:
        """
        Get the next job to process (FIFO order).
        
        Returns:
            Next JobQueue instance or None if no jobs available
        """
        job = db.query(JobQueue).filter(
            JobQueue.status == 'pending'
        ).order_by(
            JobQueue.priority.desc(),
            JobQueue.created_at.asc()
        ).first()
        
        if job:
            job.status = 'processing'
            job.started_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
            
            logger.info("Job started processing", job_id=job.id, document_id=job.document_id)
        
        return job
    
    @staticmethod
    def update_job_progress(
        db: Session,
        job_id: int,
        current_step: Optional[str] = None,
        progress_percent: Optional[int] = None
    ) -> bool:
        """Update job progress."""
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return False
        
        if current_step:
            job.current_step = current_step
        if progress_percent is not None:
            job.progress_percent = min(100, max(0, progress_percent))
        
        db.commit()
        return True
    
    @staticmethod
    def complete_job(db: Session, job_id: int) -> bool:
        """Mark job as completed."""
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return False
        
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.progress_percent = 100
        
        db.commit()
        logger.info("Job completed", job_id=job_id, document_id=job.document_id)
        return True
    
    @staticmethod
    def fail_job(
        db: Session,
        job_id: int,
        error_message: str,
        retry: bool = True
    ) -> bool:
        """Mark job as failed, optionally retry."""
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return False
        
        job.retry_count += 1
        
        if retry and job.retry_count < job.max_retries:
            # Retry: reset to pending
            job.status = 'pending'
            job.current_step = None
            job.progress_percent = 0
            logger.info(
                "Job failed, retrying",
                job_id=job_id,
                retry_count=job.retry_count,
                error=error_message[:200]
            )
        else:
            # Max retries reached or no retry
            job.status = 'failed'
            job.failed_at = datetime.utcnow()
            job.error_message = error_message
            logger.error(
                "Job failed permanently",
                job_id=job_id,
                document_id=job.document_id,
                retry_count=job.retry_count,
                error=error_message[:200]
            )
        
        db.commit()
        return True
    
    @staticmethod
    def get_job_status(db: Session, job_id: int) -> Optional[Dict]:
        """Get job status by ID."""
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return None
        
        return job.to_dict()
    
    @staticmethod
    def get_job_by_document_id(db: Session, document_id: int) -> Optional[JobQueue]:
        """Get job by document ID."""
        return db.query(JobQueue).filter(
            JobQueue.document_id == document_id
        ).order_by(JobQueue.created_at.desc()).first()
    
    @staticmethod
    def get_queue_position(db: Session, job_id: int) -> int:
        """Get position in queue (1-based)."""
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return -1
        
        # Count jobs ahead in queue (same or higher priority, created earlier)
        position = db.query(func.count(JobQueue.id)).filter(
            and_(
                JobQueue.status == 'pending',
                JobQueue.priority >= job.priority,
                JobQueue.created_at <= job.created_at,
                JobQueue.id != job_id
            )
        ).scalar() or 0
        
        return position + 1
    
    @staticmethod
    def get_failed_jobs(db: Session, limit: int = 100) -> List[JobQueue]:
        """Get failed jobs for admin review."""
        return db.query(JobQueue).filter(
            JobQueue.status == 'failed'
        ).order_by(JobQueue.failed_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_queue_stats(db: Session) -> Dict:
        """Get queue statistics."""
        stats = {
            'pending': db.query(func.count(JobQueue.id)).filter(
                JobQueue.status == 'pending'
            ).scalar() or 0,
            'processing': db.query(func.count(JobQueue.id)).filter(
                JobQueue.status == 'processing'
            ).scalar() or 0,
            'completed': db.query(func.count(JobQueue.id)).filter(
                JobQueue.status == 'completed'
            ).scalar() or 0,
            'failed': db.query(func.count(JobQueue.id)).filter(
                JobQueue.status == 'failed'
            ).scalar() or 0,
            'total': db.query(func.count(JobQueue.id)).scalar() or 0
        }
        return stats

# Singleton instance
queue_service = QueueService()

