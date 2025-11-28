#!/bin/bash
# SKS Migration Script for HaqNow
# This script migrates the application from VM to Exoscale SKS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ZONE="ch-dk-2"
CLUSTER_NAME="haqnow-production"
NODEPOOL_NAME="haqnow-nodes"
SECURITY_GROUP_NAME="sks-production-nodes"
K8S_VERSION="1.34.2"
INSTANCE_TYPE="standard.medium"
NODE_COUNT=2

# Load credentials from .env
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

export EXOSCALE_API_KEY=$(grep "^EXOSCALE_API_KEY=" .env | cut -d'=' -f2)
export EXOSCALE_SECRET_KEY=$(grep "^EXOSCALE_SECRET_KEY=" .env | cut -d'=' -f2)

if [ -z "$EXOSCALE_API_KEY" ] || [ -z "$EXOSCALE_SECRET_KEY" ]; then
    echo -e "${RED}Error: Exoscale credentials not found in .env${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Starting SKS Migration${NC}"
echo ""

# Step 1: Create Security Group for SKS nodes
echo -e "${YELLOW}Step 1: Creating security group for SKS nodes...${NC}"

# Check if security group already exists
EXISTING_SG=$(exo x list-security-groups -z "$ZONE" -o json 2>&1 | \
    python3 -c "import sys, json; sgs = json.load(sys.stdin).get('security-groups', []); [print(sg['id']) for sg in sgs if sg.get('name') == '$SECURITY_GROUP_NAME']" 2>/dev/null || echo "")

if [ -n "$EXISTING_SG" ]; then
    SECURITY_GROUP_ID="$EXISTING_SG"
    echo -e "${YELLOW}Security group already exists: $SECURITY_GROUP_ID${NC}"
else
    # Create security group using JSON input
    SG_RESPONSE=$(echo "{\"name\":\"$SECURITY_GROUP_NAME\",\"description\":\"Security group for SKS production nodes\"}" | \
        exo x create-security-group -z "$ZONE" -o json 2>&1)
    
    # Wait a moment for creation to complete, then get the ID
    sleep 2
    SECURITY_GROUP_ID=$(exo x list-security-groups -z "$ZONE" -o json 2>&1 | \
        python3 -c "import sys, json; sgs = json.load(sys.stdin).get('security-groups', []); [print(sg['id']) for sg in sgs if sg.get('name') == '$SECURITY_GROUP_NAME']" 2>/dev/null || echo "")
    
    if [ -z "$SECURITY_GROUP_ID" ]; then
        echo -e "${RED}Failed to create security group. Response: $SG_RESPONSE${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Security group created: $SECURITY_GROUP_ID${NC}"
fi

# Step 2: Create SKS Cluster
echo -e "${YELLOW}Step 2: Creating SKS cluster...${NC}"

# Check if cluster already exists
EXISTING_CLUSTER=$(exo x list-sks-clusters -z "$ZONE" -o json 2>&1 | \
    python3 -c "import sys, json; clusters = json.load(sys.stdin).get('sks-clusters', []); [print(c['id']) for c in clusters if c.get('name') == '$CLUSTER_NAME']" 2>/dev/null || echo "")

if [ -n "$EXISTING_CLUSTER" ]; then
    CLUSTER_ID="$EXISTING_CLUSTER"
    echo -e "${YELLOW}Cluster already exists: $CLUSTER_ID${NC}"
