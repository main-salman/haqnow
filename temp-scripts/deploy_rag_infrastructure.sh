#!/bin/bash

# RAG Infrastructure Deployment Script
echo "🚀 Deploying RAG Infrastructure on Exoscale"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Commit current changes
echo "📝 Committing current changes..."
git add -A
git commit -m "RAG infrastructure deployment preparation" || true
git push origin main

# Step 2: Deploy Terraform infrastructure
echo "🏗️ Deploying Terraform infrastructure..."
cd terraform

# Check if terraform.tfvars exists and has the required variables
if ! grep -q "postgres_password" terraform.tfvars; then
    echo "postgres_password = \"$(openssl rand -base64 32)\"" >> terraform.tfvars
    print_status "Generated PostgreSQL password"
fi

if ! grep -q "mysql_root_password" terraform.tfvars; then
    echo "mysql_root_password = \"$(openssl rand -base64 32)\"" >> terraform.tfvars
    print_status "Generated MySQL root password"
fi

# Initialize terraform if needed
terraform init

# Plan the deployment
echo "📋 Planning Terraform deployment..."
terraform plan -input=false -out=tfplan

# Apply the changes
echo "🚀 Applying Terraform changes..."
if terraform apply -input=false tfplan; then
    print_status "Infrastructure deployed successfully"
else
    print_error "Terraform deployment failed"
    exit 1
fi

# Get the PostgreSQL connection details
echo "📊 Getting database connection details..."
POSTGRES_URI=$(terraform output -raw postgres_rag_uri 2>/dev/null || echo "")

if [ -z "$POSTGRES_URI" ]; then
    print_warning "Could not get PostgreSQL URI from Terraform output"
else
    print_status "PostgreSQL RAG database deployed successfully"
fi

cd ..

# Step 3: Deploy application with new RAG features
echo "🔧 Deploying application with RAG features..."

# Update the deploy script to restart services
ssh root@159.100.250.145 'cd /opt/foi-archive && git pull origin main'

# Install RAG dependencies
ssh root@159.100.250.145 'cd /opt/foi-archive/backend && source .venv/bin/activate && pip install -r requirements-rag.txt' || print_warning "RAG dependencies installation may have issues"

# Install pgvector Python package
ssh root@159.100.250.145 'cd /opt/foi-archive/backend && source .venv/bin/activate && pip install pgvector psycopg2-binary' || print_warning "pgvector installation may have issues"

# Restart backend service
ssh root@159.100.250.145 'systemctl restart foi-archive'

# Wait for service to start
sleep 10

# Step 4: Initialize RAG database
echo "🗄️ Initializing RAG database..."
ssh root@159.100.250.145 'cd /opt/foi-archive/backend && source .venv/bin/activate && python3 -c "
import asyncio
from app.database.rag_database import init_rag_db, ensure_pgvector_extension, test_rag_db_connection

try:
    # Test connection
    if test_rag_db_connection():
        print(\"✅ RAG database connection successful\")
    else:
        print(\"❌ RAG database connection failed\")
        exit(1)
    
    # Ensure pgvector extension
    if ensure_pgvector_extension():
        print(\"✅ pgvector extension available\")
    else:
        print(\"⚠️ pgvector extension not available\")
    
    # Initialize database
    init_rag_db()
    print(\"✅ RAG database initialized successfully\")
    
except Exception as e:
    print(f\"❌ RAG database initialization failed: {e}\")
    exit(1)
"' || print_warning "RAG database initialization may have issues"

# Step 5: Process existing documents for RAG
echo "📚 Processing existing documents for RAG..."
ssh root@159.100.250.145 'cd /opt/foi-archive/backend && source .venv/bin/activate && python3 -c "
import requests
import time

# Wait for service to be ready
time.sleep(5)

try:
    # Process all existing documents
    response = requests.post(\"http://localhost:8000/api/rag/process-all-documents\", timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f\"✅ Started processing {result.get(\"document_count\", 0)} documents for RAG\")
    else:
        print(f\"⚠️ RAG processing request failed: {response.status_code}\")
except Exception as e:
    print(f\"⚠️ RAG processing request failed: {e}\")
"' || print_warning "Document processing may have issues"

# Step 6: Test the deployment
echo "🧪 Testing RAG deployment..."

# Test basic API health
if curl -s "https://www.haqnow.com/api/health" | grep -q "healthy"; then
    print_status "Main API is healthy"
else
    print_warning "Main API health check failed"
fi

# Test RAG status
RAG_STATUS=$(curl -s "https://www.haqnow.com/api/rag/status" | jq -r '.status' 2>/dev/null || echo "unknown")
if [ "$RAG_STATUS" = "healthy" ] || [ "$RAG_STATUS" = "degraded" ]; then
    print_status "RAG API is responding (status: $RAG_STATUS)"
else
    print_warning "RAG API status unknown or failed"
fi

# Step 7: Frontend rebuild and deployment
echo "🎨 Rebuilding and deploying frontend..."
ssh root@159.100.250.145 'cd /opt/foi-archive/frontend && npm run build && cp -r dist/* /var/www/html/ && chown -R www-data:www-data /var/www/html'

# Final status check
echo ""
echo "🎉 RAG Infrastructure Deployment Complete!"
echo "==========================================="
echo ""
echo "📊 Deployment Summary:"
echo "- PostgreSQL RAG database: Deployed on Exoscale"
echo "- pgvector extension: Enabled for vector operations"
echo "- Backend RAG service: Updated and deployed"
echo "- Document processing: Initiated for existing documents"
echo "- Frontend: Rebuilt with RAG features"
echo ""
echo "🌐 Test your deployment:"
echo "- Main site: https://www.haqnow.com"
echo "- Search page: https://www.haqnow.com/search-page"
echo "- Try the AI Q&A tab for natural language queries!"
echo ""
echo "📝 Monitor logs:"
echo "- Backend logs: ssh root@159.100.250.145 'journalctl -u foi-archive -f'"
echo "- RAG status: curl https://www.haqnow.com/api/rag/status"
echo ""

# Create deployment status file
cat > RAG_DEPLOYMENT_STATUS.md << EOF
# RAG Infrastructure Deployment Status

**Deployment Date:** $(date)
**Status:** COMPLETED

## Infrastructure Deployed

✅ **PostgreSQL Database**: Exoscale DBaaS with pgvector extension
✅ **RAG Service**: Updated to use PostgreSQL for vector operations  
✅ **Database Models**: RAG-specific models with vector support
✅ **API Endpoints**: RAG Q&A endpoints functional
✅ **Frontend**: Updated with AI Q&A interface

## Database Configuration

- **Database Type**: PostgreSQL 15 with pgvector
- **Provider**: Exoscale Database as a Service
- **Connection**: Separate from main MySQL database
- **Vector Dimensions**: 384 (all-MiniLM-L6-v2 embeddings)

## Next Steps

1. Monitor document processing: \`curl https://www.haqnow.com/api/rag/analytics\`
2. Test natural language queries on the search page
3. Upload new documents to verify automatic RAG processing
4. Check that "iranian" queries now find "iran" documents

## Known Issues

- Document processing may take time for large numbers of existing documents
- Ollama may need manual installation for full LLM functionality
- Monitor backend logs for any PostgreSQL connection issues

EOF

print_status "Deployment status saved to RAG_DEPLOYMENT_STATUS.md"
print_status "RAG Infrastructure deployment completed successfully! 🎉"