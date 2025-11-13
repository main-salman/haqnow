# Virus & Malware Scanning Documentation

## Overview

HaqNow implements comprehensive virus and malware scanning for all file uploads using **ClamAV**, an open-source antivirus engine. This ensures that the platform remains secure while maintaining privacy and avoiding reliance on third-party cloud services.

## Architecture

### Components

1. **ClamAV Daemon** (`clamd`)
   - Background service that performs actual virus scanning
   - Unix socket: `/var/run/clamav/clamd.ctl`
   - TCP fallback: `localhost:3310`
   - Memory usage: ~500MB-1GB
   - Automatic startup via systemd

2. **FreshClam** (`clamav-freshclam`)
   - Automatic virus definition updater
   - Updates multiple times daily
   - Ensures protection against latest threats
   - Runs as systemd service

3. **Python Service** (`virus_scanning_service.py`)
   - Python wrapper around ClamAV
   - Graceful error handling
   - Comprehensive logging
   - Singleton pattern for efficiency

### Scanning Flow

```
User Upload → File Received → Virus Scan → Clean? → Continue Processing
                                          ↓
                                        Infected → Reject & Delete
```

1. User uploads file via frontend
2. Backend receives file content (max 100MB)
3. **Virus scan runs immediately** before any processing
4. If infected: HTTP 400 error, file deleted, user notified
5. If clean: Continue to metadata stripping → S3 upload → database entry

## Implementation Details

### Synchronous Scanning

**Why Synchronous?**
- User requirement: scan before file is accepted
- Better security: infected files never reach storage
- Acceptable performance: 20 docs/week workload
- Clear user feedback: scan status visible

**Performance:**
- Small files (<1MB): 1-2 seconds
- Medium files (1-10MB): 2-5 seconds
- Large files (10-100MB): 5-15 seconds

### Detection Capabilities

ClamAV detects:
- ✅ Viruses (8+ million signatures)
- ✅ Trojans and backdoors
- ✅ Malware and spyware
- ✅ Ransomware
- ✅ Exploits in documents (PDF, DOC, etc.)
- ✅ Malicious scripts and macros
- ✅ Archive bombs (ZIP, RAR)
- ✅ Phishing content

### File Types Scanned

All uploaded file types are scanned, including:
- Documents: PDF, DOC, DOCX, ODT
- Images: JPG, PNG, GIF, BMP, TIFF
- Spreadsheets: XLS, XLSX, CSV, ODS
- Archives: ZIP
- Text files: TXT, RTF

## Configuration

### Environment Variables

No environment variables required. ClamAV runs as a local service.

### ClamAV Configuration Files

**Main config:** `/etc/clamav/clamd.conf`
```conf
# Default Ubuntu/Debian configuration works out-of-box
LocalSocket /var/run/clamav/clamd.ctl
TCPSocket 3310
MaxFileSize 100M
MaxScanSize 100M
```

**Update config:** `/etc/clamav/freshclam.conf`
```conf
# Automatic updates from ClamAV database
DatabaseMirror database.clamav.net
Checks 24
```

## Service Management

### Check Status

```bash
# Check daemon status
sudo systemctl status clamav-daemon

# Check update service
sudo systemctl status clamav-freshclam

# Test connection
clamdscan --version
```

### Start/Stop Services

```bash
# Start services
sudo systemctl start clamav-daemon
sudo systemctl start clamav-freshclam

# Stop services (not recommended in production)
sudo systemctl stop clamav-daemon
sudo systemctl stop clamav-freshclam

# Restart services
sudo systemctl restart clamav-daemon
```

### Update Virus Definitions

```bash
# Manual update (automatic updates run daily)
sudo freshclam

# Force update
sudo freshclam --quiet
```

### View Logs

```bash
# ClamAV daemon logs
sudo journalctl -u clamav-daemon -f

# Update logs
sudo journalctl -u clamav-freshclam -f

# Application logs (virus scan results)
tail -f /tmp/backend.log | grep -i virus
```

## Testing

### Test Script

Run the comprehensive test suite:

