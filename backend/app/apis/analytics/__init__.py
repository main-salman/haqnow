"""Analytics API endpoints for admin dashboard - upload stats, document metrics, etc."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from ...database.database import get_db
from ...database.models import Document, DocumentComment, RAGQuery, JobQueue
from ...auth.jwt_auth import get_current_user, User

logger = structlog.get_logger()

router = APIRouter()


# Pydantic models for API responses
class TimeSeriesDataPoint(BaseModel):
    date: str
    count: int


class UploadStats(BaseModel):
    total_uploads: int
    uploads_today: int
    uploads_this_week: int
    uploads_this_month: int
    uploads_by_day: List[TimeSeriesDataPoint]
    uploads_by_week: List[TimeSeriesDataPoint]
    uploads_by_month: List[TimeSeriesDataPoint]


class DocumentStatusStats(BaseModel):
    total_documents: int
    pending: int
    approved: int
    rejected: int
    processed: int


class EngagementStats(BaseModel):
    total_views: int
    total_comments: int
    comments_pending: int
    comments_approved: int
    total_rag_queries: int
    avg_rag_response_time_ms: Optional[float]


class CountryUploadStat(BaseModel):
    country: str
    count: int


class LanguageUploadStat(BaseModel):
    language: str
    count: int


class ProcessingStats(BaseModel):
    jobs_pending: int
    jobs_processing: int
    jobs_completed: int
    jobs_failed: int
    avg_processing_time_seconds: Optional[float]


class AdminAnalyticsSummary(BaseModel):
    upload_stats: UploadStats
    document_status: DocumentStatusStats
    engagement: EngagementStats
    uploads_by_country: List[CountryUploadStat]
    uploads_by_language: List[LanguageUploadStat]
    processing_stats: ProcessingStats
    generated_at: str


def get_date_range_filter(days: int):
    """Get datetime filter for the last N days."""
    return datetime.utcnow() - timedelta(days=days)


@router.get("/summary", response_model=AdminAnalyticsSummary)
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics summary for admin dashboard."""
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        # === Upload Statistics ===
        total_uploads = db.query(func.count(Document.id)).scalar() or 0
        
        uploads_today = db.query(func.count(Document.id)).filter(
            Document.created_at >= today_start
        ).scalar() or 0
        
        uploads_this_week = db.query(func.count(Document.id)).filter(
            Document.created_at >= week_start
        ).scalar() or 0
        
        uploads_this_month = db.query(func.count(Document.id)).filter(
            Document.created_at >= month_start
        ).scalar() or 0
        
        # Uploads by day (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        uploads_by_day_raw = db.query(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.created_at >= thirty_days_ago
        ).group_by(
            func.date(Document.created_at)
        ).order_by(
            func.date(Document.created_at)
        ).all()
        
        uploads_by_day = [
            TimeSeriesDataPoint(date=str(row.date), count=row.count)
            for row in uploads_by_day_raw
        ]
        
        # Uploads by week (last 12 weeks)
        twelve_weeks_ago = now - timedelta(weeks=12)
        uploads_by_week_raw = db.query(
            func.yearweek(Document.created_at).label('yearweek'),
            func.count(Document.id).label('count')
        ).filter(
            Document.created_at >= twelve_weeks_ago
        ).group_by(
            func.yearweek(Document.created_at)
        ).order_by(
            func.yearweek(Document.created_at)
        ).all()
        
        uploads_by_week = [
            TimeSeriesDataPoint(date=str(row.yearweek), count=row.count)
            for row in uploads_by_week_raw
        ]
        
        # Uploads by month (last 12 months)
        twelve_months_ago = now - timedelta(days=365)
        uploads_by_month_raw = db.query(
            func.date_format(Document.created_at, '%Y-%m').label('month'),
            func.count(Document.id).label('count')
        ).filter(
            Document.created_at >= twelve_months_ago
        ).group_by(
            func.date_format(Document.created_at, '%Y-%m')
        ).order_by(
            func.date_format(Document.created_at, '%Y-%m')
        ).all()
        
        uploads_by_month = [
            TimeSeriesDataPoint(date=str(row.month), count=row.count)
            for row in uploads_by_month_raw
        ]
        
        upload_stats = UploadStats(
            total_uploads=total_uploads,
            uploads_today=uploads_today,
            uploads_this_week=uploads_this_week,
            uploads_this_month=uploads_this_month,
            uploads_by_day=uploads_by_day,
            uploads_by_week=uploads_by_week,
            uploads_by_month=uploads_by_month
        )
        
        # === Document Status Statistics ===
        status_counts = db.query(
            Document.status,
            func.count(Document.id).label('count')
        ).group_by(Document.status).all()
        
        status_dict = {row.status: row.count for row in status_counts}
        
        processed_count = db.query(func.count(Document.id)).filter(
            Document.processed_at.isnot(None)
        ).scalar() or 0
        
        document_status = DocumentStatusStats(
            total_documents=total_uploads,
            pending=status_dict.get('pending', 0),
            approved=status_dict.get('approved', 0),
            rejected=status_dict.get('rejected', 0),
            processed=processed_count
        )
        
        # === Engagement Statistics ===
        total_views = db.query(func.sum(Document.view_count)).scalar() or 0
        
        total_comments = db.query(func.count(DocumentComment.id)).scalar() or 0
        
        comments_pending = db.query(func.count(DocumentComment.id)).filter(
            DocumentComment.status == 'pending'
        ).scalar() or 0
        
        comments_approved = db.query(func.count(DocumentComment.id)).filter(
            DocumentComment.status == 'approved'
        ).scalar() or 0
        
        total_rag_queries = db.query(func.count(RAGQuery.id)).scalar() or 0
        
        avg_rag_response_time = db.query(
            func.avg(RAGQuery.response_time_ms)
        ).filter(
            RAGQuery.response_time_ms.isnot(None)
        ).scalar()
        
        engagement = EngagementStats(
            total_views=total_views,
            total_comments=total_comments,
            comments_pending=comments_pending,
            comments_approved=comments_approved,
            total_rag_queries=total_rag_queries,
            avg_rag_response_time_ms=float(avg_rag_response_time) if avg_rag_response_time else None
        )
        
        # === Uploads by Country ===
        country_stats = db.query(
            Document.country,
            func.count(Document.id).label('count')
        ).filter(
            Document.country.isnot(None)
        ).group_by(
            Document.country
        ).order_by(
            func.count(Document.id).desc()
        ).limit(20).all()
        
        uploads_by_country = [
            CountryUploadStat(country=row.country or "Unknown", count=row.count)
            for row in country_stats
        ]
        
        # === Uploads by Language ===
        language_stats = db.query(
            Document.document_language,
            func.count(Document.id).label('count')
        ).filter(
            Document.document_language.isnot(None)
        ).group_by(
            Document.document_language
        ).order_by(
            func.count(Document.id).desc()
        ).all()
        
        uploads_by_language = [
            LanguageUploadStat(language=row.document_language or "unknown", count=row.count)
            for row in language_stats
        ]
        
        # === Processing Statistics ===
        job_status_counts = db.query(
            JobQueue.status,
            func.count(JobQueue.id).label('count')
        ).group_by(JobQueue.status).all()
        
        job_status_dict = {row.status: row.count for row in job_status_counts}
        
        # Calculate average processing time for completed jobs
        avg_processing_time = db.query(
            func.avg(
                func.timestampdiff(
                    text('SECOND'),
                    JobQueue.started_at,
                    JobQueue.completed_at
                )
            )
        ).filter(
            JobQueue.status == 'completed',
            JobQueue.started_at.isnot(None),
            JobQueue.completed_at.isnot(None)
        ).scalar()
        
        processing_stats = ProcessingStats(
            jobs_pending=job_status_dict.get('pending', 0),
            jobs_processing=job_status_dict.get('processing', 0),
            jobs_completed=job_status_dict.get('completed', 0),
            jobs_failed=job_status_dict.get('failed', 0),
            avg_processing_time_seconds=float(avg_processing_time) if avg_processing_time else None
        )
        
        logger.info(
            "Analytics summary generated",
            total_uploads=total_uploads,
            total_views=total_views
        )
        
        return AdminAnalyticsSummary(
            upload_stats=upload_stats,
            document_status=document_status,
            engagement=engagement,
            uploads_by_country=uploads_by_country,
            uploads_by_language=uploads_by_language,
            processing_stats=processing_stats,
            generated_at=now.isoformat()
        )
        
    except Exception as e:
        logger.error("Error generating analytics summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating analytics summary: {str(e)}"
        )


