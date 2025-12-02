#!/bin/bash

# FAST deployment script for HaqNow - Single source of truth
# Usage: ./scripts/deploy.sh [--env=dev|prod] [patch|minor|major] [--sks|--vm]
# 
# Examples:
#   ./scripts/deploy.sh --env=dev patch    # Deploy main branch to dev (haqnow.click)
#   ./scripts/deploy.sh --env=prod patch   # Deploy prod branch to production (haqnow.com)
#   ./scripts/deploy.sh patch              # Default: dev environment
#
# SPEED OPTIMIZATIONS:
# - Uses pre-built base image (dependencies built once)
# - App images just copy code (~10 seconds)
# - Frontend built locally, not in Docker
# - Target: 2-3 minutes total deployment time

set -e

# Parse arguments
DEPLOY_ENV="dev"  # Default to dev
VERSION_TYPE="patch"
DEPLOY_TARGET="auto"

for arg in "$@"; do
    case $arg in
        --env=*)
            DEPLOY_ENV="${arg#*=}"
            ;;
        --sks|--vm)
            DEPLOY_TARGET="$arg"
            ;;
        patch|minor|major)
            VERSION_TYPE="$arg"
            ;;
    esac
done

# Validate environment
if [[ "$DEPLOY_ENV" != "dev" && "$DEPLOY_ENV" != "prod" ]]; then
    echo "❌ Invalid environment: $DEPLOY_ENV"
    echo "   Usage: ./scripts/deploy.sh [--env=dev|prod] [patch|minor|major]"
    exit 1
fi

# Set environment-specific variables
if [ "$DEPLOY_ENV" = "prod" ]; then
    NAMESPACE="haqnow"
    IMAGE_TAG="latest"
    GIT_BRANCH="prod"
    DOMAIN="haqnow.com"
    MANIFESTS_DIR="k8s/manifests"
    SECRETS_SCRIPT="./k8s/scripts/create-secrets.sh"
    BACKEND_REPLICAS=2
else
    NAMESPACE="haqnow-dev"
    IMAGE_TAG="dev"
    GIT_BRANCH="main"
    DOMAIN="haqnow.click"
    MANIFESTS_DIR="k8s/manifests/dev"
    SECRETS_SCRIPT="./k8s/scripts/create-secrets-dev.sh"
    BACKEND_REPLICAS=1
fi

echo "🌐 Environment: $DEPLOY_ENV"
echo "🏷️  Image tag: $IMAGE_TAG"
echo "🌿 Git branch: $GIT_BRANCH"
echo "🔗 Domain: $DOMAIN"
echo ""

# Auto-detect deployment target
if [ "$DEPLOY_TARGET" = "auto" ]; then
    if [ -f .env ] && grep -q "^SKS_CLUSTER_ID=" .env && [ -n "$(grep "^SKS_CLUSTER_ID=" .env | cut -d'=' -f2)" ]; then
        DEPLOY_TARGET="--sks"
        echo "🔍 Auto-detected: SKS deployment"
    else
        DEPLOY_TARGET="--vm"
        echo "🔍 Auto-detected: VM deployment"
    fi
fi

# Get SERVER_HOST
if [ "$DEPLOY_TARGET" = "--sks" ]; then
    if [ -f .env ] && grep -q "^SKS_NLB_IP=" .env; then
        SERVER_HOST=${SERVER_HOST:-$(grep "^SKS_NLB_IP=" .env | cut -d'=' -f2)}
    else
        SERVER_HOST=${SERVER_HOST:-$DOMAIN}
    fi
else
    SERVER_HOST=${SERVER_HOST:-$DOMAIN}
fi

SSH_KEY_PATH=${SSH_KEY_PATH:-$HOME/.ssh/id_rsa}
SSH_OPTS="-i ${SSH_KEY_PATH} -o StrictHostKeyChecking=accept-new"

echo "🚀 Starting FAST deployment to $DEPLOY_ENV..."
echo "📦 Target: $([ "$DEPLOY_TARGET" = "--sks" ] && echo "SKS" || echo "VM")"
START_TIME=$(date +%s)

# Ensure we're on the correct branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$GIT_BRANCH" ]; then
    echo ""
    echo "⚠️  Warning: You're on branch '$CURRENT_BRANCH' but deploying to $DEPLOY_ENV (expects '$GIT_BRANCH')"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Step 1: Update version (~5s)
