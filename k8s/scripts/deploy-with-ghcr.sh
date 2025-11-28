#!/bin/bash
# Deploy to SKS using GitHub Container Registry

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get GitHub user from gh CLI
GITHUB_USER=$(gh api user -q .login 2>/dev/null || echo "main-salman")

echo -e "${GREEN}🚀 Deploying to SKS using GitHub Container Registry${NC}"
echo ""

# Check if token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    echo ""
    echo "Please create a GitHub token with write:packages and read:packages scopes:"
    echo "  https://github.com/settings/tokens/new"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN=\"ghp_your_token_here\""
    echo "  ./k8s/scripts/deploy-with-ghcr.sh"
    echo ""
    exit 1
fi

# Login to GHCR
echo -e "${YELLOW}Logging in to GitHub Container Registry...${NC}"
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin || {
    echo -e "${RED}❌ Failed to login to GHCR${NC}"
    echo "Make sure your token has write:packages and read:packages scopes"
    exit 1
}
echo -e "${GREEN}✅ Logged in to GHCR${NC}"
echo ""

# Set environment variables
export REGISTRY="ghcr.io"
export DOCKER_USER="$GITHUB_USER"
export DOCKER_PASSWORD="$GITHUB_TOKEN"
export KUBECONFIG="$(pwd)/k8s/.kubeconfig"

echo -e "${GREEN}Configuration:${NC}"
echo "  Registry: $REGISTRY"
echo "  User: $DOCKER_USER"
echo "  Kubeconfig: $KUBECONFIG"
echo ""

# Deploy
echo -e "${GREEN}Starting deployment...${NC}"
./scripts/deploy.sh patch

