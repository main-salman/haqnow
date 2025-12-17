"""
hCaptcha Verification Service
Provides verification of hCaptcha tokens to prevent automated uploads.
"""
import os
import structlog
import requests
from typing import Optional

logger = structlog.get_logger()

class CaptchaService:
    """Service for verifying hCaptcha tokens"""
    
    def __init__(self):
        self.secret_key = os.getenv("HCAPTCHA_SECRET_KEY")
        self.available = bool(self.secret_key)
        self.verify_url = "https://hcaptcha.com/siteverify"
        
        if not self.available:
            logger.warning("hCaptcha secret key not configured - captcha verification disabled")
        else:
            logger.info("hCaptcha verification service initialized")
    
    def verify_token(self, token: str, remote_ip: Optional[str] = None) -> bool:
        """
        Verify an hCaptcha token with hCaptcha API.
        
        Args:
            token: The hCaptcha token from the frontend
            remote_ip: Optional IP address of the user (for additional verification)
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.available:
            # When secret key is not configured, don't verify (old behavior)
            # Frontend validation ensures captcha is completed
            return True
        
        if not token:
            logger.warning("Captcha verification failed - no token provided")
            return False
        
        try:
            # Prepare verification request
            data = {
                "secret": self.secret_key,
                "response": token
            }
            
            if remote_ip:
                data["remoteip"] = remote_ip
            
            # Make request to hCaptcha API
            response = requests.post(
                self.verify_url,
                data=data,
                timeout=5  # 5 second timeout
            )
            
            if response.status_code != 200:
                logger.error(
                    "hCaptcha API error",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False
            
            result = response.json()
            
            if result.get("success"):
                logger.info("Captcha verification successful")
                return True
            else:
                error_codes = result.get("error-codes", [])
                logger.warning(
                    "Captcha verification failed",
                    error_codes=error_codes
                )
                return False
                
        except requests.exceptions.Timeout:
            logger.error("hCaptcha API timeout - verification failed")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(
                "hCaptcha API request failed",
                error=str(e)
            )
            return False
        except Exception as e:
            logger.error(
                "Unexpected error during captcha verification",
                error=str(e)
            )
            return False

# Create singleton instance
captcha_service = CaptchaService()
