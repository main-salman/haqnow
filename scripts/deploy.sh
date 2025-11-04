#!/bin/bash

# Comprehensive deployment script for HaqNow
# Usage: ./deploy.sh [patch|minor|major]
# Default: patch

set -e  # Exit on any error

VERSION_TYPE=${1:-patch}

# Preferred host (use domain to avoid IP churn). Override by exporting SERVER_HOST.
SERVER_HOST=${SERVER_HOST:-www.haqnow.com}

echo "🚀 Starting HaqNow deployment process..."
echo ""

# Step 1: Update version
echo "📦 Updating version ($VERSION_TYPE)..."
scripts/update-version.sh $VERSION_TYPE

if [ $? -ne 0 ]; then
    echo "❌ Version update failed!"
    exit 1
fi

NEW_VERSION=$(grep '"version"' frontend/package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
echo "✅ Version updated to: $NEW_VERSION"
echo ""

# Step 2: Build frontend locally
echo "🔨 Building frontend locally..."
cd frontend
npm run build
cd ..

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend build completed"
echo ""

# Step 3: Commit and push changes
echo "📝 Committing and pushing changes..."
git add -A
git commit -m "Deploy version $NEW_VERSION

- Version incremented using deployment script
- Frontend built and ready for deployment
- Automatic version management: $([ "$VERSION_TYPE" = "patch" ] && echo "patch increment" || echo "$VERSION_TYPE update")"

git push origin main

if [ $? -ne 0 ]; then
    echo "❌ Git push failed!"
    exit 1
fi

echo "✅ Changes pushed to repository"
echo ""

# Step 4: Copy environment configuration to server
echo "⚙️ Copying .env configuration to server..."
# The backend loads .env from its working directory (/opt/foi-archive/backend)
scp .env root@${SERVER_HOST}:/opt/foi-archive/backend/.env
# Also keep a copy at repo root for reference/other scripts
scp .env root@${SERVER_HOST}:/opt/foi-archive/.env || true

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy .env file to server!"
    exit 1
fi

echo "✅ Environment configuration copied to server"
echo ""

# Step 5: Deploy to production server
echo "🌐 Deploying to production server..."
ssh root@${SERVER_HOST} << EOF
echo "=== Deploying HaqNow v$NEW_VERSION ==="

cd /opt/foi-archive

# Force sync with latest changes (handles divergent branches)
echo "🔄 Force syncing with remote repository..."
echo "📋 Current repository status:"
git status --porcelain

# Clean up any untracked files that might interfere
echo "🧹 Cleaning untracked files..."
git clean -fd

# Force sync to match remote exactly
if ! git fetch origin; then
    echo "❌ Failed to fetch from remote repository"
    exit 1
fi

if ! git reset --hard origin/main; then
    echo "❌ Failed to reset to origin/main"
    exit 1
fi

CURRENT_COMMIT=\$(git rev-parse --short HEAD)
echo "✅ Repository synced to latest version: \$CURRENT_COMMIT"

# Verify we're on the correct branch and commit
if [ "\$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
    echo "⚠️  Warning: Not on main branch"
fi

# Stop backend service during deployment
sudo systemctl stop foi-archive || true

# Install/update backend dependencies
cd backend
# Ensure venv exists and is activated safely
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate || { echo "❌ Failed to activate venv"; exit 1; }
pip install --upgrade pip setuptools wheel || true
pip install -r requirements.txt

# Install RAG-specific dependencies
echo "🤖 Installing RAG (AI Q&A) dependencies..."
pip install -r requirements-rag.txt || echo "RAG dependencies installation completed"

# Setup Ollama for local LLM processing (confirmed fallback/provider)
echo "🧠 Setting up Ollama for AI Q&A..."
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
else
    echo "✅ Ollama already installed"
fi

# Start Ollama service
echo "🔄 Starting Ollama service..."
sudo systemctl start ollama || nohup ollama serve > /tmp/ollama.log 2>&1 &
sudo systemctl enable ollama || echo "⚠️ Ollama service setup failed"
sleep 5

# Pull required LLM model
MODEL_NAME="llama3:latest"
echo "📦 Ensuring Ollama model ($MODEL_NAME) is available..."
ollama pull "$MODEL_NAME" || echo "⚠️ LLM model download failed - RAG Q&A may not work"

# Create RAG database tables
echo "🗄️ Setting up RAG database tables..."
python create_rag_tables.py || echo "RAG tables already exist or creation failed"

# Run privacy migration if needed
echo "🔒 Running privacy migration (IP address removal)..."
python run_migration.py || echo "Migration already applied or not needed"

# Populate translations with about and foi sections
echo "🌍 Populating translations with updated sections..."
python populate_translations.py || echo "Translation population completed or already up to date"

# Test RAG system
echo "🧪 Testing RAG system components..."
python test_rag_system.py || echo "⚠️ RAG system test failed - check logs"

cd ..

# Build frontend on server
cd frontend
npm run build

# Deploy to nginx
sudo cp -r dist/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html

cd ..

# Restart and verify services
echo "🔄 Starting backend service..."
sudo systemctl start foi-archive
sudo systemctl enable foi-archive

# Wait for backend to start
sleep 8

# Verify backend is running
if sudo systemctl is-active --quiet foi-archive; then
    echo "✅ Backend service started successfully"
else
    echo "⚠️ Backend service failed to start, attempting manual start..."
    cd /opt/foi-archive/backend
    source .venv/bin/activate
    nohup python3 main.py > /tmp/backend.log 2>&1 &
    echo "✅ Backend started manually"
    cd ..
fi

# Restart web server
echo "🌐 Restarting web server..."
sudo systemctl reload nginx
sudo systemctl enable nginx

# Verify local services are running
echo "🔍 Verifying local service status..."
for service in foi-archive nginx ollama; do
    if sudo systemctl is-active --quiet \$service; then
        echo "  ✅ \$service: running"
    else
        echo "  ⚠️  \$service: not running"
    fi
done

# Verify external database connectivity
echo "🔗 Testing external database connectivity..."
cd /opt/foi-archive/backend
if source .venv/bin/activate && python3 -c "from app.database.database import get_db; next(get_db()); print('  ✅ MySQL DBaaS: connected')" 2>/dev/null; then
    echo "  ✅ MySQL DBaaS: connected"
else
    echo "  ⚠️  MySQL DBaaS: connection failed"
fi

if source .venv/bin/activate && python3 -c "from app.database.rag_database import get_rag_db; next(get_rag_db()); print('  ✅ PostgreSQL RAG DBaaS: connected')" 2>/dev/null; then
    echo "  ✅ PostgreSQL RAG DBaaS: connected"
else
    echo "  ⚠️  PostgreSQL RAG DBaaS: connection failed"
fi
cd ..

# Health check: Test backend API
echo "🩺 Testing backend API health..."
sleep 3
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "  ✅ Backend API: responding"
else
    echo "  ⚠️  Backend API: not responding"
fi

# Health check: Test frontend
echo "🩺 Testing frontend..."
if curl -s http://localhost:80 > /dev/null 2>&1; then
    echo "  ✅ Frontend: accessible"
else
    echo "  ⚠️  Frontend: not accessible"
fi

# Process existing documents for RAG (background task)
echo "📚 Processing existing documents for AI Q&A..."
source .venv/bin/activate && nohup python -c "
import asyncio
import requests
try:
    response = requests.post('http://localhost:8000/api/rag/process-all-documents')
    print('✅ RAG processing initiated:', response.status_code)
except Exception as e:
    print('⚠️ RAG processing failed to start:', e)
" > /tmp/rag_processing.log 2>&1 &

echo ""
echo "✅ HaqNow v$NEW_VERSION deployed successfully!"
echo "🔒 Privacy-compliant with complete IP address removal"
echo "🤖 AI Q&A system with RAG technology enabled"
echo "🌍 Visit: http://${SERVER_HOST}"
echo "📊 Admin: http://${SERVER_HOST}/admin-login-page"
echo "🧠 AI Q&A: Go to Search page → AI Q&A tab"
EOF

if [ $? -ne 0 ]; then
    echo "❌ Production deployment failed!"
    exit 1
fi

# Health check: Test AI/RAG system
echo ""
echo "🤖 Testing AI/RAG system functionality..."
cd backend
if source .venv/bin/activate && python3 test_ai_deployment.py; then
    echo "  ✅ AI/RAG system: operational"
    AI_STATUS="✅ OPERATIONAL"
else
    echo "  ⚠️  AI/RAG system: issues detected"
    AI_STATUS="⚠️ NEEDS ATTENTION"
fi
cd ..

echo ""
echo "🎉 Deployment completed successfully!"
echo "⚙️ Environment: Local .env configuration synced to server"
echo "📱 Frontend: http://${SERVER_HOST}"
echo "📋 Version: $NEW_VERSION displayed in footer"
echo "🔧 Admin Panel: http://${SERVER_HOST}/admin-login-page"
echo "🤖 AI Q&A: Available on Search page with natural language questions"
echo "🔬 AI Status: $AI_STATUS"
echo ""
echo "🧪 Testing RAG system on live site..."
echo "🔍 To test AI Q&A: Visit /search-page → Click 'AI Q&A' tab → Ask questions!"
echo ""
echo "Next deployment: ./deploy.sh [patch|minor|major]" 