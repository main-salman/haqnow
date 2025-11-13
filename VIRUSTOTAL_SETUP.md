# 🛡️ VirusTotal Virus Scanning Setup

## Overview

HaqNow now uses **VirusTotal** for virus and malware scanning. This cloud-based solution offers:

- ✅ **500 scans/day** free tier (vs your 20 docs/week = ~3/day)
- ✅ **70+ antivirus engines** (Kaspersky, McAfee, Avast, etc.)
- ✅ **Zero memory footprint** (no server resources needed)
- ✅ **Better detection rates** than single-engine solutions
- ✅ **Automatic updates** (always latest virus definitions)

## Step 1: Get Your Free API Key

### Create VirusTotal Account

1. **Go to VirusTotal**: https://www.virustotal.com/gui/join-us
2. **Sign up** with your email address
3. **Verify** your email
4. **Login** to your account

### Get Your API Key

1. Click your **profile icon** (top right)
2. Go to **API Key** section
3. Copy your **API key** (looks like: `a1b2c3d4e5...`)

**Note**: Keep this key private! It's like a password.

## Step 2: Add API Key to Your .env File

Open `/Users/salman/Documents/fadih/.env` and add your API key:

```bash
# Find this line:
VIRUSTOTAL_API_KEY=YOUR_API_KEY_HERE

# Replace with your actual key:
VIRUSTOTAL_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Important**: Never commit this key to git! The `.env` file is in `.gitignore`.

## Step 3: Deploy to Production

```bash
cd /Users/salman/Documents/fadih
SERVER_HOST=194.182.164.77 ./scripts/deploy.sh patch
```

This will:
- ✅ Remove ClamAV (saves ~1GB RAM)
- ✅ Deploy VirusTotal integration
- ✅ Sync your .env file to the server
- ✅ Restart backend with new configuration

## Step 4: Verify It's Working

### Test the Health Endpoint

```bash
curl -s https://www.haqnow.com/api/health | python3 -m json.tool
```

Should show:

```json
{
  "status": "healthy",
  "services": {
    "virus_scanning": {
      "available": true,
      "scanner": "VirusTotal",
      "engines": "70+",
      "daily_limit": "500 scans/day",
      "rate_limit": "4 requests/minute"
    }
  }
}
```

### Test File Upload

1. Go to: https://www.haqnow.com/upload-document
2. You should see: **"All uploaded files are automatically scanned for viruses and malware"**
3. Upload a normal file → Should work fine
4. Upload EICAR test virus → Should be rejected

## EICAR Test Virus

To test virus detection, create a test file:

```bash
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt
```

Then upload `eicar.txt` to your site. It should be rejected with a message showing multiple antivirus engines detected it.

**Note**: EICAR is a harmless test signature used to verify antivirus is working.

## How It Works

### Upload Flow with VirusTotal

1. User uploads file
2. Backend calculates file SHA256 hash
3. **Check if file already scanned** (by hash lookup)
   - If yes: Use cached results (instant)
   - If no: Upload file to VirusTotal
4. Wait for scan results (2-30 seconds)
5. Parse results from 70+ engines
6. **If malicious/suspicious**: Reject upload, delete file
7. **If clean**: Continue to metadata stripping → storage

### Performance

- **Already scanned files**: < 1 second (hash lookup)
- **New files**: 5-30 seconds (upload + scan)
- **Your workload** (3 files/day): Well within limits

## VirusTotal Free Tier Limits

- **Daily requests**: 500/day
- **Rate limit**: 4 requests/minute  
- **Your usage**: ~3-4 per day (20 docs/week)
- **Headroom**: 125x your current needs! ✅

## Privacy Considerations

⚠️ **Important**: Files uploaded to VirusTotal become part of their public database (shared with security researchers).

**For HaqNow:**
- Documents are submitted by whistleblowers for **public exposure**
- Once approved by admin, they're **publicly accessible** on your site
- VirusTotal scanning happens **before publication**
- Trade-off: Better security (70+ engines) vs. pre-publication visibility

**If privacy is critical**: You can upgrade to VirusTotal Premium for private scanning, or use ClamAV despite memory constraints.

## Comparison: VirusTotal vs. ClamAV

| Feature | VirusTotal | ClamAV |
|---------|------------|---------|
| Cost | Free (500/day) | Free |
| Engines | 70+ | 1 |
| Detection Rate | Excellent | Good |
| Memory | 0 MB | ~1000 MB |
| Speed | 5-30 sec | 1-5 sec |
| Updates | Automatic | Daily |
| Privacy | Public database | On-premises |
| Setup | API key only | Install daemon |

## Troubleshooting

### Error: "VirusTotal API key not configured"

**Solution**: Add your API key to `.env` file and redeploy.

### Error: "Upload failed: 401"

**Solution**: Your API key is invalid. Check:
1. Key copied correctly (no extra spaces)
2. Key is active (not revoked)
3. Get new key from VirusTotal

### Error: "Upload failed: 429"

**Solution**: Rate limit exceeded. Wait 1 minute and try again.

### Error: "Analysis timeout"

**Solution**: VirusTotal is slow. File is safe to retry.

## Monitoring Usage

### Check Your API Usage

1. Login to VirusTotal
2. Go to **API Key** section
3. View **usage statistics**

You should see ~3-4 requests per day (well below 500 limit).

### Backend Logs

Check scan results in logs:

```bash
ssh root@www.haqnow.com
tail -f /tmp/backend.log | grep -i virus
```

You'll see:
- `Scanning file with VirusTotal`
- `File scan completed - clean` (for safe files)
- `VIRUS DETECTED by VirusTotal` (for infected files)

## Cost

**Current**: $0/month (free tier)

**If you exceed 500/day**: Upgrade to VirusTotal Premium (~$550/month) or add rate limiting.

**Your usage**: 20 docs/week = ~3/day = **0.6% of free tier** ✅

## Summary

✅ **Free tier is very generous** for your needs (125x headroom)  
✅ **Better security** than single-engine ClamAV  
✅ **Zero memory usage** (solves OOM issue)  
✅ **Easy setup** (just API key)  
✅ **Automatic updates** (always protected)  

⚠️ **Privacy trade-off**: Files visible to VirusTotal (acceptable for public whistleblower documents)

## Quick Commands

```bash
# Deploy with VirusTotal
SERVER_HOST=194.182.164.77 ./scripts/deploy.sh patch

# Check health
curl -s https://www.haqnow.com/api/health | jq '.services.virus_scanning'

# View logs
ssh root@www.haqnow.com "tail -f /tmp/backend.log | grep -i virus"
```

---

**Ready to deploy!** Just add your API key to `.env` and run deploy.sh 🚀

