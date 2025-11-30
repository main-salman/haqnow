# ⚡ Fast Deployment Guide

## Overview

The deployment process has been optimized for speed. The new `deploy.sh` script is the **single source of truth** for all deployments and includes:

- **Parallel Docker builds** (backend, worker, frontend build simultaneously)
- **Multi-stage Dockerfiles** with intelligent caching
- **Registry cache reuse** for faster subsequent builds
- **Buildx cache mounts** for pip/npm dependency caching

## Performance Targets

- **First build**: ~5-8 minutes (all dependencies)
- **Code-only changes**: ~2-3 minutes (cached dependencies)
- **Dependency changes**: ~5-7 minutes (cached base layers)

## Usage

```bash
# Auto-detect deployment target (SKS or VM)
./scripts/deploy.sh patch

# Explicit SKS deployment
./scripts/deploy.sh patch --sks

# Explicit VM deployment
./scripts/deploy.sh patch --vm
```

## How It Works

### 1. Multi-Stage Dockerfiles

All Dockerfiles now use multi-stage builds:

```dockerfile
# Stage 1: Base (cached unless base image changes)
FROM python:3.11-slim AS base
# Install system dependencies

# Stage 2: Dependencies (cached unless requirements change)
FROM base AS dependencies
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r requirements.txt

# Stage 3: Application (rebuilds on code changes)
FROM dependencies AS app
COPY . .
```

**Benefits**:
- System dependencies cached separately from Python packages
- Python packages cached separately from application code
- Only changed layers rebuild

### 2. Parallel Builds

The `deploy.sh` script builds all three images simultaneously:

```bash
# Build backend (background)
docker buildx build ... backend/ &
BACKEND_PID=$!

# Build worker (background)
docker buildx build ... worker/ &
WORKER_PID=$!

# Build frontend (background)
docker buildx build ... frontend/ &
FRONTEND_PID=$!

# Wait for all to complete
wait $BACKEND_PID && wait $WORKER_PID && wait $FRONTEND_PID
```

**Benefits**:
- Total build time = longest single build (not sum of all builds)
- CPU/network resources utilized efficiently

### 3. Registry Caching

Builds use `--cache-from` to pull cached layers from registry:

```bash
docker buildx build \
    --cache-from type=registry,ref=ghcr.io/main-salman/backend-api:latest \
    --cache-to type=inline \
    ...
```

**Benefits**:
- Unchanged layers pulled from registry (no rebuild)
- Subsequent builds are much faster
- Works across different machines/builds

### 4. Buildx Cache Mounts

Dependency installs use cache mounts:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r requirements.txt
```

**Benefits**:
- pip/npm caches persist between builds
- Faster dependency installation
- Reduces network usage

## Deployment Flow

1. **Version Update** (~5s)
   - Increments version in `package.json`
   - Updates version files

2. **Frontend Build** (~30-60s)
   - Local npm build (not Docker)
   - Fast TypeScript compilation

3. **Git Commit & Push** (~10s)
   - Commits changes
   - Pushes to GitHub

4. **Docker Builds** (~2-8 min)
   - Parallel builds with caching
   - Registry cache reuse
   - Buildx cache mounts

5. **Image Push** (~30-60s)
   - Parallel pushes to GHCR
   - Fast upload with existing layers

6. **Kubernetes Deploy** (~30-60s)
   - Update secrets
   - Apply manifests
   - Rollout restart
   - Wait for readiness

**Total**: ~3-10 minutes (depending on what changed)

## Troubleshooting

### Build Still Slow?

1. **Check Docker Buildx is enabled**:
   ```bash
   docker buildx version
   docker buildx create --use --name haqnow-builder
   ```

2. **Verify cache is working**:
   ```bash
   # Check build logs for "CACHED" layers
   docker buildx build ... --progress=plain
   ```

3. **Clear cache if needed**:
   ```bash
   docker builder prune -a
   ```

### Images Not Pulling?

1. **Check imagePullSecrets**:
   ```bash
   kubectl get secrets -n haqnow | grep ghcr
   ```

2. **Verify GHCR login**:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u main-salman --password-stdin
   ```

### Deployment Fails?

1. **Check pod status**:
   ```bash
   kubectl get pods -n haqnow
   kubectl describe pod <pod-name> -n haqnow
   ```

2. **Check logs**:
   ```bash
   kubectl logs <pod-name> -n haqnow
   ```

## Migration from Old Process

The old process used separate scripts:
- `k8s/scripts/build-and-push-images.sh`
- `k8s/scripts/deploy.sh`
- `k8s/scripts/create-secrets.sh`

**New process**: Everything in `scripts/deploy.sh` (single source of truth)

Old scripts still exist for manual use but are integrated into `deploy.sh`.

## Next Steps

1. **Test the fast deployment**:
   ```bash
   ./scripts/deploy.sh patch
   ```

2. **Monitor build times**:
   - First build: ~5-8 min
   - Subsequent builds: ~2-3 min (code changes only)

3. **Optimize further if needed**:
   - Consider pre-built base images
   - Use GitHub Actions for CI/CD builds
   - Implement build caching strategies

