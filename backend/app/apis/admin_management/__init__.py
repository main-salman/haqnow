"""Admin Management API endpoints for 2FA and multi-admin support."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ...database.database import get_db
from ...database.models import Admin, APIKey, Document
from ...auth.jwt_auth import get_current_user, User, get_password_hash, verify_password
from passlib.context import CryptContext
import secrets
import string
import pyotp
import qrcode
import io
import base64

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models for API requests/responses
class AdminCreate(BaseModel):
    email: str
    name: str
    password: str
    is_super_admin: bool = False

class AdminUpdate(BaseModel):
    name: Optional[str] = None
    is_super_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class AdminResponse(BaseModel):
    id: int
    email: str
    name: str
    two_factor_enabled: bool
    is_active: bool
    is_super_admin: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str
    last_login_at: Optional[str]

class TwoFactorSetupResponse(BaseModel):
    qr_code_url: str
    secret: str
    backup_codes: List[str]

class TwoFactorVerifyRequest(BaseModel):
    token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

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
    
    # Create new admin
    password_hash = pwd_context.hash(admin_data.password)
    new_admin = Admin(
        email=admin_data.email,
        name=admin_data.name,
        password_hash=password_hash,
        is_super_admin=admin_data.is_super_admin,
        is_active=True,
        two_factor_enabled=False,
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

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set up 2FA for the current admin user."""
    try:
        # Get the admin from database
        admin = db.query(Admin).filter(Admin.email == current_user.email).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Generate a new TOTP secret
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Generate the provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="HaqNow.com"
        )
        
        # Generate QR code as base64 image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_code_data_url = f"data:image/png;base64,{qr_code_base64}"
        
        # Generate backup codes
        backup_codes = [
            ''.join(secrets.choice(string.digits) for _ in range(8))
            for _ in range(10)
        ]
        
        # Store the secret in the admin record (temporarily, until verified)
        admin.two_factor_secret = secret
        admin.backup_codes = ','.join(backup_codes)  # Store as comma-separated string
        db.commit()
        
        return TwoFactorSetupResponse(
            qr_code_url=qr_code_data_url,
            secret=secret,
            backup_codes=backup_codes
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}"
        )

@router.post("/2fa/verify")
async def verify_two_factor(
    verify_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify 2FA token and enable 2FA for the user."""
    try:
        # Get the admin from database
        admin = db.query(Admin).filter(Admin.email == current_user.email).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Check if 2FA secret exists
        if not admin.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up. Please set up 2FA first."
            )
        
        # Validate token format
        if not verify_data.token or not verify_data.token.isdigit() or len(verify_data.token) != 6:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Verification code must be exactly 6 digits"
            )
        
        # Verify the TOTP token with debugging
        totp = pyotp.TOTP(admin.two_factor_secret)
        
        # Debug information
        current_token = totp.now()
        print(f"🔍 2FA Debug Info:")
        print(f"  - User provided token: {verify_data.token}")
        print(f"  - Current valid token: {current_token}")
        print(f"  - Secret length: {len(admin.two_factor_secret)}")
        print(f"  - Secret: {admin.two_factor_secret[:8]}...")
        
        # Try verification with a wider time window (allow ±1 time step = ±30 seconds)
        is_valid = totp.verify(verify_data.token, valid_window=1)
        
        if not is_valid:
            # Try additional debugging - check a few more time windows
            print(f"  - Checking additional time windows...")
            for i in range(-2, 3):
                test_token = totp.at(totp.timecode(totp.now()) + i)
                print(f"    Window {i}: {test_token}")
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid verification code. Please ensure your device time is synchronized and try again."
            )
        
        # Enable 2FA for the user
        admin.two_factor_enabled = True
        db.commit()
        
        return {"message": "2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}"
        )

@router.post("/2fa/disable")
async def disable_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable 2FA for the current admin user."""
    try:
        # Get the admin from database
        admin = db.query(Admin).filter(Admin.email == current_user.email).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Disable 2FA and clear secrets
        admin.two_factor_enabled = False
        admin.two_factor_secret = None
        admin.backup_codes = None
        db.commit()
        
        return {"message": "2FA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change password for the current admin user."""
    try:
        # Get the admin from database
        admin = db.query(Admin).filter(Admin.email == current_user.email).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Verify current password
        if not pwd_context.verify(password_data.current_password, admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if len(password_data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Check if new password is different from current
        if password_data.current_password == password_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Hash new password
        new_password_hash = pwd_context.hash(password_data.new_password)
        
        # Update password in database
        admin.password_hash = new_password_hash
        db.commit()
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

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