#!/bin/bash
# Create Kubernetes secrets from .env file

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

echo -e "${YELLOW}Creating Kubernetes secrets from .env file...${NC}"

# Create namespace if it doesn't exist
kubectl create namespace haqnow --dry-run=client -o yaml | kubectl apply -f -

# Read .env and create secret
kubectl create secret generic haqnow-secrets \
    --from-env-file=.env \
    --namespace=haqnow \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ Secrets created successfully!${NC}"

