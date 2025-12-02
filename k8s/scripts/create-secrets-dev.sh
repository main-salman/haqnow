#!/bin/bash
# Create Kubernetes secrets for DEV environment from .env file

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "Error: kubectl not configured. Please run migrate-to-sks.sh first"
    exit 1
fi

echo -e "${YELLOW}Creating Kubernetes secrets for DEV environment from .env file...${NC}"

# Create namespace if it doesn't exist
kubectl create namespace haqnow-dev --dry-run=client -o yaml | kubectl apply -f -

# Read .env and create secret in haqnow-dev namespace
kubectl create secret generic haqnow-secrets \
    --from-env-file=.env \
    --namespace=haqnow-dev \
    --dry-run=client -o yaml | kubectl apply -f -

# Create GHCR secret for pulling images (same credentials as prod)
GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' .env 2>/dev/null | cut -d'=' -f2- | sed 's/#.*$//' | tr -d ' ')
DOCKER_USER="main-salman"

if [ -n "$GITHUB_TOKEN" ]; then
    kubectl create secret docker-registry ghcr-secret \
        --docker-server=ghcr.io \
        --docker-username="$DOCKER_USER" \
        --docker-password="$GITHUB_TOKEN" \
        --namespace=haqnow-dev \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ GHCR pull secret created for dev namespace${NC}"
fi

echo -e "${GREEN}✅ Dev secrets created successfully!${NC}"

