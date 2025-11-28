#!/bin/bash
# Test deployment after migration

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}Error: kubectl not configured${NC}"
    exit 1
fi

echo -e "${GREEN}🧪 Testing SKS Deployment${NC}"
echo ""

# Check pods
echo -e "${YELLOW}Checking pod status...${NC}"
kubectl get pods -n haqnow

# Check services
echo ""
echo -e "${YELLOW}Checking services...${NC}"
kubectl get services -n haqnow

# Get service endpoints
echo ""
echo -e "${YELLOW}Getting service endpoints...${NC}"
BACKEND_IP=$(kubectl get service backend-service -n haqnow -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
FRONTEND_IP=$(kubectl get service frontend-service -n haqnow -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")

if [ -n "$BACKEND_IP" ]; then
    echo "Backend Service IP: $BACKEND_IP"
fi
if [ -n "$FRONTEND_IP" ]; then
    echo "Frontend Service IP: $FRONTEND_IP"
fi

# Port forward and test
echo ""
echo -e "${YELLOW}Testing backend health endpoint...${NC}"
kubectl port-forward -n haqnow service/backend-service 8000:8000 &
PF_PID=$!
sleep 5

if curl -s http://localhost:8000/health | python3 -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

kill $PF_PID 2>/dev/null || true

# Check logs
echo ""
echo -e "${YELLOW}Checking recent logs...${NC}"
echo "Backend logs (last 10 lines):"
kubectl logs -n haqnow -l app=backend-api --tail=10 || echo "No backend logs"
echo ""
echo "Worker logs (last 10 lines):"
kubectl logs -n haqnow -l app=worker --tail=10 || echo "No worker logs"

echo ""
echo -e "${GREEN}✅ Basic tests complete${NC}"
echo ""
echo "To run Playwright e2e tests:"
echo "  cd frontend && npm run test:e2e"