else
    # Create SKS cluster using JSON input
    CLUSTER_JSON=$(python3 -c "
import json
print(json.dumps({
    'name': '$CLUSTER_NAME',
    'description': 'HaqNow production cluster',
    'version': '$K8S_VERSION',
    'level': 'starter',
    'cni': 'calico',
    'addons': ['exoscale-cloud-controller', 'exoscale-container-storage-interface', 'metrics-server']
}))
")
    
    CLUSTER_ID=$(echo "$CLUSTER_JSON" | \
        exo x create-sks-cluster -z "$ZONE" -o json 2>&1 | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")
    
    if [ -z "$CLUSTER_ID" ]; then
        echo -e "${RED}Failed to create SKS cluster${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ SKS cluster created: $CLUSTER_ID${NC}"
echo -e "${YELLOW}Waiting for cluster to be ready (this may take 5-10 minutes)...${NC}"

# Wait for cluster to be ready
for i in {1..60}; do
    STATUS=$(exo x get-sks-cluster --id "$CLUSTER_ID" -z "$ZONE" -o json 2>&1 | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('state', 'unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✅ Cluster is ready!${NC}"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo -e "${RED}Cluster creation timeout${NC}"
        exit 1
    fi
    
    echo -n "."
    sleep 10
done
echo ""

# Step 3: Create Node Pool
echo -e "${YELLOW}Step 3: Creating node pool with $NODE_COUNT nodes...${NC}"

# Check if node pool already exists
EXISTING_NODEPOOL=$(exo x get-sks-cluster --id "$CLUSTER_ID" -z "$ZONE" -o json 2>&1 | \
    python3 -c "import sys, json; cluster = json.load(sys.stdin); nodepools = cluster.get('nodepools', []); [print(np['id']) for np in nodepools if np.get('name') == '$NODEPOOL_NAME']" 2>/dev/null || echo "")

if [ -n "$EXISTING_NODEPOOL" ]; then
    NODEPOOL_ID="$EXISTING_NODEPOOL"
    echo -e "${YELLOW}Node pool already exists: $NODEPOOL_ID${NC}"
else
    # Create node pool using JSON input
    NODEPOOL_JSON=$(python3 -c "
import json
print(json.dumps({
    'name': '$NODEPOOL_NAME',
    'description': 'Production node pool for HaqNow',
    'instance-type': '$INSTANCE_TYPE',
    'size': $NODE_COUNT,
    'security-groups': ['$SECURITY_GROUP_ID']
}))
")
    
    NODEPOOL_ID=$(echo "$NODEPOOL_JSON" | \
        exo x create-sks-nodepool --sks-cluster-id "$CLUSTER_ID" -z "$ZONE" -o json 2>&1 | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")
    
    if [ -z "$NODEPOOL_ID" ]; then
        echo -e "${RED}Failed to create node pool${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Node pool created: $NODEPOOL_ID${NC}"
echo -e "${YELLOW}Waiting for nodes to be ready (this may take 5-10 minutes)...${NC}"

# Wait for nodes to be ready
for i in {1..60}; do
    NODES_READY=$(exo x get-sks-nodepool --sks-cluster-id "$CLUSTER_ID" --id "$NODEPOOL_ID" -z "$ZONE" -o json 2>&1 | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('instances', []))" 2>/dev/null | grep -c "running" || echo "0")
    
    if [ "$NODES_READY" -ge "$NODE_COUNT" ]; then
        echo -e "${GREEN}✅ All nodes are ready!${NC}"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo -e "${YELLOW}Warning: Nodes may still be provisioning${NC}"
    fi
    
    echo -n "."
    sleep 10
done
echo ""

# Step 4: Get kubeconfig
echo -e "${YELLOW}Step 4: Generating kubeconfig...${NC}"
mkdir -p ~/.kube
exo x generate-sks-cluster-kubeconfig \
    --sks-cluster-id "$CLUSTER_ID" \
    --zone "$ZONE" \
    --user kubernetes-admin \
    --group system:masters \
    > ~/.kube/haqnow-kubeconfig.yaml 2>&1

export KUBECONFIG=~/.kube/haqnow-kubeconfig.yaml

# Verify cluster access
if kubectl cluster-info &>/dev/null; then
    echo -e "${GREEN}✅ Kubeconfig generated and cluster access verified${NC}"
else
    echo -e "${RED}Failed to access cluster${NC}"
    exit 1
fi

# Step 5: Get node IPs for database whitelist
echo -e "${YELLOW}Step 5: Getting node IPs for database whitelist...${NC}"
NODE_IPS=$(kubectl get nodes -o json | python3 -c "
import sys, json
nodes = json.load(sys.stdin)['items']
ips = []
for node in nodes:
    for addr in node['status']['addresses']:
        if addr['type'] == 'ExternalIP':
            ips.append(addr['address'] + '/32')
print(' '.join(ips))
" 2>/dev/null || echo "")

if [ -z "$NODE_IPS" ]; then
    echo -e "${YELLOW}Warning: Could not get node IPs automatically${NC}"
    echo "Please get node IPs manually and update database IP filters"
else
    echo -e "${GREEN}✅ Node IPs: $NODE_IPS${NC}"
    echo "$NODE_IPS" > /tmp/sks-node-ips.txt
fi

echo ""
echo -e "${GREEN}✅ SKS Infrastructure Created Successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Update database IP filters with node IPs"
echo "2. Build and push container images"
echo "3. Deploy Kubernetes manifests"
echo "4. Test the deployment"
echo ""
echo "Cluster ID: $CLUSTER_ID"
echo "Node Pool ID: $NODEPOOL_ID"
echo "Security Group ID: $SECURITY_GROUP_ID"
echo "Node IPs saved to: /tmp/sks-node-ips.txt"

