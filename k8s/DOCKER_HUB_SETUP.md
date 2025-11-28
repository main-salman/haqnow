# 🐳 Docker Hub Setup Guide

## Problem

Docker images need to be pushed to a registry that Kubernetes can access. We're using Docker Hub, which requires repositories to exist before pushing.

## Solution: Create Docker Hub Repositories

### Step 1: Create Docker Hub Account (if needed)

1. Go to https://hub.docker.com
2. Sign up or sign in

### Step 2: Create Repositories

Create these three public repositories:

1. **haqnow/backend-api**
   - Go to https://hub.docker.com/repository/create
   - Name: `haqnow/backend-api`
   - Visibility: Public
   - Description: "HaqNow Backend API"

2. **haqnow/worker**
   - Go to https://hub.docker.com/repository/create
   - Name: `haqnow/worker`
   - Visibility: Public
   - Description: "HaqNow Document Processing Worker"

3. **haqnow/frontend**
   - Go to https://hub.docker.com/repository/create
   - Name: `haqnow/frontend`
   - Visibility: Public
   - Description: "HaqNow Frontend"

### Step 3: Set Docker Hub Credentials (Optional but Recommended)

```bash
# Add to .env or export
export DOCKER_USER="your_dockerhub_username"
export DOCKER_PASSWORD="your_dockerhub_password"
```

### Step 4: Deploy

```bash
./scripts/deploy.sh patch
```

## Alternative: Use Private Registry

If you prefer not to use Docker Hub:

1. Set up Exoscale Container Registry (CRS) - requires Terraform
2. Use GitHub Container Registry (ghcr.io)
3. Use a private registry

## Troubleshooting

### "push access denied"

- Repository doesn't exist → Create it on Docker Hub
- Wrong credentials → Check DOCKER_USER and DOCKER_PASSWORD
- Private repository → Make it public or use credentials

### "authorization failed"

- Need to login: `docker login -u your_username`
- Or set DOCKER_PASSWORD environment variable

