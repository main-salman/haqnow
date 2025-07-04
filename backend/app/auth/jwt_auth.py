"""JWT-based authentication module to replace databutton auth middleware."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class User(BaseModel):
    """User model for JWT authentication."""
    sub: str
    user_id: str | None = None
    name: str | None = None
    picture: str | None = None
    email: str | None = None
    is_admin: bool = False

class TokenData(BaseModel):
    """Token data model."""
    email: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Get password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_admin(email: str, password: str) -> Optional[User]:
    """Authenticate admin user."""
    admin_email = os.getenv("admin_email")
    admin_password = os.getenv("admin_password")
    
    if not admin_email or not admin_password:
        return None
    
    if email == admin_email and password == admin_password:
        return User(
            sub=email,
            user_id=email,
            name="Admin",
            email=email,
            is_admin=True
        )
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # For simplicity, we'll just return a basic user
        # In a real app, you'd query your database here
        return User(
            sub=email,
            user_id=email,
            email=email,
            is_admin=payload.get("is_admin", False)
        )
    except JWTError:
        raise credentials_exception

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get admin user - requires admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# For backward compatibility, create a function that mimics databutton's behavior
def get_authorized_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get authorized user - replacement for databutton's get_authorized_user."""
    return get_current_user(credentials) 