# 🦠 Virus Scanning Deployment Guide

## Summary

HaqNow now includes comprehensive virus and malware scanning using ClamAV for all file uploads. This implementation:

- ✅ **Synchronous Scanning**: Users see "Scanning for viruses..." during upload
- ✅ **Automatic Deletion**: Infected files immediately rejected
- ✅ **Privacy-First**: All scanning on-premises, no external APIs
- ✅ **Free & Open Source**: Zero licensing costs
- ✅ **Fully Integrated**: Part of deployment script and install process

## What Was Implemented

### Backend Changes
1. **New Service** (`virus_scanning_service.py`)
   - Interfaces with ClamAV daemon
   - Scans file content before processing
   - Returns (is_safe, virus_name) tuple

2. **Upload API Integration** (`file_uploader/__init__.py`)
   - Virus scan runs immediately after file validation
   - Before metadata stripping and S3 upload
   - Rejects infected files with HTTP 400 error

3. **Health Monitoring** (`main.py`)
   - Logs virus scanner status at startup
   - `/api/health` endpoint shows scanner status
   - Comprehensive error handling

### Frontend Changes
1. **User Communication** (`UploadDocumentPage.tsx`)
   - Green security badge: "All files scanned for viruses"
   - Toast message: "Scanning file for viruses..."
   - Clear error messages if virus detected

### Deployment Infrastructure
1. **Installation Script** (`install.sh`)
   - Installs ClamAV daemon and updates
   - Configures systemd services
   - Updates virus definitions

2. **Deployment Script** (`deploy.sh`)
   - Automatically installs/updates ClamAV
   - Refreshes virus definitions
   - Verifies services are running
   - Includes in health checks

### Documentation
1. **Test Suite** (`test_virus_scanning.py`)
   - Tests service availability
   - Tests clean file scanning
   - Tests EICAR virus detection
   - Tests performance

2. **Comprehensive Docs** (`documentation/VIRUS_SCANNING.md`)
   - Architecture overview
   - Configuration guide
   - Troubleshooting steps
   - Monitoring instructions

## Deployment Steps

### Option 1: Deploy to Production (Recommended)

```bash
# From your local machine
cd /Users/salman/Documents/fadih

# Deploy with virus scanning (automatic ClamAV installation)
./scripts/deploy.sh patch
```

This will:
1. ✅ Commit all changes to git
2. ✅ Build frontend locally
3. ✅ Push to GitHub
4. ✅ SSH to production server
5. ✅ Install/update ClamAV
6. ✅ Update virus definitions
7. ✅ Deploy new backend code
8. ✅ Restart services
9. ✅ Verify ClamAV is running

### Option 2: Local Development Testing

```bash
# Install ClamAV locally (macOS)
brew install clamav

# Start ClamAV daemon
brew services start clamav

# Update virus definitions
freshclam

# Install Python dependencies
cd backend
source .venv/bin/activate
pip install clamd>=1.0.2

# Test the service
python test_virus_scanning.py

# Run backend
python main.py
```

## Verification Steps

After deployment, verify everything works:

### 1. Check ClamAV Services

```bash
# SSH to production server
ssh root@www.haqnow.com

# Check daemon status
sudo systemctl status clamav-daemon
# Should show: Active: active (running)

# Check update service
sudo systemctl status clamav-freshclam
# Should show: Active: active (running)

# Verify virus definitions
sudo clamdscan --version
# Should show: ClamAV 0.103.x with recent database date
```

### 2. Check Backend Health

```bash
# From anywhere
curl -s "https://www.haqnow.com/api/health" | jq

# Should show:
# {
#   "status": "healthy",
#   "services": {
#     "virus_scanning": {
#       "available": true,
#       "scanner": "ClamAV",
#       "version": "ClamAV 0.103..."
#     }
#   }
# }
```

### 3. Test File Upload

**Test 1: Clean File (should succeed)**
```bash
# Create a clean test file
echo "This is a test document" > test_clean.txt

# Upload via API
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@test_clean.txt" \
  -F "title=Test Clean Document" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"

# Should return: 200 OK with file_url
```

**Test 2: EICAR Test Virus (should be rejected)**
```bash
# Create EICAR test file (harmless test virus)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > test_virus.txt

# Try to upload
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@test_virus.txt" \
  -F "title=Test Virus" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"

# Should return: 400 Bad Request
# Error message: "File upload rejected: Eicar-Signature"
```

### 4. Test via Web Interface