echo ""
echo "📦 Step 1: Updating version..."
scripts/update-version.sh $VERSION_TYPE
NEW_VERSION=$(grep '"version"' frontend/package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
echo "✅ Version: $NEW_VERSION"

# Step 2: Build frontend locally (~30s)
echo ""
echo "🔨 Step 2: Building frontend..."
cd frontend
npm run build
cd ..
echo "✅ Frontend built"

# Step 3: Commit and push (~10s)
echo ""
echo "📝 Step 3: Git commit & push..."
git add -A
if ! git diff --staged --quiet; then
    git commit -m "Deploy v$NEW_VERSION to $DEPLOY_ENV"
fi
git push origin $GIT_BRANCH
echo "✅ Pushed to GitHub ($GIT_BRANCH)"

# Step 4: Deploy
if [ "$DEPLOY_TARGET" = "--sks" ]; then
    # ============================================
    # SKS DEPLOYMENT (FAST - uses pre-built base)
    # ============================================
    echo ""
    echo "☸️  Step 4: SKS Deployment to $DEPLOY_ENV..."
    
    # Check Docker
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running!"
        exit 1
    fi
    
    # Check kubectl
    export KUBECONFIG="${KUBECONFIG:-$(pwd)/k8s/.kubeconfig}"
    if ! kubectl cluster-info > /dev/null 2>&1; then
        echo "❌ Kubernetes not accessible"
        exit 1
    fi
    
    # Load config from .env
    REGISTRY="ghcr.io"
    DOCKER_USER="main-salman"
    GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' .env 2>/dev/null | cut -d'=' -f2- | sed 's/#.*$//' | tr -d ' ')
    
    # Login to GHCR
    echo "🔐 Logging in to GHCR..."
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$DOCKER_USER" --password-stdin
    
    IMAGE_PREFIX="${REGISTRY}/${DOCKER_USER}"
    BUILD_START=$(date +%s)
    
    # Check if base image exists
    echo "🔍 Checking base image..."
    if ! docker manifest inspect ${IMAGE_PREFIX}/backend-base:latest > /dev/null 2>&1; then
        echo "⚠️  Base image not found. Building (one-time, ~10 min)..."
        echo "   This only happens once. Future deploys will be fast."
        docker buildx build --platform linux/amd64 \
            -f backend/Dockerfile.base \
            -t ${IMAGE_PREFIX}/backend-base:latest \
            --push backend/
        echo "✅ Base image built and pushed"
    else
        echo "✅ Base image exists (cached)"
    fi
    
    # Build app images (FAST - just copies code)
    echo ""
    echo "🔨 Building app images with tag :$IMAGE_TAG..."
    
    # Backend API (~10s)
    echo "  📦 backend-api:$IMAGE_TAG..."
    docker buildx build --platform linux/amd64 \
        -f backend/Dockerfile \
        -t ${IMAGE_PREFIX}/backend-api:${IMAGE_TAG} \
        --push backend/ &
    BACKEND_PID=$!
    
    # Worker (only build for prod, dev uses shared prod worker)
    if [ "$DEPLOY_ENV" = "prod" ]; then
        echo "  📦 worker:$IMAGE_TAG..."
        docker buildx build --platform linux/amd64 \
            -f backend/Dockerfile.worker \
            -t ${IMAGE_PREFIX}/worker:${IMAGE_TAG} \
            --push backend/ &
        WORKER_PID=$!
    fi
    
    # Frontend (~5s)
    echo "  📦 frontend:$IMAGE_TAG..."
    docker buildx build --platform linux/amd64 \
        -f frontend/Dockerfile \
        -t ${IMAGE_PREFIX}/frontend:${IMAGE_TAG} \
        --push frontend/ &
    FRONTEND_PID=$!
    
    # Wait for builds
    wait $BACKEND_PID && echo "  ✅ backend-api:$IMAGE_TAG done"
    if [ "$DEPLOY_ENV" = "prod" ]; then
        wait $WORKER_PID && echo "  ✅ worker:$IMAGE_TAG done"
    fi
    wait $FRONTEND_PID && echo "  ✅ frontend:$IMAGE_TAG done"
    
    BUILD_TIME=$(($(date +%s) - BUILD_START))
    echo "⏱️  Build time: ${BUILD_TIME}s"
    
    # Deploy to Kubernetes
    echo ""
    echo "🚀 Deploying to Kubernetes namespace: $NAMESPACE..."
    
    if [ "$DEPLOY_ENV" = "dev" ]; then
        # Dev deployment
        kubectl apply -f k8s/manifests/dev/namespace-dev.yaml
        kubectl apply -f k8s/manifests/dev/configmap-dev.yaml
        $SECRETS_SCRIPT
        kubectl apply -f k8s/manifests/dev/backend-deployment-dev.yaml
        kubectl apply -f k8s/manifests/dev/frontend-deployment-dev.yaml
        kubectl apply -f k8s/manifests/dev/ingress-dev.yaml
        
        # Restart dev pods to pull new images
        echo "🔄 Restarting dev pods..."
        kubectl rollout restart deployment/backend-api -n haqnow-dev
        kubectl rollout restart deployment/frontend -n haqnow-dev
        
        # Wait for rollout
        echo "⏳ Waiting for dev pods..."
        kubectl rollout status deployment/backend-api -n haqnow-dev --timeout=60s || true
        kubectl rollout status deployment/frontend -n haqnow-dev --timeout=60s || true
    else
        # Production deployment
        kubectl apply -f k8s/manifests/namespace.yaml
        kubectl apply -f k8s/manifests/configmap.yaml
        $SECRETS_SCRIPT
        kubectl apply -f k8s/manifests/backend-deployment.yaml
        kubectl apply -f k8s/manifests/worker-deployment.yaml
        kubectl apply -f k8s/manifests/frontend-deployment.yaml
        
        # Restart prod pods to pull new images
        echo "🔄 Restarting prod pods..."
        kubectl rollout restart deployment/backend-api -n haqnow
        kubectl rollout restart deployment/worker -n haqnow
        kubectl rollout restart deployment/frontend -n haqnow
        
        # Wait for rollout
        echo "⏳ Waiting for prod pods..."
        kubectl rollout status deployment/backend-api -n haqnow --timeout=60s || true
        kubectl rollout status deployment/worker -n haqnow --timeout=60s || true
        kubectl rollout status deployment/frontend -n haqnow --timeout=60s || true
    fi
    
    TOTAL_TIME=$(($(date +%s) - START_TIME))
    echo ""
    echo "============================================"
    echo "✅ SKS DEPLOYMENT COMPLETE!"
    echo "🌐 Environment: $DEPLOY_ENV"
    echo "⏱️  Total time: ${TOTAL_TIME}s ($(($TOTAL_TIME / 60))m $(($TOTAL_TIME % 60))s)"
    echo "🔗 URL: https://$DOMAIN"
    echo "📊 Status: kubectl get pods -n $NAMESPACE"
    echo "============================================"
    exit 0
fi

# ============================================
# VM DEPLOYMENT (Original fast method)
# ============================================
echo ""
echo "🖥️  Step 4: VM Deployment..."

if [ "$DEPLOY_ENV" = "dev" ]; then
    echo "⚠️  VM deployment is only supported for production"
    echo "   Dev environment requires SKS deployment"
    exit 1
fi

scp ${SSH_OPTS} .env root@${SERVER_HOST}:/tmp/.env
ssh ${SSH_OPTS} root@${SERVER_HOST} "rm -rf /tmp/frontend_dist" || true
scp -r ${SSH_OPTS} frontend/dist root@${SERVER_HOST}:/tmp/frontend_dist

ssh ${SSH_OPTS} root@${SERVER_HOST} "NEW_VERSION=$NEW_VERSION SERVER_HOST=$SERVER_HOST bash -s" << 'EOF'
cd /opt/foi-archive
git fetch origin && git reset --hard origin/prod
cp /tmp/.env .env && cp /tmp/.env backend/.env
sudo rm -rf /var/www/html/* && sudo cp -r /tmp/frontend_dist/* /var/www/html/
sudo systemctl restart foi-archive foi-archive-worker nginx
echo "✅ Services restarted"
EOF

TOTAL_TIME=$(($(date +%s) - START_TIME))
echo ""
echo "============================================"
echo "✅ VM DEPLOYMENT COMPLETE!"
echo "🌐 Environment: $DEPLOY_ENV"
echo "⏱️  Total time: ${TOTAL_TIME}s"
echo "🔗 URL: https://$DOMAIN"
echo "============================================"
