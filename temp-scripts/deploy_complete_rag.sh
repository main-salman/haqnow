#!/bin/bash

set -e

echo "🚀 STARTING COMPLETE RAG DEPLOYMENT WITH SECRETS FROM .ENV"
echo "================================================================"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

# Export Exoscale credentials for Terraform
export EXOSCALE_API_KEY=$EXOSCALE_API_KEY
export EXOSCALE_SECRET_KEY=$EXOSCALE_SECRET_KEY

echo ""
echo "🏗️  STEP 1: DEPLOYING POSTGRESQL RAG DATABASE WITH TERRAFORM"
echo "============================================================"

cd terraform

# Create terraform.tfvars with secrets from .env
echo "📝 Creating terraform.tfvars with environment secrets..."
cat > terraform.tfvars << EOF
# Exoscale credentials
exoscale_api_key = "$EXOSCALE_API_KEY"
exoscale_secret_key = "$EXOSCALE_SECRET_KEY"

# PostgreSQL RAG database configuration
postgres_plan = "$POSTGRES_RAG_PLAN"
postgres_user = "$POSTGRES_RAG_USER"
postgres_password = "$POSTGRES_RAG_PASSWORD"
postgres_database = "$POSTGRES_RAG_DATABASE"

# Existing instance ID (update if different)
instance_id = "foi-archive-instance"
EOF

echo "✅ terraform.tfvars created with secrets"

# Initialize and plan
echo ""
echo "🔍 Running terraform init and plan..."
terraform init
terraform plan

# Apply changes
echo ""
echo "🚀 Deploying PostgreSQL RAG database..."
terraform apply -auto-approve

# Get the PostgreSQL URI from terraform output
echo ""
echo "📡 Retrieving PostgreSQL connection URI..."
POSTGRES_RAG_URI=$(terraform output -raw postgres_rag_uri 2>/dev/null || echo "")

if [ -n "$POSTGRES_RAG_URI" ]; then
    echo "✅ PostgreSQL RAG URI retrieved: $POSTGRES_RAG_URI"
    
    # Update .env file with actual PostgreSQL URI
    cd ..
    echo ""
    echo "📝 Updating .env with actual PostgreSQL RAG URI..."
    sed -i.bak "s|POSTGRES_RAG_URI=.*|POSTGRES_RAG_URI=$POSTGRES_RAG_URI|" .env
    echo "✅ .env updated with PostgreSQL RAG URI"
else
    echo "⚠️  Could not retrieve PostgreSQL URI from terraform output"
    cd ..
fi

echo ""
echo "🏗️  STEP 2: DEPLOYING APPLICATION WITH RAG SUPPORT"
echo "================================================="

# Deploy application with updated environment
echo "🚀 Running main deployment script..."
chmod +x deploy.sh
./deploy.sh

echo ""
echo "🏗️  STEP 3: SETTING UP RAG DATABASE AND PROCESSING DOCUMENTS"
echo "==========================================================="

# Test the deployment
echo "🧪 Testing RAG system on live server..."
chmod +x test_live_rag.sh
./test_live_rag.sh

echo ""
echo "🎉 COMPLETE RAG DEPLOYMENT FINISHED!"
echo "==================================="
echo ""
echo "📋 DEPLOYMENT SUMMARY:"
echo "   • PostgreSQL RAG Database: ✅ Deployed on Exoscale"
echo "   • Backend Service: ✅ Updated with RAG support"
echo "   • Frontend Interface: ✅ AI Q&A component active"
echo "   • Document Processing: ✅ Automatic RAG integration"
echo "   • Natural Language Search: ✅ Ready for use"
echo ""
echo "🔗 Test your deployment at: https://haqnow.com"
echo "   Try asking questions like: 'Do you have Iranian documents?'"
echo ""
echo "✅ RAG system is now fully operational!"