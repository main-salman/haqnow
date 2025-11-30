#!/bin/bash
# Check if Docker Hub repositories exist

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOCKER_USER="${DOCKER_USER:-haqnow}"
REPOS=("backend-api" "worker" "frontend")

echo -e "${YELLOW}Checking Docker Hub repositories for ${DOCKER_USER}...${NC}"
echo ""

ALL_EXIST=true
for repo in "${REPOS[@]}"; do
    FULL_REPO="${DOCKER_USER}/${repo}"
    if docker manifest inspect "${FULL_REPO}:latest" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${FULL_REPO} exists${NC}"
    else
        echo -e "${RED}❌ ${FULL_REPO} does not exist${NC}"
        ALL_EXIST=false
    fi
done

echo ""
if [ "$ALL_EXIST" = true ]; then
    echo -e "${GREEN}✅ All repositories exist! Ready to deploy.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some repositories are missing.${NC}"
    echo ""
    echo "Create them at: https://hub.docker.com/repository/create"
    echo ""
    echo "Required repositories:"
    for repo in "${REPOS[@]}"; do
        echo "  - ${DOCKER_USER}/${repo}"
    done
    echo ""
    echo "Or use GitHub Container Registry instead:"
    echo "  export REGISTRY=ghcr.io"
    echo "  export DOCKER_USER=main-salman"
    exit 1
fi


