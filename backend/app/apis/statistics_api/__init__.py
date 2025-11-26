from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
import os
import structlog

# Import database
from app.database import get_db, Document

logger = structlog.get_logger()

router = APIRouter()

# Pydantic Models
class CountryStat(BaseModel):
    country: str
    doc_count: int

class StateStat(BaseModel):
    state: str
    doc_count: int

class CountryStatsResponse(BaseModel):
    countries: List[CountryStat]
    total_countries: int
    total_documents: int

class StateStatsResponse(BaseModel):
    states: List[StateStat]
    country: str
    total_states: int
    total_documents: int

class GlobalStatsResponse(BaseModel):
    total_documents: int
    total_countries: int
    total_states: int
    approved_documents: int
    pending_documents: int
    processed_documents: int

@router.get("/country-stats", response_model=CountryStatsResponse)
async def get_country_stats(db: Session = Depends(get_db)):
    """Get document count statistics by country."""
    
    try:
        # Get all approved documents grouped by country
        # Deleted documents are permanently removed from DB, so they won't appear
        country_stats = db.query(
            Document.country,
            func.count(Document.id).label('doc_count')
        ).filter(
            Document.status == "approved"
        ).group_by(
            Document.country
        ).order_by(
            func.count(Document.id).desc()
        ).all()
        
        # Convert to response format
        countries = [
            CountryStat(country=stat.country or "Unknown", doc_count=stat.doc_count)
            for stat in country_stats
        ]
        
        total_documents = sum(country.doc_count for country in countries)
        
        logger.info("Country statistics retrieved successfully", 
                   total_countries=len(countries),
                   total_documents=total_documents)
        
        return CountryStatsResponse(
            countries=countries,
            total_countries=len(countries),
            total_documents=total_documents
        )
        
    except Exception as e:
        logger.error("Error retrieving country statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving country statistics"
        )

@router.get("/state-stats/{country}", response_model=StateStatsResponse)
async def get_state_stats(country: str, db: Session = Depends(get_db)):
    """Get document count statistics by state/province for a specific country."""
    
    try:
        # Get all approved documents for the specified country grouped by state
        # Deleted documents are permanently removed from DB, so they won't appear
        state_stats = db.query(
            Document.state,
            func.count(Document.id).label('doc_count')
        ).filter(
            Document.country == country,
            Document.status == "approved"
        ).group_by(
            Document.state
        ).order_by(
            func.count(Document.id).desc()
        ).all()
        
        # Convert to response format
        states = [
            StateStat(state=stat.state or "Unknown", doc_count=stat.doc_count)
            for stat in state_stats
        ]
        
        total_documents = sum(state.doc_count for state in states)
        
        logger.info("State statistics retrieved successfully", 
                   country=country,
                   total_states=len(states),
                   total_documents=total_documents)
        
        return StateStatsResponse(
            states=states,
            country=country,
            total_states=len(states),
            total_documents=total_documents
        )
        
    except Exception as e:
        logger.error("Error retrieving state statistics", country=country, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving state statistics"
        )

@router.get("/global-stats", response_model=GlobalStatsResponse)
async def get_global_stats(db: Session = Depends(get_db)):
    """Get global statistics for the platform."""
    
    try:
        # Get total documents count
        total_documents = db.query(func.count(Document.id)).scalar()
        
        # Get approved documents count
        approved_documents = db.query(func.count(Document.id)).filter(
            Document.status == "approved"
        ).scalar()
        
        # Get pending documents count
        pending_documents = db.query(func.count(Document.id)).filter(
            Document.status == "pending"
        ).scalar()
        
        # Get processed documents count (approved documents that have been processed)
        processed_documents = db.query(func.count(Document.id)).filter(
            Document.status == "approved",
            Document.processed_at.isnot(None)
        ).scalar()
        
        # Get unique countries count (from approved documents)
        # Deleted documents are permanently removed from DB, so they won't appear
        total_countries = db.query(func.count(distinct(Document.country))).filter(
            Document.status == "approved",
            Document.country.isnot(None)
        ).scalar()
        
        # Get unique states count (from approved documents)
        # Deleted documents are permanently removed from DB, so they won't appear
        total_states = db.query(func.count(distinct(Document.state))).filter(
            Document.status == "approved",
            Document.state.isnot(None)
        ).scalar()
        
        # Ensure counts are not None
        total_documents = total_documents or 0
        approved_documents = approved_documents or 0
        pending_documents = pending_documents or 0
        processed_documents = processed_documents or 0
        total_countries = total_countries or 0
        total_states = total_states or 0
        
        logger.info("Global statistics retrieved successfully", 
                   total_documents=total_documents,
                   approved_documents=approved_documents)
        
        return GlobalStatsResponse(
            total_documents=total_documents,
            total_countries=total_countries,
            total_states=total_states,
            approved_documents=approved_documents,
            pending_documents=pending_documents,
            processed_documents=processed_documents
        )
        
    except Exception as e:
        logger.error("Error retrieving global statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving global statistics"
        )
