"""Authentication API endpoints - Passwordless OTP authentication."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime
from ...auth.jwt_auth import create_access_token, get_current_user, User
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.models import Admin
from ...services.otp_service import otp_service
from ...services.email_service import email_service

router = APIRouter()
security = HTTPBearer()

class OTPRequest(BaseModel):
    email: EmailStr

class OTPRequestResponse(BaseModel):
    message: str
    email: str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserResponse(BaseModel):
    user: User

@router.post("/login/request-otp", response_model=OTPRequestResponse)
async def request_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """
    Request OTP code for passwordless login.
    Sends OTP code to admin email if the email exists in the system.
    """
    # Check if admin exists and is active
    admin = db.query(Admin).filter(Admin.email == request.email.lower().strip()).first()
    if not admin:
        # Don't reveal if email exists or not for security
        # Still return success to prevent email enumeration
        return OTPRequestResponse(
            message="If this email exists, an OTP code has been sent.",
            email=request.email
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Generate OTP
    otp_code = otp_service.generate_otp(request.email.lower().strip())
    
    if not otp_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please wait before requesting another code."
        )
    
    # Send OTP email
    email_sent = email_service.send_otp_email(request.email.lower().strip(), otp_code)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email. Please try again later."
        )
    
    return OTPRequestResponse(
        message="OTP code has been sent to your email.",
        email=request.email
    )

@router.post("/login/verify-otp", response_model=LoginResponse)
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP code and return JWT token for passwordless login.
    """
    email = request.email.lower().strip()
    
    # Validate OTP code format
    if not request.otp_code or not request.otp_code.isdigit() or len(request.otp_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code format. Please enter a 6-digit code."
        )
    
    # Verify OTP
    is_valid = otp_service.verify_otp(email, request.otp_code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP code. Please request a new code."
        )
    
    # Get admin user
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user or account inactive"
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