```bash
cd /opt/foi-archive/backend
source .venv/bin/activate
python test_virus_scanning.py
```

**Tests performed:**
1. ✅ Service availability check
2. ✅ Clean file scanning
3. ✅ EICAR test virus detection
4. ✅ Large file performance

### Manual Testing

**Test 1: Upload Clean File**
```bash
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@clean_document.pdf" \
  -F "title=Test Document" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"
```
Expected: Success (200)

**Test 2: Upload EICAR Test Virus**
```bash
# Create EICAR test file (harmless test virus)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt

# Try to upload
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@eicar.txt" \
  -F "title=Test Virus" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"
```
Expected: Error 400 with virus detection message

**Test 3: Health Check**
```bash
curl https://www.haqnow.com/api/health
```
Expected response:
```json
{
  "status": "healthy",
  "message": "HaqNow API is running",
  "services": {
    "virus_scanning": {
      "available": true,
      "scanner": "ClamAV",
      "version": "ClamAV 0.103.x..."
    }
  }
}
```

## Monitoring

### Health Endpoint

```bash
curl -s https://www.haqnow.com/api/health | jq '.services.virus_scanning'
```

### Metrics to Monitor

1. **Service Availability**: `virus_scanning.available = true`
2. **Version Info**: Ensure virus definitions are recent
3. **Scan Performance**: Check logs for scan duration
4. **Detection Rate**: Monitor rejected uploads in logs

### Log Examples

**Clean File:**
```json
{
  "event": "File scan completed - clean",
  "filename": "document.pdf",
  "size": 524288,
  "timestamp": "2025-11-13T10:30:45Z"
}
```

**Infected File:**
```json
{
  "event": "VIRUS DETECTED in uploaded file",
  "filename": "malicious.pdf",
  "virus": "Win.Trojan.Generic",
  "size": 1048576,
  "timestamp": "2025-11-13T10:31:22Z"
}
```

## Troubleshooting

### Problem: "ClamAV daemon not available"

**Symptoms:**
- Logs show: "ClamAV daemon not available - virus scanning disabled"
- Uploads succeed without scanning

**Solutions:**
```bash
# Check if daemon is running
sudo systemctl status clamav-daemon

# If not running, start it
sudo systemctl start clamav-daemon

# Check for errors
sudo journalctl -u clamav-daemon -n 50

# Restart backend to reconnect
sudo systemctl restart foi-archive
```

### Problem: "Authentication failed" or connection errors

**Solution:**
```bash
# Check socket permissions
ls -la /var/run/clamav/clamd.ctl

# Should be accessible by backend user
# If not, add backend user to clamav group
sudo usermod -aG clamav www-data

# Restart services
sudo systemctl restart clamav-daemon
sudo systemctl restart foi-archive
```

### Problem: Outdated virus definitions

**Symptoms:**
- Known viruses not detected
- Virus definition version is old

**Solution:**
```bash
# Update definitions manually
sudo systemctl stop clamav-freshclam
sudo freshclam
sudo systemctl start clamav-freshclam

# Verify update
clamdscan --version
```

### Problem: High memory usage

**Symptoms:**
- Server running out of memory
- ClamAV daemon using >2GB RAM

**Solution:**
```bash
# Check current usage
ps aux | grep clam

# Restart daemon to free memory
sudo systemctl restart clamav-daemon

# Consider adding swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problem: Slow scans

**Symptoms:**
- File uploads take >30 seconds
- Users complaining about upload speed

**Diagnosis:**
```bash
# Check system resources
top
htop

# Monitor scan times in logs
tail -f /tmp/backend.log | grep "virus scan"

