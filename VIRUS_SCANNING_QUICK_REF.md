# 🦠 Virus Scanning - Quick Reference

## What It Does
All files uploaded to HaqNow are automatically scanned for viruses and malware using ClamAV before processing.

## Deploy
```bash
./scripts/deploy.sh patch
```

## Test After Deployment

### 1. Check Health
```bash
curl -s "https://www.haqnow.com/api/health" | jq '.services.virus_scanning'
```
Should show: `"available": true`

### 2. Test Clean Upload
```bash
echo "Test document" > clean.txt
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@clean.txt" \
  -F "title=Test" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"
```
Should: ✅ Succeed

### 3. Test Virus Detection
```bash
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > virus.txt
curl -X POST https://www.haqnow.com/api/file-uploader/upload \
  -F "file=@virus.txt" \
  -F "title=Test Virus" \
  -F "country=United States" \
  -F "state=Federal / National" \
  -F "document_language=english"
```
Should: ❌ Reject with "Virus detected"

## Monitor

### Check Services (on server)
```bash
ssh root@www.haqnow.com
sudo systemctl status clamav-daemon clamav-freshclam
```

### View Logs
```bash
ssh root@www.haqnow.com
tail -f /tmp/backend.log | grep -i virus
```

## Troubleshooting

### ClamAV Not Running
```bash
ssh root@www.haqnow.com
sudo systemctl start clamav-daemon
sudo systemctl restart foi-archive
```

### Update Virus Definitions
```bash
ssh root@www.haqnow.com
sudo freshclam
```

## User Experience

**Frontend:**
- 🛡️ Green badge: "All files scanned for viruses..."
- ⏳ During upload: "Scanning file for viruses..."
- ✅ Clean file: Proceeds normally
- ❌ Infected: Error message with virus name

**Performance:**
- Small files: 1-2 seconds
- Large files: 2-5 seconds
- Your workload (20/week): Negligible impact

## Key Files

- Service: `backend/app/services/virus_scanning_service.py`
- Integration: `backend/app/apis/file_uploader/__init__.py`
- Tests: `backend/test_virus_scanning.py`
- Docs: `documentation/VIRUS_SCANNING.md`

## Features

✅ Synchronous scanning (user waits)  
✅ Infected files immediately deleted  
✅ Privacy-first (on-premises scanning)  
✅ Free & open-source (ClamAV)  
✅ Auto-updates virus definitions  
✅ Comprehensive logging  
✅ Health monitoring  

## Cost
**$0** - Completely free, no API keys needed

## Security
- 8+ million virus signatures
- Updated multiple times daily
- Detects: viruses, trojans, malware, ransomware, exploits
- No external API calls (privacy preserved)

---

## Quick Commands

```bash
# Deploy
./scripts/deploy.sh patch

# Check health
curl -s https://www.haqnow.com/api/health | jq

# View logs
ssh root@www.haqnow.com "tail -f /tmp/backend.log | grep -i virus"

# Restart services
ssh root@www.haqnow.com "sudo systemctl restart clamav-daemon foi-archive"

# Update virus definitions
ssh root@www.haqnow.com "sudo freshclam"
```

## Success Checklist

- [ ] Deployed via `./scripts/deploy.sh patch`
- [ ] Health check shows `virus_scanning: available`
- [ ] Clean file upload succeeds
- [ ] EICAR test file rejected
- [ ] ClamAV services running on server
- [ ] Logs show scan entries
- [ ] Frontend shows security badge

---

**Everything configured! Deploy when ready.** 🚀

