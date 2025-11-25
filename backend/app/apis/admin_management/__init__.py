"""Admin Management API endpoints for multi-admin support with passwordless authentication."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from ...database.database import get_db
from ...database.models import Admin, APIKey, Document
from ...auth.jwt_auth import get_current_user, User

router = APIRouter()

# Pydantic models for API requests/responses
class AdminCreate(BaseModel):
    email: EmailStr
    name: str
    is_super_admin: bool = False

class AdminUpdate(BaseModel):
    name: Optional[str] = None
    is_super_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class AdminResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_super_admin: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str
    last_login_at: Optional[str]

class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = ["upload", "download"]

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    created_by: str | None
    created_at: str
    last_used_at: str | None
    usage_count: int
    # When creating, we optionally return the plaintext key once
    plaintext_key: str | None = None

def require_super_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is a super admin."""
    from sqlalchemy.orm import Session
    from ...database.database import SessionLocal
    from ...database.models import Admin
    
    db = SessionLocal()
    try:
        # Check if user is super admin in database
        admin = db.query(Admin).filter(Admin.email == current_user.email).first()
        if not admin or not admin.is_super_admin or not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin privileges required"
            )
        return current_user
    finally:
        db.close()

@router.get("/me", response_model=AdminResponse)
async def get_current_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current admin user's own information."""
    admin = db.query(Admin).filter(Admin.email == current_user.email).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin.to_dict()

@router.get("/admins", response_model=List[AdminResponse])
async def list_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """List all admin users (super admin only)."""
    admins = db.query(Admin).all()
    return [admin.to_dict() for admin in admins]

@router.post("/admins", response_model=AdminResponse)
async def create_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Create a new admin user (super admin only)."""
    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )
    
    # Create new admin (passwordless - uses OTP authentication)
    new_admin = Admin(
        email=admin_data.email.lower().strip(),
        name=admin_data.name,
        is_super_admin=admin_data.is_super_admin,
        is_active=True,
        created_by=current_user.email
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin.to_dict()

@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Delete an admin user (super admin only)."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Don't allow deleting yourself
    if admin.email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account"
        )
    
    db.delete(admin)
    db.commit()
    
    return {"message": "Admin deleted successfully"}

@router.put("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Update admin user details (super admin only)."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Don't allow demoting yourself from super admin
    if admin.email == current_user.email and admin_data.is_super_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove super admin privileges from your own account"
        )
    
    # Update fields that were provided
    if admin_data.name is not None:
        admin.name = admin_data.name
    if admin_data.is_super_admin is not None:
        admin.is_super_admin = admin_data.is_super_admin
    if admin_data.is_active is not None:
        admin.is_active = admin_data.is_active
    
    db.commit()
    db.refresh(admin)
    
    return admin.to_dict()

# -------------- API Keys Management (Admin) --------------

import secrets
import hashlib

def _hash_api_key(plaintext_key: str) -> str:
    return hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    keys = db.query(APIKey).order_by(APIKey.created_at.desc()).all()
    return [APIKeyResponse(**k.to_safe_dict()) for k in keys]

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    payload: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    # Generate key: prefix + random
    prefix = secrets.token_urlsafe(6)[:10]
    secret_part = secrets.token_urlsafe(32)
    plaintext_key = f"hn_{prefix}_{secret_part}"
    key_hash = _hash_api_key(plaintext_key)
    record = APIKey(
        name=payload.name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=list(set(payload.scopes or [])),
        is_active=True,
        created_by=current_user.email
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    data = record.to_safe_dict()
    return APIKeyResponse(**data, plaintext_key=plaintext_key)

@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    is_active: Optional[bool] = None,
    scopes: Optional[list[str]] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    record = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")
    if is_active is not None:
        record.is_active = bool(is_active)
    if scopes is not None:
        record.scopes = list(set(scopes))
    if name is not None:
        record.name = name
    db.commit()
    db.refresh(record)
    return APIKeyResponse(**record.to_safe_dict())

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    record = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(record)
    db.commit()
    return {"message": "API key deleted"}

@router.get("/profile", response_model=AdminResponse)
async def get_admin_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current admin user profile."""
    # This is a placeholder that returns the current user info
    # In a real implementation, you would query the Admin table
    return {
        "id": 1,
        "email": current_user.email or "admin@haqnow.com",
        "name": current_user.name or "Administrator",
        "two_factor_enabled": False,
        "is_active": True,
        "is_super_admin": True,
        "created_by": None,
        "created_at": "2025-01-27T00:00:00Z",
        "updated_at": "2025-01-27T00:00:00Z",
        "last_login_at": None
    }

# Top Viewed Documents Management

@router.post("/documents/{document_id}/toggle-top-viewed")
async def toggle_document_top_viewed(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle whether a document is hidden from the top viewed list.
    Admins can hide/unhide documents from appearing in top viewed.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Toggle the flag
        document.hidden_from_top_viewed = not document.hidden_from_top_viewed
        db.commit()
        
        return {
            "success": True,
            "document_id": document_id,
            "hidden_from_top_viewed": document.hidden_from_top_viewed,
            "message": f"Document {'hidden from' if document.hidden_from_top_viewed else 'visible in'} top viewed list"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error toggling top viewed status: {str(e)}"
        ) 