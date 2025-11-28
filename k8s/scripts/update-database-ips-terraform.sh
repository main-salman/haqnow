#!/bin/bash
# Update database IP filters using Terraform outputs

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../terraform" && pwd)"

cd "$TERRAFORM_DIR"

# Check if Terraform has been applied
if ! terraform output sks_node_ips &>/dev/null; then
    echo -e "${RED}Error: SKS infrastructure not found. Run terraform apply first.${NC}"
    exit 1
fi

# Get kubeconfig path
KUBECONFIG_PATH=$(terraform output -raw sks_kubeconfig_path 2>/dev/null || echo "")

if [ -z "$KUBECONFIG_PATH" ] || [ ! -f "$KUBECONFIG_PATH" ]; then
    echo -e "${RED}Error: Kubeconfig not found. Run terraform apply first.${NC}"
    exit 1
fi

export KUBECONFIG="$KUBECONFIG_PATH"

# Get node IPs using kubectl
echo -e "${YELLOW}Getting node IPs from Kubernetes cluster...${NC}"
NODE_IPS=$(kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null)

if [ -z "$NODE_IPS" ]; then
    # Fallback to InternalIP if ExternalIP not available
    NODE_IPS=$(kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
fi

if [ -z "$NODE_IPS" ]; then
    echo -e "${RED}Error: Could not retrieve node IPs from cluster${NC}"
    exit 1
fi

if [ -z "$NODE_IPS" ]; then
    echo -e "${RED}Error: Could not parse node IPs${NC}"
    exit 1
fi

echo -e "${GREEN}Updating database IP filters with SKS node IPs: $NODE_IPS${NC}"
echo ""

# Load credentials
if [ ! -f ../.env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

export EXOSCALE_API_KEY=$(grep "^EXOSCALE_API_KEY=" ../.env | cut -d'=' -f2)
export EXOSCALE_SECRET_KEY=$(grep "^EXOSCALE_SECRET_KEY=" ../.env | cut -d'=' -f2)

if [ -z "$EXOSCALE_API_KEY" ] || [ -z "$EXOSCALE_SECRET_KEY" ]; then
    echo -e "${RED}Error: Exoscale credentials not found${NC}"
    exit 1
fi

ZONE="ch-dk-2"
MYSQL_DB="foi-archive-mysql-production"
POSTGRES_DB="foi-archive-postgres-rag-production"

# Convert space-separated IPs to array and add /32 CIDR
IP_ARRAY=$(echo "$NODE_IPS" | python3 -c "
import sys, json
ips = [ip.strip() + '/32' for ip in sys.stdin.read().strip().split() if ip.strip()]
print(json.dumps(ips))
")

# Also include the existing VM IP for now (during migration)
VM_IP="194.182.164.77/32"
ALL_IPS=$(echo "$IP_ARRAY" | python3 -c "
import sys, json
node_ips = json.load(sys.stdin)
vm_ip = '$VM_IP'
all_ips = list(set(node_ips + [vm_ip]))  # Remove duplicates
print(json.dumps(all_ips))
")

# Create JSON payload for MySQL update
MYSQL_PAYLOAD=$(python3 -c "
import json
ips = json.loads('$ALL_IPS')
payload = {'ip-filter': ips}
print(json.dumps(payload))
")

# Create JSON payload for PostgreSQL update
POSTGRES_PAYLOAD=$(python3 -c "
import json
ips = json.loads('$ALL_IPS')
payload = {'ip-filter': ips}
print(json.dumps(payload))
")

# Update MySQL database
echo -e "${YELLOW}Updating MySQL database IP filter...${NC}"
echo "$MYSQL_PAYLOAD" | exo x update-dbaas-service-mysql "$MYSQL_DB" --zone "$ZONE" 2>&1 | grep -q "error" && {
    echo -e "${RED}Failed to update MySQL IP filter${NC}"
    echo "$MYSQL_PAYLOAD" | exo x update-dbaas-service-mysql "$MYSQL_DB" --zone "$ZONE" 2>&1
    exit 1
} || echo -e "${GREEN}✅ MySQL IP filter updated${NC}"

# Update PostgreSQL database
echo -e "${YELLOW}Updating PostgreSQL database IP filter...${NC}"
echo "$POSTGRES_PAYLOAD" | exo x update-dbaas-service-pg "$POSTGRES_DB" --zone "$ZONE" 2>&1 | grep -q "error" && {
    echo -e "${RED}Failed to update PostgreSQL IP filter${NC}"
    echo "$POSTGRES_PAYLOAD" | exo x update-dbaas-service-pg "$POSTGRES_DB" --zone "$ZONE" 2>&1
    exit 1
} || echo -e "${GREEN}✅ PostgreSQL IP filter updated${NC}"

echo ""
echo -e "${GREEN}✅ Database IP filters updated successfully!${NC}"

