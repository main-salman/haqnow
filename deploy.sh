#!/bin/bash

# FOI Archive - Deployment Script
# This script deploys the application to Exoscale using Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 FOI Archive Deployment to Exoscale${NC}"

# Check if terraform directory exists
if [ ! -d "terraform" ]; then
    echo -e "${RED}❌ Error: terraform directory not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo -e "${RED}❌ Error: terraform/terraform.tfvars not found!${NC}"
    echo "Please create terraform.tfvars from terraform.tfvars.example"
    echo "and fill in your Exoscale credentials."
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Error: Terraform is not installed!${NC}"
    echo "Please install Terraform: https://www.terraform.io/downloads.html"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Options:${NC}"
echo "1. Deploy infrastructure only"
echo "2. Deploy infrastructure and application"
echo "3. Update application code only (infrastructure must exist)"
echo "4. Destroy infrastructure"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo -e "${BLUE}🏗️ Deploying infrastructure only...${NC}"
        deploy_infrastructure_only=true
        ;;
    2)
        echo -e "${BLUE}🏗️ Deploying infrastructure and application...${NC}"
        deploy_full=true
        ;;
    3)
        echo -e "${BLUE}📦 Updating application code only...${NC}"
        update_app_only=true
        ;;
    4)
        echo -e "${RED}💥 Destroying infrastructure...${NC}"
        read -p "Are you sure you want to destroy all infrastructure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            destroy_infrastructure=true
        else
            echo "Deployment cancelled."
            exit 0
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid option${NC}"
        exit 1
        ;;
esac

cd terraform

if [ "$destroy_infrastructure" = true ]; then
    echo -e "${RED}💥 Destroying infrastructure...${NC}"
    terraform destroy -auto-approve
    echo -e "${GREEN}✅ Infrastructure destroyed${NC}"
    exit 0
fi

if [ "$deploy_infrastructure_only" = true ] || [ "$deploy_full" = true ]; then
    echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
    terraform init

    echo -e "${YELLOW}📋 Planning infrastructure changes...${NC}"
    terraform plan

    read -p "Do you want to apply these changes? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi

    echo -e "${BLUE}🏗️ Applying infrastructure changes...${NC}"
    terraform apply -auto-approve

    # Get outputs
    INSTANCE_IP=$(terraform output -raw instance_ip)
    MYSQL_HOST=$(terraform output -raw mysql_host)
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
    echo -e "${YELLOW}📊 Deployment Info:${NC}"
    echo "  Instance IP: $INSTANCE_IP"
    echo "  MySQL Host: $MYSQL_HOST"
fi

# If updating app only, get the instance IP
if [ "$update_app_only" = true ]; then
    INSTANCE_IP=$(terraform output -raw instance_ip 2>/dev/null)
    if [ -z "$INSTANCE_IP" ]; then
        echo -e "${RED}❌ Error: Could not get instance IP. Infrastructure may not exist.${NC}"
        echo "Please deploy infrastructure first using option 1 or 2."
        exit 1
    fi
    echo -e "${YELLOW}📦 Updating application on: $INSTANCE_IP${NC}"
fi

# Deploy or update application code
if [ "$deploy_full" = true ] || [ "$update_app_only" = true ]; then
    echo -e "${YELLOW}📦 Deploying application code...${NC}"
    
    # Wait for instance to be ready
    echo "Waiting for instance to be ready..."
    sleep 30
    
    # Check SSH connectivity
    echo "Testing SSH connectivity..."
    ssh_attempts=0
    max_attempts=10
    
    while [ $ssh_attempts -lt $max_attempts ]; do
        if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@$INSTANCE_IP "echo 'SSH connection successful'" 2>/dev/null; then
            break
        fi
        echo "SSH attempt $((ssh_attempts + 1))/$max_attempts failed, retrying..."
        sleep 30
        ssh_attempts=$((ssh_attempts + 1))
    done
    
    if [ $ssh_attempts -eq $max_attempts ]; then
        echo -e "${RED}❌ Error: Could not establish SSH connection after $max_attempts attempts${NC}"
        echo "Please check:"
        echo "1. Instance is running"
        echo "2. Security groups allow SSH (port 22)"
        echo "3. SSH key is correct"
        exit 1
    fi
    
    echo -e "${GREEN}✅ SSH connection established${NC}"
    
    # Create deployment package
    echo "Creating deployment package..."
    cd ..
    
    # Create temporary directory for deployment
    DEPLOY_DIR="/tmp/foi-deploy-$(date +%s)"
    mkdir -p $DEPLOY_DIR
    
    # Copy application files
    cp -r backend $DEPLOY_DIR/
    cp -r frontend $DEPLOY_DIR/
    cp .env $DEPLOY_DIR/
    
    # Create deployment archive
    cd $DEPLOY_DIR
    tar -czf foi-app.tar.gz backend frontend .env
    
    # Upload to server
    echo "Uploading application code..."
    scp -o StrictHostKeyChecking=no foi-app.tar.gz root@$INSTANCE_IP:/tmp/
    
    # Deploy on server
    echo "Deploying on server..."
    ssh -o StrictHostKeyChecking=no root@$INSTANCE_IP << 'EOF'
        set -e
        
        echo "Extracting application code..."
        cd /opt/foi-archive
        sudo tar -xzf /tmp/foi-app.tar.gz
        sudo chown -R foi:foi /opt/foi-archive
        
        echo "Updating environment file..."
        sudo cp .env /opt/foi-archive/.env
        sudo chown foi:foi /opt/foi-archive/.env
        sudo chmod 600 /opt/foi-archive/.env
        
        echo "Restarting application..."
        sudo systemctl stop foi-archive || true
        sudo systemctl start foi-archive
        
        echo "Checking application status..."
        sleep 10
        if sudo systemctl is-active --quiet foi-archive; then
            echo "✅ Application is running"
        else
            echo "❌ Application failed to start"
            sudo systemctl status foi-archive
            exit 1
        fi
        
        # Cleanup
        rm -f /tmp/foi-app.tar.gz
EOF
    
    # Cleanup local files
    rm -rf $DEPLOY_DIR
    
    echo -e "${GREEN}✅ Application deployed successfully!${NC}"
fi

cd ..

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${YELLOW}📱 Access your application:${NC}"
echo "  Frontend: http://$INSTANCE_IP"
echo "  Backend API: http://$INSTANCE_IP/api"
echo "  Health Check: http://$INSTANCE_IP/health"
echo ""
echo -e "${YELLOW}🔧 SSH Access:${NC}"
echo "  ssh root@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}📊 Monitoring:${NC}"
echo "  Application logs: sudo journalctl -u foi-archive -f"
echo "  Docker logs: sudo docker-compose -f /opt/foi-archive/docker-compose.yml logs -f"
echo ""

if [ "$deploy_full" = true ]; then
    echo -e "${BLUE}🔐 Next Steps:${NC}"
    echo "1. Configure your domain name to point to: $INSTANCE_IP"
    echo "2. Set up SSL certificate: sudo certbot --nginx -d your-domain.com"
    echo "3. Update .env file with production credentials if needed"
    echo "4. Test the application thoroughly"
fi 