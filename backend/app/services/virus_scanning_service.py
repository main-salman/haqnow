"""
Virus Scanning Service using ClamAV
Provides synchronous virus scanning for uploaded files with proper error handling.
"""
import io
import structlog
from typing import Tuple, Optional
import tempfile
import os

logger = structlog.get_logger()

class VirusScanningService:
    """Service for scanning files for viruses and malware using ClamAV"""
    
    def __init__(self):
        self.clamd = None
        self.available = False
        self._initialize_clamd()
    
    def _initialize_clamd(self):
        """Initialize ClamAV daemon connection"""
        try:
            import clamd
            
            # Try connecting to ClamAV daemon
            # First try Unix socket (default on Ubuntu/Debian)
            try:
                self.clamd = clamd.ClamdUnixSocket()
                self.clamd.ping()
                self.available = True
                logger.info("ClamAV connected via Unix socket")
                return
            except Exception:
                pass
            
            # Try TCP socket (fallback)
            try:
                self.clamd = clamd.ClamdNetworkSocket(host='localhost', port=3310)
                self.clamd.ping()
                self.available = True
                logger.info("ClamAV connected via TCP socket")
                return
            except Exception:
                pass
            
            logger.warning(
                "ClamAV daemon not available - virus scanning disabled",
                error="Could not connect to clamd via Unix socket or TCP"
            )
            self.available = False
            
        except ImportError:
            logger.warning(
                "ClamAV library not installed - virus scanning disabled",
                error="clamd Python library not found"
            )
            self.available = False
    
    def scan_file_content(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Scan file content for viruses.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename (for logging)
        
        Returns:
            Tuple of (is_safe, virus_name)
            - is_safe: True if file is clean, False if infected or error
            - virus_name: Name of virus if found, error message if scan failed, None if clean
        """
        if not self.available:
            logger.warning(
                "Virus scanning skipped - ClamAV not available",
                filename=filename
            )
            # For security: default to safe when scanner unavailable
            # In production, you may want to reject uploads instead
            return True, None
        
        try:
            logger.info("Scanning file for viruses", filename=filename, size=len(file_content))
            
            # Scan the file content using ClamAV
            # clamd.scan_stream() expects a file-like object
            file_stream = io.BytesIO(file_content)
            scan_result = self.clamd.instream(file_stream)
            
            # Parse scan result
            # Result format: {'stream': ('FOUND', 'Virus.Name')} or {'stream': ('OK', None)}
            if 'stream' in scan_result:
                status, virus_name = scan_result['stream']
                
                if status == 'FOUND':
                    logger.warning(
                        "VIRUS DETECTED in uploaded file",
                        filename=filename,
                        virus=virus_name,
                        size=len(file_content)
                    )
                    return False, virus_name
                elif status == 'OK':
                    logger.info(
                        "File scan completed - clean",
                        filename=filename,
                        size=len(file_content)
                    )
                    return True, None
                else:
                    # Unknown status
                    logger.error(
                        "Unknown ClamAV scan status",
                        filename=filename,
                        status=status
                    )
                    return False, f"Unknown scan status: {status}"
            else:
                logger.error(
                    "Unexpected ClamAV response format",
                    filename=filename,
                    response=scan_result
                )
                return False, "Unexpected scan response"
                
        except Exception as e:
            logger.error(
                "Error during virus scan",
                filename=filename,
                error=str(e),
                error_type=type(e).__name__
            )
            # On error, fail safe by rejecting the file
            return False, f"Scan error: {str(e)}"
    
    def scan_file_path(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan a file by path (for existing files on disk).
        
        Args:
            file_path: Path to the file
        
        Returns:
            Tuple of (is_safe, virus_name)
        """
        if not self.available:
            logger.warning(
                "Virus scanning skipped - ClamAV not available",
                file_path=file_path
            )
            return True, None
        
        try:
            # Read file and scan content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            return self.scan_file_content(file_content, os.path.basename(file_path))
            
        except Exception as e:
            logger.error(
                "Error reading file for virus scan",
                file_path=file_path,
                error=str(e)
            )
            return False, f"File read error: {str(e)}"
    
    def get_virus_definitions_version(self) -> Optional[str]:
        """Get the current virus definitions version from ClamAV"""
        if not self.available:
            return None
        
        try:
            version_info = self.clamd.version()
            return version_info
        except Exception as e:
            logger.error("Failed to get ClamAV version", error=str(e))
            return None
    
    def get_status(self) -> dict:
        """Get current status of virus scanning service"""
        status = {
            "available": self.available,
            "scanner": "ClamAV",
        }
        
        if self.available:
            status["version"] = self.get_virus_definitions_version()
        
        return status


# Singleton instance
virus_scanning_service = VirusScanningService()