1. Go to: https://www.haqnow.com/upload-document
2. You should see green security badge: **"All uploaded files are automatically scanned for viruses and malware"**
3. Upload a normal PDF → Should show "Scanning file for viruses..." then succeed
4. Try uploading EICAR test file → Should show error message

### 5. Check Logs

```bash
# On production server
tail -f /tmp/backend.log | grep -i virus

# You should see entries like:
# "Starting virus scan", filename="document.pdf"
# "Virus scan completed - file is clean", filename="document.pdf"

# For infected files:
# "VIRUS DETECTED in uploaded file", filename="test.txt", virus="Eicar-Signature"
```

## Troubleshooting

### Problem: ClamAV Not Available

**Symptoms:**
- Health check shows `"available": false`
- Logs show: "ClamAV daemon not available"

**Solution:**
```bash
# SSH to server
ssh root@www.haqnow.com

# Install ClamAV
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon clamav-freshclam

# Update definitions
sudo freshclam

# Start services
sudo systemctl start clamav-daemon
sudo systemctl start clamav-freshclam

# Restart backend
sudo systemctl restart foi-archive
```

### Problem: Outdated Virus Definitions

**Solution:**
```bash
# Update manually
sudo systemctl stop clamav-freshclam
sudo freshclam
sudo systemctl start clamav-freshclam
```

### Problem: Upload Fails with "Scan Error"

**Check logs:**
```bash
tail -f /tmp/backend.log | grep -i "virus\|scan"
```

**Common causes:**
- ClamAV daemon not running
- Permissions issue with socket
- File too large for scan buffer

## Performance Notes

For your workload (20 documents/week):
- **Scan time**: 1-5 seconds per file
- **Memory**: ~500MB-1GB for ClamAV daemon
- **CPU**: Negligible impact
- **Storage**: ~200MB for virus definitions

This is well within acceptable limits for your use case.

## Security Benefits

1. ✅ **Malware Protection**: Blocks viruses, trojans, ransomware
2. ✅ **Document Exploits**: Detects malicious PDFs, DOCs, etc.
3. ✅ **Archive Scanning**: Scans inside ZIP files
4. ✅ **Regular Updates**: Virus definitions updated multiple times daily
5. ✅ **Privacy Preserved**: No external API calls, all on-premises

## Monitoring

### Daily
- ✅ Automatic: Virus definition updates
- ✅ Automatic: Service health checks

### Weekly
- Check scan logs for patterns
- Verify no unusual rejections
- Review service uptime

### Monthly
- Check ClamAV version (auto-updated via Ubuntu)
- Review disk usage for logs

## Files Changed

```
✅ NEW: backend/app/services/virus_scanning_service.py
✅ NEW: backend/test_virus_scanning.py
✅ NEW: documentation/VIRUS_SCANNING.md
✅ MODIFIED: backend/app/apis/file_uploader/__init__.py
✅ MODIFIED: backend/requirements.txt
✅ MODIFIED: backend/install.sh
✅ MODIFIED: backend/main.py
✅ MODIFIED: scripts/deploy.sh
✅ MODIFIED: frontend/src/pages/UploadDocumentPage.tsx
✅ UPDATED: history.txt
```

## Next Steps

1. **Deploy Now:**
   ```bash
   ./scripts/deploy.sh patch
   ```

2. **Verify Installation:**
   - Check health endpoint
   - Test clean file upload
   - Test EICAR virus detection

3. **Monitor:**
   - Check logs for scan entries
   - Verify ClamAV services running
   - Review rejected uploads (if any)

4. **Document:**
   - Update team about new security feature
   - Add to user FAQ if needed
   - Include in platform features

## Questions?

- **Documentation**: See `documentation/VIRUS_SCANNING.md`
- **Testing**: Run `python backend/test_virus_scanning.py`
- **Logs**: Check `/tmp/backend.log` on server
- **Health**: `curl https://www.haqnow.com/api/health`

## Success Criteria

After deployment, you should have:
- ✅ ClamAV running on production server
- ✅ Virus scanning integrated in upload flow
- ✅ Users notified about scanning (green badge)
- ✅ Infected files rejected with clear error
- ✅ Clean files processed normally
- ✅ Health endpoint showing scanner status
- ✅ Comprehensive logs for monitoring

---

## 🎉 Ready to Deploy!

Everything is configured and tested. Simply run:

```bash
./scripts/deploy.sh patch
```

The deployment script will handle:
- ClamAV installation
- Virus definition updates
- Code deployment
- Service restart
- Health verification

All document uploads will be automatically scanned for viruses! 🔒

