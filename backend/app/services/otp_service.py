"""OTP service for passwordless authentication."""

import os
import secrets
import json
import logging
from typing import Optional
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)

class OTPService:
    """Service for generating and validating OTP codes."""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        self._memory_store: dict[str, dict] = {}  # Fallback in-memory store
        self._initialize_redis()
        
        # OTP configuration
        self.otp_length = 6
        self.otp_expiry_minutes = 10  # OTP expires in 10 minutes
        self.rate_limit_minutes = 1  # Rate limit: 1 OTP per minute per email
    
    def _initialize_redis(self):
        """Initialize Redis connection with fallback to in-memory."""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ OTP service using Redis storage")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available for OTP, using in-memory store: {e}")
            self.use_redis = False
    
    def _get_otp_key(self, email: str) -> str:
        """Generate Redis key for OTP."""
        return f"otp:{email.lower().strip()}"
    
    def _get_rate_limit_key(self, email: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"otp_rate_limit:{email.lower().strip()}"
    
    def _generate_otp(self) -> str:
        """Generate a random 6-digit OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])
    
    def _check_rate_limit(self, email: str) -> bool:
        """Check if email is rate limited."""
        rate_limit_key = self._get_rate_limit_key(email)
        
        if self.use_redis:
            try:
                last_request = self.redis_client.get(rate_limit_key)
                if last_request:
                    last_time = datetime.fromisoformat(last_request)
                    if datetime.utcnow() - last_time < timedelta(minutes=self.rate_limit_minutes):
                        return False  # Rate limited
                return True
            except Exception as e:
                logger.warning(f"Redis rate limit check error: {e}")
                # Fallback to memory
                pass
        
        # In-memory rate limit check
        if email in self._memory_store:
            stored_data = self._memory_store[email]
            if 'rate_limit_until' in stored_data:
                if datetime.utcnow() < stored_data['rate_limit_until']:
                    return False
        
        return True
    
    def _set_rate_limit(self, email: str):
        """Set rate limit for email."""
        rate_limit_key = self._get_rate_limit_key(email)
        rate_limit_until = datetime.utcnow() + timedelta(minutes=self.rate_limit_minutes)
        
        if self.use_redis:
            try:
                self.redis_client.setex(
                    rate_limit_key,
                    self.rate_limit_minutes * 60,
                    datetime.utcnow().isoformat()
                )
            except Exception as e:
                logger.warning(f"Redis rate limit set error: {e}")
        
        # Also store in memory as backup
        if email not in self._memory_store:
            self._memory_store[email] = {}
        self._memory_store[email]['rate_limit_until'] = rate_limit_until
    
    def generate_otp(self, email: str) -> Optional[str]:
        """
        Generate and store OTP for email.
        Returns OTP code if successful, None if rate limited.
        """
        email = email.lower().strip()
        
        # Check rate limit
        if not self._check_rate_limit(email):
            logger.warning(f"Rate limit exceeded for email: {email}")
            return None
        
        # Generate OTP
        otp_code = self._generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
        
        otp_data = {
            'code': otp_code,
            'email': email,
            'expires_at': expires_at.isoformat(),
            'attempts': 0,
            'max_attempts': 5
        }
        
        # Store OTP
        otp_key = self._get_otp_key(email)
        
        if self.use_redis:
            try:
                self.redis_client.setex(
                    otp_key,
                    self.otp_expiry_minutes * 60,
                    json.dumps(otp_data)
                )
            except Exception as e:
                logger.warning(f"Redis OTP storage error: {e}, falling back to memory")
                self.use_redis = False
        
        # Store in memory (always, as backup)
        self._memory_store[email] = otp_data
        
        # Set rate limit
        self._set_rate_limit(email)
        
        logger.info(f"OTP generated for email: {email}")
        return otp_code
    
    def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        Verify OTP code for email.
        Returns True if valid, False otherwise.
        """
        email = email.lower().strip()
        otp_key = self._get_otp_key(email)
        
        # Get OTP data
        otp_data = None
        
        if self.use_redis:
            try:
                stored = self.redis_client.get(otp_key)
                if stored:
                    otp_data = json.loads(stored)
            except Exception as e:
                logger.warning(f"Redis OTP retrieval error: {e}")
        
        # Fallback to memory
        if not otp_data and email in self._memory_store:
            otp_data = self._memory_store[email]
        
        if not otp_data:
            logger.warning(f"No OTP found for email: {email}")
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(otp_data['expires_at'])
        if datetime.utcnow() > expires_at:
            logger.warning(f"OTP expired for email: {email}")
            self._invalidate_otp(email)
            return False
        
        # Check attempts
        attempts = otp_data.get('attempts', 0)
        max_attempts = otp_data.get('max_attempts', 5)
        if attempts >= max_attempts:
            logger.warning(f"Max attempts exceeded for email: {email}")
            self._invalidate_otp(email)
            return False
        
        # Verify code
        if otp_data['code'] != otp_code:
            # Increment attempts
            otp_data['attempts'] = attempts + 1
            if self.use_redis:
                try:
                    remaining_ttl = self.redis_client.ttl(otp_key)
                    if remaining_ttl > 0:
                        self.redis_client.setex(
                            otp_key,
                            remaining_ttl,
                            json.dumps(otp_data)
                        )
                except Exception:
                    pass
            self._memory_store[email] = otp_data
            logger.warning(f"Invalid OTP attempt for email: {email}, attempts: {otp_data['attempts']}")
            return False
        
        # Valid OTP - invalidate it
        self._invalidate_otp(email)
        logger.info(f"OTP verified successfully for email: {email}")
        return True
    
    def _invalidate_otp(self, email: str):
        """Invalidate OTP for email."""
        email = email.lower().strip()
        otp_key = self._get_otp_key(email)
        
        if self.use_redis:
            try:
                self.redis_client.delete(otp_key)
            except Exception:
                pass
        
        # Remove from memory
        if email in self._memory_store:
            del self._memory_store[email]

# Global OTP service instance
otp_service = OTPService()

