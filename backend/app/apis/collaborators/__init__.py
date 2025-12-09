from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from typing import Optional, List
import structlog
import io

from app.auth.user import AdminUser
from app.database import get_db, Collaborator
from app.services.s3_service import s3_service

logger = structlog.get_logger()

router = APIRouter()


class CollaboratorResponse(BaseModel):
    id: int
    name: str
    description: str
    logo_url: str
    logo_path: str
    website_url: str
    priority: int
    is_active: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CollaboratorsListResponse(BaseModel):
    collaborators: List[CollaboratorResponse]
    total: int


@router.get("", response_model=CollaboratorsListResponse)
async def get_collaborators(db: Session = Depends(get_db)):
    """Get all active collaborators, sorted by priority (public endpoint)."""
    try:
        collaborators = (
            db.query(Collaborator)
            .filter(Collaborator.is_active == True)
            .order_by(Collaborator.priority.desc(), Collaborator.created_at.desc())
            .all()
        )
        
        return CollaboratorsListResponse(
            collaborators=[CollaboratorResponse(**c.to_dict()) for c in collaborators],
            total=len(collaborators)
        )
    except Exception as e:
        logger.error("Failed to get collaborators", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get collaborators")


@router.get("/all", response_model=CollaboratorsListResponse)
async def get_all_collaborators(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get all collaborators including inactive (admin only)."""
    try:
        collaborators = (
            db.query(Collaborator)
            .order_by(Collaborator.priority.desc(), Collaborator.created_at.desc())
            .all()
        )
        
        return CollaboratorsListResponse(
            collaborators=[CollaboratorResponse(**c.to_dict()) for c in collaborators],
            total=len(collaborators)
        )
    except Exception as e:
        logger.error("Failed to get all collaborators", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get all collaborators")


@router.post("", response_model=CollaboratorResponse)
async def create_collaborator(
    admin_user: AdminUser,
    name: str = Form(...),
    description: str = Form(...),
    website_url: str = Form(...),
    priority: int = Form(default=5),
    logo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create a new collaborator (admin only)."""
    try:
        # Validate priority
        if priority < 1 or priority > 10:
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 10")
        
        # Validate website URL format
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        # Read logo file content
        logo_content = await logo.read()
        logo_file_stream = io.BytesIO(logo_content)
        
        # Upload logo to S3
        logo_path = s3_service.upload_logo(
            logo_file_stream,
            logo.filename or "logo.png",
            logo.content_type
        )
        
        if not logo_path:
            raise HTTPException(status_code=500, detail="Failed to upload logo")
        
        # Get logo URL
        logo_url = s3_service.get_file_url(logo_path)
        
        # Get admin email
        admin_email = getattr(admin_user, "email", None) or getattr(admin_user, "sub", None)
        
        # Create collaborator
        collaborator = Collaborator(
            name=name,
            description=description,
            logo_url=logo_url,
            logo_path=logo_path,
            website_url=website_url,
            priority=priority,
            is_active=True,
            created_by=admin_email
        )
        
        db.add(collaborator)
        db.commit()
        db.refresh(collaborator)
        
        logger.info("Collaborator created", 
                   collaborator_id=collaborator.id,
                   name=name,
                   created_by=admin_email)
        
        return CollaboratorResponse(**collaborator.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to create collaborator", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create collaborator: {str(e)}")


@router.put("/{collaborator_id}", response_model=CollaboratorResponse)
async def update_collaborator(
    collaborator_id: int,
    admin_user: AdminUser,
    name: str = Form(...),
    description: str = Form(...),
    website_url: str = Form(...),
    priority: int = Form(...),
    is_active: bool = Form(default=True),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Update a collaborator (admin only)."""
    try:
        collaborator = db.query(Collaborator).filter(Collaborator.id == collaborator_id).first()
        
        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator not found")
        
        # Validate priority
        if priority < 1 or priority > 10:
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 10")
        
        # Validate website URL format
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        # Update logo if provided
        if logo:
            # Delete old logo from S3
            if collaborator.logo_path:
                s3_service.delete_file(collaborator.logo_path)
            
            # Upload new logo
            logo_content = await logo.read()
            logo_file_stream = io.BytesIO(logo_content)
            
            logo_path = s3_service.upload_logo(
                logo_file_stream,
                logo.filename or "logo.png",
                logo.content_type
            )
            
            if not logo_path:
                raise HTTPException(status_code=500, detail="Failed to upload logo")
            
            collaborator.logo_path = logo_path
            collaborator.logo_url = s3_service.get_file_url(logo_path)
        
        # Update other fields
        collaborator.name = name
        collaborator.description = description
        collaborator.website_url = website_url
        collaborator.priority = priority
        collaborator.is_active = is_active
        
        db.commit()
        db.refresh(collaborator)
        
        logger.info("Collaborator updated", 
                   collaborator_id=collaborator_id,
                   name=name)
        
        return CollaboratorResponse(**collaborator.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to update collaborator", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update collaborator: {str(e)}")


@router.delete("/{collaborator_id}")
async def delete_collaborator(
    collaborator_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Delete a collaborator (admin only). Soft delete by setting is_active=False."""
    try:
        collaborator = db.query(Collaborator).filter(Collaborator.id == collaborator_id).first()
        
        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator not found")
        
        # Delete logo from S3
        if collaborator.logo_path:
            s3_service.delete_file(collaborator.logo_path)
        
        # Soft delete: set is_active=False
        collaborator.is_active = False
        
        db.commit()
        
        logger.info("Collaborator deleted", collaborator_id=collaborator_id)
        
        return {"message": "Collaborator deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete collaborator", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete collaborator: {str(e)}")

