#!/bin/bash
# Build and push container images to Docker Hub (temporary - can switch to CRS later)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
# Using Docker Hub temporarily - can switch to CRS later
REGISTRY="docker.io"
DOCKER_USER="${DOCKER_USER:-haqnow}"  # Set DOCKER_USER env var or use default
PROJECT="${DOCKER_USER}"

# Load credentials
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

echo -e "${GREEN}🔨 Building and pushing container images${NC}"
echo ""

# Login to Docker Hub
echo -e "${YELLOW}Attempting Docker Hub login...${NC}"
if [ -n "$DOCKER_PASSWORD" ]; then
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin "$REGISTRY" || {
        echo -e "${RED}❌ Docker Hub login failed${NC}"
        echo "Please check your Docker Hub credentials"
        exit 1
    }
    echo -e "${GREEN}✅ Logged in to Docker Hub${NC}"
else
    echo -e "${YELLOW}⚠️  DOCKER_PASSWORD not set. Attempting anonymous push...${NC}"
    echo -e "${YELLOW}Note: You may need to create repositories on Docker Hub first:${NC}"
    echo "  - https://hub.docker.com/repository/create"
    echo "  - Create: haqnow/backend-api, haqnow/worker, haqnow/frontend"
    echo ""
fi

# Build and push backend API image
echo -e "${YELLOW}Building backend API image...${NC}"
cd backend
docker build -f Dockerfile -t "${PROJECT}/backend-api:latest" .
docker tag "${PROJECT}/backend-api:latest" "${REGISTRY}/${PROJECT}/backend-api:latest"
docker push "${REGISTRY}/${PROJECT}/backend-api:latest" || {
    echo -e "${RED}Failed to push backend image. Make sure Docker Hub credentials are set or image is public.${NC}"
    exit 1
}
echo -e "${GREEN}✅ Backend API image pushed${NC}"

# Build and push worker image
echo -e "${YELLOW}Building worker image...${NC}"
docker build -f Dockerfile.worker -t "${PROJECT}/worker:latest" .
docker tag "${PROJECT}/worker:latest" "${REGISTRY}/${PROJECT}/worker:latest"
docker push "${REGISTRY}/${PROJECT}/worker:latest" || {
    echo -e "${RED}Failed to push worker image${NC}"
    exit 1
}
echo -e "${GREEN}✅ Worker image pushed${NC}"
cd ..

# Build and push frontend image
echo -e "${YELLOW}Building frontend image...${NC}"
cd frontend
docker build -f Dockerfile -t "${PROJECT}/frontend:latest" .
docker tag "${PROJECT}/frontend:latest" "${REGISTRY}/${PROJECT}/frontend:latest"
docker push "${REGISTRY}/${PROJECT}/frontend:latest" || {
    echo -e "${RED}Failed to push frontend image${NC}"
    exit 1
}
echo -e "${GREEN}✅ Frontend image pushed${NC}"
cd ..

echo ""
echo -e "${GREEN}✅ All images built and pushed successfully!${NC}"
echo ""
echo "Images pushed to: ${REGISTRY}/${PROJECT}/"
