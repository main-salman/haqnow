"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import timedelta
from ...auth.jwt_auth import authenticate_admin, create_access_token, get_current_user, User

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserResponse(BaseModel):
    user: User

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Admin login endpoint."""
    user = authenticate_admin(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
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

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(user=current_user)

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)."""
    return {"message": "Successfully logged out"} 