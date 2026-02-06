# 🐳 GitHub Container Registry (GHCR) Setup

Alternative to Docker Hub - uses your existing GitHub account.

## Advantages

- ✅ No need to create repositories manually
- ✅ Uses existing GitHub authentication
- ✅ Private by default (more secure)
- ✅ Integrated with GitHub

## Setup

### Step 1: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Docker Registry"
4. Scopes: Check `write:packages` and `read:packages`
5. Generate token and copy it

### Step 2: Login to GHCR

```bash
export GITHUB_USER="main-salman"  # Your GitHub username
export GITHUB_TOKEN="ghp_..."     # Token from Step 1

echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
```

### Step 3: Deploy Using GHCR

```bash
export REGISTRY="ghcr.io"
export DOCKER_USER="main-salman"  # Your GitHub username
export DOCKER_PASSWORD="$GITHUB_TOKEN"  # Or set in .env

./scripts/deploy.sh patch
```

## Update Kubernetes Manifests

The manifests will automatically use the registry you specify. Images will be:
- `ghcr.io/main-salman/backend-api:latest`
- `ghcr.io/main-salman/worker:latest`
- `ghcr.io/main-salman/frontend:latest`

## Make Images Public (Optional)

By default, GHCR images are private. To make them public:

1. Go to https://github.com/main-salman?tab=packages
2. Click on each package
3. Go to "Package settings" → "Change visibility" → "Public"

Or use GitHub CLI:
```bash
gh api user/packages/container/backend-api -X PATCH -f visibility=public
gh api user/packages/container/worker -X PATCH -f visibility=public
gh api user/packages/container/frontend -X PATCH -f visibility=public
```

## Fix 403 Forbidden when GitHub Actions pushes (e.g. backend-base)

If the "Build and Push Docker Images" workflow fails with:

```text
ERROR: failed to push ghcr.io/main-salman/backend-base:latest: ... 403 Forbidden
```

the package may have been created by a different login (e.g. `deploy.sh` with a PAT), so the workflow’s `GITHUB_TOKEN` has no write access.

**Fix:** Grant the repository permission to write to the package:

1. Open https://github.com/main-salman?tab=packages (or the org that owns the package).
2. Click the **backend-base** package.
3. Open **Package settings** (left sidebar).
4. Under **Danger Zone** or **Manage Actions access**, click **Add repository** (or **Manage Actions access**).
5. Select repository **main-salman/haqnow** and set role **Write**.
6. Save. Re-run the failed workflow.

After this, the workflow can push `backend-base:latest` without 403.

