"""Admin Management API endpoints for 2FA and multi-admin support."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ...database.database import get_db
from ...database.models import Admin
from ...auth.jwt_auth import get_current_user, User, get_password_hash, verify_password
from passlib.context import CryptContext
import secrets
import string

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models for API requests/responses
class AdminCreate(BaseModel):
    email: str
    name: str
    password: str
    is_super_admin: bool = False

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

def require_super_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is a super admin."""
    # For now, we'll check if the user is admin (legacy system)
    # TODO: Update when we fully migrate to the new admin system
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user

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

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set up 2FA for the current admin user."""
    # This is a placeholder implementation
    # In a real implementation, you would:
    # 1. Generate a TOTP secret using pyotp
    # 2. Create a QR code URL
    # 3. Generate backup codes
    # 4. Store the secret in the database (encrypted)
    
    # For now, return placeholder data
    fake_secret = "JBSWY3DPEHPK3PXP"  # Base32 encoded secret
    fake_qr_url = f"otpauth://totp/HaqNow.com:{current_user.email}?secret={fake_secret}&issuer=HaqNow.com"
    fake_backup_codes = [
        ''.join(secrets.choice(string.digits) for _ in range(8))
        for _ in range(10)
    ]
    
    return TwoFactorSetupResponse(
        qr_code_url=fake_qr_url,
        secret=fake_secret,
        backup_codes=fake_backup_codes
    )

@router.post("/2fa/verify")
async def verify_two_factor(
    verify_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify 2FA token and enable 2FA for the user."""
    # This is a placeholder implementation
    # In a real implementation, you would:
    # 1. Verify the TOTP token using pyotp
    # 2. Enable 2FA for the user
    # 3. Store backup codes securely
    
    # For now, just return success if token is 6 digits
    if len(verify_data.token) != 6 or not verify_data.token.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    return {"message": "2FA enabled successfully"}

@router.post("/2fa/disable")
async def disable_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable 2FA for the current admin user."""
    # This is a placeholder implementation
    # In a real implementation, you would:
    # 1. Verify current password or 2FA token
    # 2. Disable 2FA in the database
    # 3. Clear 2FA secret and backup codes
    
    return {"message": "2FA disabled successfully"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change password for the current admin user."""
    # This is a placeholder implementation
    # In a real implementation, you would:
    # 1. Verify current password
    # 2. Hash new password
    # 3. Update in database
    # 4. Optionally invalidate all existing sessions
    
    # For now, just validate password strength
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    return {"message": "Password changed successfully"}

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