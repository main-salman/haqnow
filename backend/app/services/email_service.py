"""Email notification service for admin notifications."""

import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import structlog

logger = structlog.get_logger()

class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@fadih.org")
        self.admin_email = os.getenv("admin_email")
        self.client = None
        
        if self.sendgrid_api_key:
            self.client = SendGridAPIClient(api_key=self.sendgrid_api_key)
        else:
            logger.warning("SendGrid API key not configured, email notifications disabled")
    
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send an email using SendGrid."""
        if not self.client:
            logger.warning("Email service not configured, skipping email send")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            
            response = self.client.send(message)
            logger.info("Email sent successfully", 
                       to_email=to_email, 
                       status_code=response.status_code)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", 
                        to_email=to_email, 
                        error=str(e))
            return False
    
    def notify_admin_new_document(self, document_id: str, title: str, country: str, 
                                 state: str, uploader_ip: str = None) -> bool:
        """Notify admin about a new document upload."""
        if not self.admin_email:
            logger.warning("Admin email not configured, skipping notification")
            return False
        
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

# Global email service instance
email_service = EmailService() 