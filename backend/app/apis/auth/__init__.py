"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import timedelta
from ...auth.jwt_auth import authenticate_admin, create_access_token, get_current_user, User
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.models import Admin
import pyotp

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class TwoFactorRequiredResponse(BaseModel):
    requires_2fa: bool = True
    email: str
    message: str = "2FA verification required"

class TwoFactorLoginRequest(BaseModel):
    email: str
    token: str

class UserResponse(BaseModel):
    user: User

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login endpoint with 2FA support."""
    user = authenticate_admin(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has 2FA enabled
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if admin and admin.two_factor_enabled:
        # Return 2FA required response instead of JWT token
        return TwoFactorRequiredResponse(
            email=request.email
        )
    
    # No 2FA required - create access token as normal
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.post("/login/verify-2fa", response_model=LoginResponse)
async def verify_login_2fa(request: TwoFactorLoginRequest, db: Session = Depends(get_db)):
    """Verify 2FA token during login and return JWT token."""
    # First verify that the user exists and is active
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Check if user has 2FA enabled and secret exists
    if not admin.two_factor_enabled or not admin.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled for this user",
        )
    
    # Validate token format
    if not request.token or not request.token.isdigit() or len(request.token) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token format",
        )
    
    # Verify the TOTP token
    totp = pyotp.TOTP(admin.two_factor_secret)
    is_valid = totp.verify(request.token, valid_window=1)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token",
        )
    
    # Create user object and JWT token
    user = User(
        sub=admin.email,
        user_id=admin.email,
        name=admin.name,
        email=admin.email,
        is_admin=True
    )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    
    # Update last login time
    from datetime import datetime
    admin.last_login_at = datetime.utcnow()
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(user=current_user)

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)."""
    return {"message": "Successfully logged out"} 