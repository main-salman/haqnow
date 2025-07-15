from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import structlog

# Import auth and database
from app.auth.user import AdminUser
from app.database import get_db, Translation

logger = structlog.get_logger()

router = APIRouter()

# Pydantic Models
class TranslationCreate(BaseModel):
    key: str
    language: str
    value: str
    section: str

class TranslationUpdate(BaseModel):
    value: str

class TranslationResponse(BaseModel):
    id: int
    key: str
    language: str
    value: str
    section: str
    updated_by: str
    created_at: str
    updated_at: str

class TranslationBulkUpdate(BaseModel):
    translations: Dict[str, str]  # key -> value mapping

class LanguageResponse(BaseModel):
    translations: Dict[str, str]  # key -> value mapping for a specific language

# --- Translation CRUD Operations ---

@router.get("/languages/{language_code}", response_model=LanguageResponse)
async def get_language_translations(
    language_code: str,
    section: Optional[str] = Query(None, description="Filter by section"),
    db: Session = Depends(get_db)
):
    """Get all translations for a specific language, optionally filtered by section."""
    try:
        query_builder = db.query(Translation).filter(Translation.language == language_code)
        
        if section:
            query_builder = query_builder.filter(Translation.section == section)
        
        translations = query_builder.all()
        
        # Convert to key-value mapping
        result = {translation.key: translation.value for translation in translations}
        
        logger.info("Language translations retrieved", 
                   language=language_code, 
                   section=section,
                   count=len(result))
        
        return LanguageResponse(translations=result)
        
    except Exception as e:
        logger.error("Error retrieving language translations", 
                    language=language_code,
                    section=section,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve translations")

@router.get("/sections/{section_name}")
async def get_section_translations(
    section_name: str,
    db: Session = Depends(get_db)
):
    """Get translations for a specific section across all languages."""
    try:
        translations = db.query(Translation).filter(Translation.section == section_name).all()
        
        # Group by language
        result = {}
        for translation in translations:
            if translation.language not in result:
                result[translation.language] = {}
            result[translation.language][translation.key] = translation.value
        
        logger.info("Section translations retrieved", 
                   section=section_name,
                   languages=list(result.keys()))
        
        return result
        
    except Exception as e:
        logger.error("Error retrieving section translations", 
                    section=section_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve translations")

@router.get("/admin/all", response_model=List[TranslationResponse])
async def get_all_translations(
    admin_user: AdminUser,
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None, description="Filter by language"),
    section: Optional[str] = Query(None, description="Filter by section"),
    search: Optional[str] = Query(None, description="Search in keys or values")
):
    """Get all translations with admin authentication. For admin management interface."""
    try:
        query_builder = db.query(Translation)
        
        # Apply filters
        if language:
            query_builder = query_builder.filter(Translation.language == language)
        if section:
            query_builder = query_builder.filter(Translation.section == section)
        if search:
            search_term = f"%{search}%"
            query_builder = query_builder.filter(
                or_(
                    Translation.key.ilike(search_term),
                    Translation.value.ilike(search_term)
                )
            )
        
        translations = query_builder.order_by(Translation.section, Translation.key, Translation.language).all()
        
        result = [TranslationResponse(**translation.to_dict()) for translation in translations]
        
        logger.info("Admin translations retrieved", 
                   count=len(result),
                   filters={"language": language, "section": section, "search": search})
        
        return result
        
    except Exception as e:
        logger.error("Error retrieving admin translations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve translations")

@router.post("/admin/create", response_model=TranslationResponse)
async def create_translation(
    translation_data: TranslationCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Create a new translation entry."""
    try:
        # Check if translation already exists
        existing = db.query(Translation).filter(
            and_(
                Translation.key == translation_data.key,
                Translation.language == translation_data.language
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Translation already exists for key '{translation_data.key}' in language '{translation_data.language}'"
            )
        
        # Create new translation
        translation = Translation(
            key=translation_data.key,
            language=translation_data.language,
            value=translation_data.value,
            section=translation_data.section,
            updated_by=admin_user.email or admin_user.sub
        )
        
        db.add(translation)
        db.commit()
        db.refresh(translation)
        
        logger.info("Translation created", 
                   key=translation_data.key,
                   language=translation_data.language,
                   section=translation_data.section,
                   admin=admin_user.email)
        
        return TranslationResponse(**translation.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error creating translation", 
                    key=translation_data.key,
                    language=translation_data.language,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create translation")

@router.put("/admin/update/{translation_id}", response_model=TranslationResponse)
async def update_translation(
    translation_id: int,
    update_data: TranslationUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Update an existing translation."""
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        
        if not translation:
            raise HTTPException(status_code=404, detail="Translation not found")
        
        # Update the translation
        translation.value = update_data.value
        translation.updated_by = admin_user.email or admin_user.sub
        
        db.commit()
        db.refresh(translation)
        
        logger.info("Translation updated", 
                   id=translation_id,
                   key=translation.key,
                   language=translation.language,
                   admin=admin_user.email)
        
        return TranslationResponse(**translation.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error updating translation", 
                    id=translation_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update translation")

@router.put("/admin/bulk-update/{language_code}/{section_name}")
async def bulk_update_translations(
    language_code: str,
    section_name: str,
    update_data: TranslationBulkUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Bulk update translations for a specific language and section."""
    try:
        updated_count = 0
        created_count = 0
        
        for key, value in update_data.translations.items():
            # Try to find existing translation
            translation = db.query(Translation).filter(
                and_(
                    Translation.key == key,
                    Translation.language == language_code
                )
            ).first()
            
            if translation:
                # Update existing
                translation.value = value
                translation.section = section_name  # Ensure section is correct
                translation.updated_by = admin_user.email or admin_user.sub
                updated_count += 1
            else:
                # Create new
                translation = Translation(
                    key=key,
                    language=language_code,
                    value=value,
                    section=section_name,
                    updated_by=admin_user.email or admin_user.sub
                )
                db.add(translation)
                created_count += 1
        
        db.commit()
        
        logger.info("Bulk translations updated", 
                   language=language_code,
                   section=section_name,
                   updated=updated_count,
                   created=created_count,
                   admin=admin_user.email)
        
        return {
            "message": f"Successfully processed {len(update_data.translations)} translations",
            "updated": updated_count,
            "created": created_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error("Error bulk updating translations", 
                    language=language_code,
                    section=section_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to bulk update translations")

@router.delete("/admin/delete/{translation_id}")
async def delete_translation(
    translation_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Delete a translation."""
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        
        if not translation:
            raise HTTPException(status_code=404, detail="Translation not found")
        
        logger.info("Translation deleted", 
                   id=translation_id,
                   key=translation.key,
                   language=translation.language,
                   admin=admin_user.email)
        
        db.delete(translation)
        db.commit()
        
        return {"message": "Translation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error deleting translation", 
                    id=translation_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete translation") 