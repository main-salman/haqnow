"""OTP service for passwordless authentication using MySQL database."""

import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OTPService:
    """Service for generating and validating OTP codes using MySQL database."""
    
    def __init__(self):
        # OTP configuration
        self.otp_length = 6
        self.otp_expiry_minutes = 10  # OTP expires in 10 minutes
        self.rate_limit_seconds = 60  # Rate limit: 1 OTP per 60 seconds per email
        self.max_attempts = 5
    
    def _generate_otp(self) -> str:
        """Generate a random 6-digit OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])
    
    def generate_otp(self, db: Session, email: str) -> Optional[str]:
        """
        Generate and store OTP for email in database.
        Returns OTP code if successful, None if rate limited.
        """
        from app.database.models import OTPCode
        
        email = email.lower().strip()
        now = datetime.utcnow()
        
        # Check rate limit - look for recent OTP requests
        recent_otp = db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.created_at > now - timedelta(seconds=self.rate_limit_seconds)
        ).first()
        
        if recent_otp:
            logger.warning(f"Rate limit exceeded for email: {email}")
            return None
        
        # Invalidate any existing unused OTPs for this email
        db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.used == False
        ).update({"used": True})
        
        # Generate new OTP
        otp_code = self._generate_otp()
        expires_at = now + timedelta(minutes=self.otp_expiry_minutes)
        
        # Create OTP record
        otp_record = OTPCode(
            email=email,
            code=otp_code,
            attempts=0,
            max_attempts=self.max_attempts,
            expires_at=expires_at,
            used=False
        )
        
        db.add(otp_record)
        db.commit()
        
        logger.info(f"OTP generated for email: {email}")
        return otp_code
    
    def verify_otp(self, db: Session, email: str, otp_code: str) -> bool:
        """
        Verify OTP code for email.
        Returns True if valid, False otherwise.
        """
        from app.database.models import OTPCode
        
        email = email.lower().strip()
        now = datetime.utcnow()
        
        # Find valid OTP for this email
        otp_record = db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.used == False,
            OTPCode.expires_at > now
        ).order_by(OTPCode.created_at.desc()).first()
        
        if not otp_record:
            logger.warning(f"No valid OTP found for email: {email}")
            return False
        
        # Check attempts
        if otp_record.attempts >= otp_record.max_attempts:
            logger.warning(f"Max attempts exceeded for email: {email}")
            otp_record.used = True
            db.commit()
            return False
        
        # Verify code
        if otp_record.code != otp_code:
            # Increment attempts
            otp_record.attempts += 1
            db.commit()
            logger.warning(f"Invalid OTP attempt for email: {email}, attempts: {otp_record.attempts}")
            return False
        
        # Valid OTP - mark as used
        otp_record.used = True
        db.commit()
        
        logger.info(f"OTP verified successfully for email: {email}")
        return True
    
    def cleanup_expired(self, db: Session) -> int:
        """
        Clean up expired OTP codes.
        Returns number of records deleted.
        """
        from app.database.models import OTPCode
        
        now = datetime.utcnow()
        # Delete OTPs that are either used or expired more than 1 hour ago
        result = db.query(OTPCode).filter(
            (OTPCode.used == True) | (OTPCode.expires_at < now - timedelta(hours=1))
        ).delete(synchronize_session=False)
        db.commit()
        
        if result > 0:
            logger.info(f"Cleaned up {result} expired OTP records")
        
        return result


# Global OTP service instance
otp_service = OTPService()
