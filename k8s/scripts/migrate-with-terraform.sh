#!/bin/bash
# Migrate to SKS using Terraform
# This script uses Terraform to create all SKS infrastructure

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../terraform" && pwd)"

echo -e "${GREEN}🚀 Starting SKS Migration with Terraform${NC}"
echo ""

# Check if .env exists
if [ ! -f "$TERRAFORM_DIR/../.env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${RED}Error: terraform.tfvars not found${NC}"
    echo "Please copy terraform.tfvars.example and configure it"
    exit 1
fi

# Check if SKS is already enabled
if grep -q "sks_enabled.*=.*true" terraform.tfvars 2>/dev/null; then
    echo -e "${YELLOW}SKS is already enabled in terraform.tfvars${NC}"
else
    echo -e "${YELLOW}Enabling SKS in terraform.tfvars...${NC}"
    
    # Add SKS configuration if not present
    if ! grep -q "sks_enabled" terraform.tfvars; then
        cat >> terraform.tfvars << 'EOF'

# SKS Configuration
sks_enabled = true
sks_k8s_version = "1.34.2"
sks_service_level = "starter"
sks_cni = "calico"
sks_node_instance_type = "standard.medium"
sks_node_count = 2
sks_anti_affinity = true
sks_auto_upgrade = false
EOF
        echo -e "${GREEN}✅ Added SKS configuration to terraform.tfvars${NC}"
    else
        # Update existing sks_enabled
        sed -i.bak 's/sks_enabled.*=.*false/sks_enabled = true/' terraform.tfvars
        echo -e "${GREEN}✅ Updated sks_enabled to true${NC}"
    fi
fi

# Initialize Terraform
echo -e "${YELLOW}Step 1: Initializing Terraform...${NC}"
terraform init -upgrade

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform initialization failed${NC}"
    exit 1
fi

# Plan the deployment
echo ""
echo -e "${YELLOW}Step 2: Planning Terraform deployment...${NC}"
terraform plan -out=sks-migration.tfplan

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform plan failed${NC}"
    exit 1
fi

# Ask for confirmation
echo ""
echo -e "${YELLOW}Review the plan above. This will create:${NC}"
echo "  • SKS cluster (Starter tier)"
echo "  • Security group for nodes"
echo "  • Node pool with 2 nodes (standard.medium)"
echo "  • Network Load Balancer"
echo ""
read -p "Continue with apply? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Migration cancelled"
    exit 0
fi

# Apply the plan
echo ""
echo -e "${YELLOW}Step 3: Applying Terraform configuration...${NC}"
echo -e "${YELLOW}This will take 10-15 minutes...${NC}"
terraform apply sks-migration.tfplan

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform apply failed${NC}"
    exit 1
fi

# Get outputs
echo ""
echo -e "${GREEN}✅ SKS Infrastructure Created!${NC}"
echo ""
echo "Getting cluster information..."

CLUSTER_ID=$(terraform output -raw sks_cluster_id 2>/dev/null || echo "")
NODEPOOL_ID=$(terraform output -raw sks_nodepool_id 2>/dev/null || echo "")
NLB_IP=$(terraform output -raw sks_nlb_ip 2>/dev/null || echo "")
KUBECONFIG_PATH=$(terraform output -raw sks_kubeconfig_path 2>/dev/null || echo "")
NODE_IPS=$(terraform output -json sks_node_ips 2>/dev/null || echo "[]")

echo ""
echo "Cluster ID: $CLUSTER_ID"
echo "Node Pool ID: $NODEPOOL_ID"
echo "NLB IP: $NLB_IP"
echo "Kubeconfig: $KUBECONFIG_PATH"
echo "Node IPs: $NODE_IPS"

# Save node IPs for database update script
if [ -n "$NODE_IPS" ] && [ "$NODE_IPS" != "[]" ]; then
    echo "$NODE_IPS" | python3 -c "import sys, json; ips = json.load(sys.stdin); print(' '.join(ips))" > /tmp/sks-node-ips.txt 2>/dev/null || true
fi

# Set up kubectl
if [ -n "$KUBECONFIG_PATH" ] && [ -f "$KUBECONFIG_PATH" ]; then
    export KUBECONFIG="$KUBECONFIG_PATH"
    echo ""
    echo -e "${YELLOW}Verifying cluster access...${NC}"
    if kubectl cluster-info &>/dev/null; then
        echo -e "${GREEN}✅ Cluster access verified${NC}"
        kubectl get nodes
    else
        echo -e "${YELLOW}⚠️  Cluster may still be provisioning. Wait a few minutes and try:${NC}"
        echo "  export KUBECONFIG=$KUBECONFIG_PATH"
        echo "  kubectl get nodes"
    fi
fi

echo ""
echo -e "${GREEN}✅ Migration Step 1 Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update database IP filters: ./k8s/scripts/update-database-ips.sh"
echo "  2. Build and push images: ./k8s/scripts/build-and-push-images.sh"
echo "  3. Deploy application: ./k8s/scripts/deploy.sh"
echo "  4. Test deployment: ./k8s/scripts/test-deployment.sh"

