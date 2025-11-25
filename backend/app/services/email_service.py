"""Email notification service for admin notifications."""

import os
from typing import Optional, Iterable
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import smtplib
from email.mime.text import MIMEText
import structlog

logger = structlog.get_logger()

class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@fadih.org")
        self.admin_email = os.getenv("admin_email")
        self.client = None
        # Generic SMTP configuration (provider-agnostic). Falls back to SendGrid-compatible defaults
        # if generic env vars are not provided.
        self.smtp_host = os.getenv("SMTP_HOST") or os.getenv("SENDGRID_SMTP_HOST", "smtp.sendgrid.net")
        try:
            self.smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("SENDGRID_SMTP_PORT", "587"))
        except ValueError:
            self.smtp_port = 587
        self.smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SENDGRID_SMTP_USERNAME", "apikey")
        # Password/token for SMTP authentication. When using SendGrid, this is typically the API key.
        self.smtp_password = os.getenv("SMTP_PASSWORD") or self.sendgrid_api_key
        # TLS/SSL toggles (sane defaults)
        self.smtp_use_ssl = (os.getenv("SMTP_USE_SSL", "false").lower() == "true")
        self.smtp_use_tls = (os.getenv("SMTP_USE_TLS", "true").lower() == "true")
        
        if self.sendgrid_api_key:
            self.client = SendGridAPIClient(api_key=self.sendgrid_api_key)
        else:
            logger.warning("SendGrid API key not configured, email notifications disabled")
    
    def _send_via_api(self, to_email: str, subject: str, content: str) -> bool:
        if not self.client:
            return False
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            response = self.client.send(message)
            status = getattr(response, "status_code", None)
            if status and 200 <= int(status) < 300:
                logger.info("Email sent via SendGrid API", to_email=to_email, status_code=status)
                return True
            logger.warning("SendGrid API returned non-success status", to_email=to_email, status_code=status)
            return False
        except Exception as e:
            logger.error("SendGrid API send failed", to_email=to_email, error=str(e))
            return False

    def _send_via_smtp(self, to_email: str, subject: str, content: str) -> bool:
        # Require at minimum host and password/token
        if not self.smtp_host or not self.smtp_password:
            return False
        msg = MIMEText(content, "html")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email
        try:
            # Choose connection strategy
            if self.smtp_use_ssl or self.smtp_port == 465:
                smtp_client = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=20)
            else:
                smtp_client = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20)
            with smtp_client as server:
                server.ehlo()
                if isinstance(server, smtplib.SMTP) and self.smtp_use_tls and not isinstance(server, smtplib.SMTP_SSL):
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception:
                        # Some providers may not advertise STARTTLS on alternative ports
                        pass
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
            logger.info("Email sent via SMTP", to_email=to_email, host=self.smtp_host, port=self.smtp_port)
            return True
        except Exception as e:
            logger.error("SMTP send failed", to_email=to_email, error=str(e), host=self.smtp_host, port=self.smtp_port)
            return False

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send an email preferring configured SMTP; fallback to SendGrid API if present."""
        # Prefer explicit SMTP configuration if provided (e.g., Maileroo)
        if self._send_via_smtp(to_email, subject, content):
            return True
        # Fallback to SendGrid API if available
        if self._send_via_api(to_email, subject, content):
            return True
        return False

    def send_bulk(self, to_emails: Iterable[str], subject: str, content: str) -> int:
        """Send an email to multiple recipients. Returns number of attempted sends.
        This performs simple per-recipient sends to keep code minimal and robust.
        """
        count = 0
        if not to_emails:
            return 0
        for addr in {e.strip() for e in to_emails if isinstance(e, str) and e.strip()}:
            ok = self.send_email(addr, subject, content)
            if ok:
                count += 1
        return count
        
        # Unreachable now; kept to preserve structure
        return 0
    
    def notify_admin_new_document(self, document_id: str, title: str, country: str, 
                                 state: str, uploader_ip: str = None, extra_recipients: Optional[Iterable[str]] = None) -> bool:
        """Notify admin about a new document upload. Can include extra recipients."""
        
        subject = f"New Corruption Document Uploaded - {title}"
        content = f"""
        <html>
        <body>
            <h2>New Corruption Document Uploaded</h2>
            <p>A new corruption exposure document has been uploaded and is pending your approval.</p>
            
            <h3>Document Details:</h3>
            <ul>
                <li><strong>Document ID:</strong> {document_id}</li>
                <li><strong>Title:</strong> {title}</li>
                <li><strong>Country:</strong> {country}</li>
                <li><strong>State/Province:</strong> {state}</li>
                <li><strong>Uploader:</strong> Anonymous</li>
            </ul>
            
            <p>Please review and approve or reject this document in the admin dashboard.</p>
            
            <p>Best regards,<br>Fadih.org System</p>
        </body>
        </html>
        """
        # If explicit recipients provided, send to them; otherwise fallback to single admin_email
        if extra_recipients:
            sent = self.send_bulk(extra_recipients, subject, content)
            return sent > 0
        if not self.admin_email:
            logger.warning("Admin email not configured and no extra recipients provided, skipping notification")
            return False
        return self.send_email(self.admin_email, subject, content)
    
    def notify_admin_document_approved(self, document_id: str, title: str) -> bool:
        """Notify admin that a document has been approved."""
        if not self.admin_email:
            return False
        
        subject = f"Corruption Document Approved - {title}"
        content = f"""
        <html>
        <body>
            <h2>Corruption Document Approved</h2>
            <p>Document <strong>{title}</strong> (ID: {document_id}) has been approved and is now publicly available.</p>
            
            <p>Best regards,<br>Fadih.org System</p>
        </body>
        </html>
        """
        
        return self.send_email(self.admin_email, subject, content)
    
    def notify_admin_document_rejected(self, document_id: str, title: str, reason: str = "") -> bool:
        """Notify admin that a document has been rejected."""
        if not self.admin_email:
            return False
        
        subject = f"Corruption Document Rejected - {title}"
        content = f"""
        <html>
        <body>
            <h2>Corruption Document Rejected</h2>
            <p>Document <strong>{title}</strong> (ID: {document_id}) has been rejected.</p>
            
            {f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""}
            
            <p>Best regards,<br>Fadih.org System</p>
        </body>
        </html>
        """
        
        return self.send_email(self.admin_email, subject, content)
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """Send OTP code email for passwordless login."""
        subject = "Your HaqNow Admin Login Code"
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">HaqNow Admin Login</h2>
                <p>Your one-time login code is:</p>
                <div style="background-color: #f3f4f6; border: 2px dashed #2563eb; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #2563eb; font-size: 32px; letter-spacing: 8px; margin: 0;">{otp_code}</h1>
                </div>
                <p style="color: #6b7280; font-size: 14px;">This code will expire in 10 minutes.</p>
                <p style="color: #6b7280; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px;">Best regards,<br>HaqNow System</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, content)

# Global email service instance
email_service = EmailService() 