# Test scan speed manually
clamdscan /path/to/test/file.pdf
```

**Solutions:**
- Ensure ClamAV daemon is running (not using clamscan CLI)
- Check server CPU/RAM availability
- Consider file size limits if files are very large

## Security Considerations

### Why ClamAV?

1. **Privacy-First**: All scanning happens on-premises
2. **No Data Sharing**: Files never leave your infrastructure
3. **Open Source**: Auditable, no vendor lock-in
4. **Free**: No API costs or subscriptions
5. **Proven**: Used by millions of servers worldwide

### Limitations

1. **Zero-Day Attacks**: ClamAV may not detect brand-new malware
2. **Single Engine**: Only one AV engine (commercial solutions use multiple)
3. **False Negatives**: Advanced malware may evade detection
4. **False Positives**: Rare but possible on legitimate files

### Defense in Depth

Virus scanning is one layer of security. Other protections:
- ✅ File size limits (100MB)
- ✅ File type validation
- ✅ Metadata stripping (privacy protection)
- ✅ Rate limiting
- ✅ CAPTCHA verification
- ✅ TLS encryption

## Performance Impact

### Resource Usage

**ClamAV Daemon:**
- Memory: 500MB-1GB (depending on database size)
- CPU: <5% during scans
- Disk: ~200MB for virus definitions

**Per Upload:**
- Scan time: 1-5 seconds (typical document)
- Memory: Minimal (scanning in daemon)
- CPU: Brief spike during scan

### Optimization

For your workload (20 docs/week):
- ✅ No optimization needed
- ✅ Default configuration is optimal
- ✅ Synchronous scanning is fine

For higher volumes (100+ docs/day):
- Consider async scanning
- Add more RAM for larger file buffers
- Use separate scanning server

## Maintenance

### Daily Tasks
- ✅ Automatic (via cron): Virus definition updates
- ✅ Automatic: Service health checks

### Weekly Tasks
- [ ] Review scan logs for patterns
- [ ] Check for rejected uploads
- [ ] Verify service uptime

### Monthly Tasks
- [ ] Review ClamAV version (Ubuntu updates it)
- [ ] Check disk usage for logs
- [ ] Verify backup coverage

### Annual Tasks
- [ ] Review scanning policy
- [ ] Evaluate need for additional scanners
- [ ] Audit scan effectiveness

## Future Enhancements

### Potential Improvements

1. **Admin Dashboard**
   - View scan statistics
   - See detection history
   - Monitor service health

2. **Async Scanning**
   - Accept upload immediately
   - Scan in background
   - Quarantine if infected later

3. **Multi-Engine Scanning**
   - Add additional AV engines
   - Cross-reference detections
   - Reduce false positives/negatives

4. **Custom Signatures**
   - Add platform-specific rules
   - Block known malicious patterns
   - Customize for document types

5. **Scan History Database**
   - Track all scan results
   - Generate reports
   - Compliance audit trail

## Support & Resources

### ClamAV Documentation
- Official Docs: https://docs.clamav.net/
- GitHub: https://github.com/Cisco-Talos/clamav
- FAQ: https://docs.clamav.net/faq/

### Testing Resources
- EICAR Test Files: https://www.eicar.org/
- Malware samples (research): https://www.malware-traffic-analysis.net/

### Community
- ClamAV Mailing List: https://www.clamav.net/contact
- Ubuntu ClamAV Guide: https://ubuntu.com/server/docs/tools-clamav

## Deployment Checklist

When deploying virus scanning:

- [x] ClamAV installed via install.sh or deploy.sh
- [x] Virus definitions updated (freshclam)
- [x] Daemon running (systemctl status clamav-daemon)
- [x] Python library installed (clamd>=1.0.2)
- [x] Service integrated in upload API
- [x] Frontend UI updated
- [x] Health check endpoint configured
- [x] Logs monitored for scan results
- [x] Test script validated
- [x] Documentation reviewed

## Conclusion

ClamAV virus scanning provides robust, privacy-preserving malware protection for HaqNow's document uploads. The implementation is:

- ✅ **Secure**: Industry-standard antivirus protection
- ✅ **Private**: No external API calls or data sharing
- ✅ **Free**: Open-source with no licensing costs
- ✅ **Automatic**: Updates and maintenance handled automatically
- ✅ **Integrated**: Seamless part of upload flow
- ✅ **Monitored**: Health checks and comprehensive logging

For a whistleblower platform handling sensitive documents, this provides essential security without compromising the platform's core privacy principles.

