"""JWT-based authentication module to replace databutton auth middleware."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
from fastapi import Header
from sqlalchemy.orm import Session
from ..database.database import SessionLocal
from ..database.models import APIKey
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

# ---------------- API Key Authentication ----------------

class APIConsumer(BaseModel):
    """Represents an API consumer authenticated via API key."""
    key_id: int
    name: str
    scopes: list[str]

def _hash_api_key(plaintext_key: str) -> str:
    """Hash the plaintext API key using SHA-256.
    Note: We use SHA-256 since we receive the full key on every request and do not need a slow hash.
    """
    return hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()

def validate_api_key(x_api_key: Optional[str] = Header(default=None)) -> Optional[APIConsumer]:
    """Validate API key from `X-API-Key` header. Returns APIConsumer if valid, else None.

    The header should contain the full plaintext key. We verify by hashing and comparing to stored hash.
    """
    if not x_api_key:
        return None
    db: Session = SessionLocal()
    try:
        key_hash = _hash_api_key(x_api_key)
        record = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
        if not record:
            return None
        # Update usage metadata (best-effort)
        from datetime import datetime
        try:
            record.last_used_at = datetime.utcnow()
            record.usage_count = (record.usage_count or 0) + 1
            db.commit()
        except Exception:
            db.rollback()
        return APIConsumer(key_id=record.id, name=record.name, scopes=record.scopes or [])
    finally:
        db.close()

def require_api_scope(required_scope: str):
    """FastAPI dependency factory to require an API key with a given scope."""
    def dependency(consumer: Optional[APIConsumer] = Depends(validate_api_key)) -> APIConsumer:
        if consumer is None:
            raise HTTPException(status_code=401, detail="Missing or invalid API key")
        if required_scope not in (consumer.scopes or []):
            raise HTTPException(status_code=403, detail="API key lacks required scope")
        return consumer
    return dependency