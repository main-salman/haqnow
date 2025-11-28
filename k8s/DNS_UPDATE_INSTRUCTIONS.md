# 🌐 DNS Update Instructions for SKS Migration

## Current Configuration

- **Old VM IP**: 194.182.164.77 (current DNS target)
- **New SKS NLB IP**: 159.100.246.117 (target after migration)

## DNS Records to Update

Once the SKS deployment is complete and tested:

### Step 1: Update DNS A Records

Update your DNS provider (wherever www.haqnow.com and haqnow.com are managed):

```
www.haqnow.com  -> A record -> 159.100.246.117
haqnow.com      -> A record -> 159.100.246.117
```

**TTL**: Set to 300 seconds (5 minutes) for faster propagation during migration

### Step 2: Verify DNS Propagation

```bash
# Check DNS resolution
dig www.haqnow.com +short
dig haqnow.com +short

# Should return: 159.100.246.117
```

### Step 3: Test New Endpoint

```bash
# Test health endpoint
curl https://www.haqnow.com/api/health

# Test frontend
curl -I https://www.haqnow.com
```

### Step 4: Update .env (After DNS Switch)

Once DNS is pointing to SKS and verified:

1. Remove VM IP from ALLOWED_ORIGINS:
   ```
   ALLOWED_ORIGINS=http://www.haqnow.com,https://www.haqnow.com,http://haqnow.com,https://haqnow.com,http://159.100.246.117,https://159.100.246.117
   ```

2. Remove VM IP from ALLOWED_HOSTS:
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,www.haqnow.com,haqnow.com,159.100.246.117
   ```

3. Update secrets in Kubernetes:
   ```bash
   ./k8s/scripts/create-secrets.sh
   kubectl rollout restart deployment/backend-api -n haqnow
   ```

## Rollback Plan

If issues occur after DNS switch:

1. **Quick rollback**: Change DNS back to VM IP (194.182.164.77)
2. **Full rollback**: Follow rollback procedure in DEPLOYMENT_GUIDE.md

## Migration Timeline

1. **Pre-migration**: DNS points to VM (194.182.164.77)
2. **During migration**: Both IPs in ALLOWED_ORIGINS/HOSTS
3. **Post-migration**: DNS points to SKS (159.100.246.117), VM IP removed

## Notes

- DNS propagation can take 5 minutes to 48 hours depending on TTL
- Keep VM running until DNS is fully propagated and verified
- Monitor application logs after DNS switch
- Run Playwright e2e tests after DNS update

