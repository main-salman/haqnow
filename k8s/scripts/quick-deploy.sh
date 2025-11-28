#!/bin/bash
# Quick deployment script - builds images and deploys to SKS

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Quick Deploy to SKS${NC}"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check kubectl
export KUBECONFIG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../k8s/kubeconfig" && pwd)"
if ! kubectl cluster-info > /dev/null 2>&1; then
    echo -e "${RED}❌ Kubernetes cluster not accessible${NC}"
    exit 1
fi

# Set Docker user
export DOCKER_USER="${DOCKER_USER:-haqnow}"

# Step 1: Build and push images
echo -e "${YELLOW}Step 1: Building and pushing container images...${NC}"
"$(dirname "$0")/build-and-push-images.sh"

# Step 2: Deploy application
echo ""
echo -e "${YELLOW}Step 2: Deploying application to SKS...${NC}"
"$(dirname "$0")/deploy.sh"

# Step 3: Test deployment
echo ""
echo -e "${YELLOW}Step 3: Testing deployment...${NC}"
"$(dirname "$0")/test-deployment.sh"

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run Playwright e2e tests: cd frontend && npm run test:e2e"
echo "  2. Update DNS to point to NLB IP: 159.100.246.117"
echo "  3. Create VM snapshot for rollback"
echo "  4. Delete old VM after verification"