@router.get("/uploads/daily")
async def get_daily_uploads(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily upload counts for the specified number of days."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.created_at >= start_date
        ).group_by(
            func.date(Document.created_at)
        ).order_by(
            func.date(Document.created_at)
        ).all()
        
        return {
            "data": [{"date": str(row.date), "count": row.count} for row in results],
            "period_days": days
        }
        
    except Exception as e:
        logger.error("Error fetching daily uploads", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads/by-status")
async def get_uploads_by_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get upload counts grouped by status."""
    try:
        results = db.query(
            Document.status,
            func.count(Document.id).label('count')
        ).group_by(Document.status).all()
        
        return {
            "data": [{"status": row.status, "count": row.count} for row in results]
        }
        
    except Exception as e:
        logger.error("Error fetching uploads by status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement/views")
async def get_view_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get view statistics for documents."""
    try:
        total_views = db.query(func.sum(Document.view_count)).scalar() or 0
        
        top_viewed = db.query(
            Document.id,
            Document.title,
            Document.view_count
        ).filter(
            Document.status == 'approved'
        ).order_by(
            Document.view_count.desc()
        ).limit(10).all()
        
        return {
            "total_views": total_views,
            "top_viewed_documents": [
                {"id": row.id, "title": row.title, "views": row.view_count}
                for row in top_viewed
            ]
        }
        
    except Exception as e:
        logger.error("Error fetching view stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

