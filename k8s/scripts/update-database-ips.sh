#!/bin/bash
# Update database IP filters to allow SKS nodes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ZONE="ch-dk-2"
MYSQL_DB="foi-archive-mysql-production"
POSTGRES_DB="foi-archive-postgres-rag-production"

# Load credentials
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

export EXOSCALE_API_KEY=$(grep "^EXOSCALE_API_KEY=" .env | cut -d'=' -f2)
export EXOSCALE_SECRET_KEY=$(grep "^EXOSCALE_SECRET_KEY=" .env | cut -d'=' -f2)

if [ -z "$EXOSCALE_API_KEY" ] || [ -z "$EXOSCALE_SECRET_KEY" ]; then
    echo -e "${RED}Error: Exoscale credentials not found${NC}"
    exit 1
fi

# Get node IPs from kubeconfig or file
if [ -f /tmp/sks-node-ips.txt ]; then
    NODE_IPS=$(cat /tmp/sks-node-ips.txt)
elif [ -f ~/.kube/haqnow-kubeconfig.yaml ]; then
    export KUBECONFIG=~/.kube/haqnow-kubeconfig.yaml
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
else
    echo -e "${RED}Error: Cannot find node IPs. Please provide them manually.${NC}"
    exit 1
fi

if [ -z "$NODE_IPS" ]; then
    echo -e "${RED}Error: No node IPs found${NC}"
    exit 1
fi

echo -e "${GREEN}Updating database IP filters with: $NODE_IPS${NC}"
echo ""

# Convert space-separated to JSON array
IP_ARRAY=$(echo "$NODE_IPS" | python3 -c "
import sys, json
ips = sys.stdin.read().strip().split()
print(json.dumps(ips))
")

# Update MySQL database
echo -e "${YELLOW}Updating MySQL database IP filter...${NC}"
exo x update-dbaas-service-mysql \
    --dbaas-service-name "$MYSQL_DB" \
    --zone "$ZONE" \
    --ip-filter "$IP_ARRAY" \
    -o json > /dev/null 2>&1 && echo -e "${GREEN}✅ MySQL IP filter updated${NC}" || {
    echo -e "${RED}Failed to update MySQL IP filter${NC}"
    exit 1
}

# Update PostgreSQL database
echo -e "${YELLOW}Updating PostgreSQL database IP filter...${NC}"
exo x update-dbaas-service-pg \
    --dbaas-service-name "$POSTGRES_DB" \
    --zone "$ZONE" \
    --ip-filter "$IP_ARRAY" \
    -o json > /dev/null 2>&1 && echo -e "${GREEN}✅ PostgreSQL IP filter updated${NC}" || {
    echo -e "${RED}Failed to update PostgreSQL IP filter${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}✅ Database IP filters updated successfully!${NC}"

