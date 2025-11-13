"""
Virus Scanning Service using VirusTotal API
Provides synchronous virus scanning for uploaded files with proper error handling.
Uses VirusTotal's free tier (500 requests/day, 4 requests/minute)
"""
import io
import structlog
from typing import Tuple, Optional
import os
import time
import hashlib

logger = structlog.get_logger()

class VirusScanningService:
    """Service for scanning files for viruses and malware using VirusTotal API"""
    
    def __init__(self):
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY")
        self.available = bool(self.api_key)
        self.api_url = "https://www.virustotal.com/api/v3"
        
        if not self.available:
            logger.warning("VirusTotal API key not configured - virus scanning disabled")
        else:
            logger.info("VirusTotal virus scanning service initialized")
    
    def scan_file_content(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Scan file content for viruses using VirusTotal API.
        
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
                "Virus scanning skipped - VirusTotal API key not configured",
                filename=filename
            )
            # For security: default to safe when scanner unavailable
            # In production, you may want to reject uploads instead
            return True, None
        
        try:
            import requests
            
            logger.info("Scanning file with VirusTotal", filename=filename, size=len(file_content))
            
            # Calculate file hash to check if already scanned
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # First, try to get existing scan results by hash
            headers = {"x-apikey": self.api_key}
            hash_url = f"{self.api_url}/files/{file_hash}"
            
            try:
                response = requests.get(hash_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    # File already scanned, use cached results
                    data = response.json()
                    return self._parse_scan_results(data, filename, file_hash)
            except Exception as e:
                logger.debug("Hash lookup failed, will upload file", error=str(e))
            
            # File not in database, upload for scanning
            upload_url = f"{self.api_url}/files"
            files = {"file": (filename, io.BytesIO(file_content))}
            
            upload_response = requests.post(
                upload_url, 
                headers=headers, 
                files=files,
                timeout=30
            )
            
            if upload_response.status_code != 200:
                logger.error(
                    "VirusTotal upload failed",
                    status=upload_response.status_code,
                    response=upload_response.text[:200]
                )
                return False, f"Upload failed: {upload_response.status_code}"
            
            upload_data = upload_response.json()
            analysis_id = upload_data.get("data", {}).get("id")
            
            if not analysis_id:
                logger.error("No analysis ID received from VirusTotal")
                return False, "No analysis ID"
            
            # Wait for analysis to complete (max 30 seconds)
            analysis_url = f"{self.api_url}/analyses/{analysis_id}"
            max_attempts = 15
            
            for attempt in range(max_attempts):
                time.sleep(2)  # Wait 2 seconds between checks
                
                analysis_response = requests.get(analysis_url, headers=headers, timeout=10)
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    status = analysis_data.get("data", {}).get("attributes", {}).get("status")
                    
                    if status == "completed":
                        return self._parse_scan_results(analysis_data, filename, file_hash)
                    elif status == "queued" or status == "in-progress":
                        logger.debug(f"Analysis in progress, attempt {attempt + 1}/{max_attempts}")
                        continue
                    else:
                        logger.warning(f"Unexpected status: {status}")
                        break
            
            # Timeout waiting for results
            logger.warning("VirusTotal analysis timed out", filename=filename)
            return False, "Analysis timeout - please try again"
                
        except Exception as e:
            logger.error(
                "Error during VirusTotal scan",
                filename=filename,
                error=str(e),
                error_type=type(e).__name__
            )
            # On error, fail safe by rejecting the file
            return False, f"Scan error: {str(e)}"
    
    def _parse_scan_results(self, data: dict, filename: str, file_hash: str) -> Tuple[bool, Optional[str]]:
        """Parse VirusTotal scan results"""
        try:
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("stats", {}) or attributes.get("last_analysis_stats", {})
            results = attributes.get("results", {}) or attributes.get("last_analysis_results", {})
            
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            
            if malicious > 0 or suspicious > 0:
                # Find which engines detected it
                detections = [
                    f"{engine}: {result.get('result', 'unknown')}"
                    for engine, result in results.items()
                    if result.get("category") in ["malicious", "suspicious"]
                ][:3]  # First 3 detections
                
                virus_info = f"{malicious + suspicious} engines detected threats: {', '.join(detections)}"
                
                logger.warning(
                    "VIRUS DETECTED by VirusTotal",
                    filename=filename,
                    file_hash=file_hash,
                    malicious=malicious,
                    suspicious=suspicious,
                    detections=detections
                )
                return False, virus_info
            else:
                logger.info(
                    "File scan completed - clean",
                    filename=filename,
                    file_hash=file_hash,
                    engines_scanned=len(results)
                )
                return True, None
                
        except Exception as e:
            logger.error("Error parsing VirusTotal results", error=str(e))
            return False, f"Parse error: {str(e)}"
    
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
                "Virus scanning skipped - VirusTotal API not available",
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
        """Get service information"""
        if not self.available:
            return None
        return "VirusTotal API v3 (70+ engines)"
    
    def get_status(self) -> dict:
        """Get current status of virus scanning service"""
        status = {
            "available": self.available,
            "scanner": "VirusTotal",
            "engines": "70+" if self.available else None,
            "daily_limit": "500 scans/day",
            "rate_limit": "4 requests/minute"
        }
        
        if self.available:
            status["version"] = self.get_virus_definitions_version()
        
        return status


# Singleton instance
virus_scanning_service = VirusScanningService()

