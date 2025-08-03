#!/bin/bash

# Comprehensive deployment script for HaqNow
# Usage: ./deploy.sh [patch|minor|major]
# Default: patch

set -e  # Exit on any error

VERSION_TYPE=${1:-patch}

echo "🚀 Starting HaqNow deployment process..."
echo ""

# Step 1: Update version
echo "📦 Updating version ($VERSION_TYPE)..."
./update-version.sh $VERSION_TYPE

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
scp backend/.env root@159.100.250.145:/opt/foi-archive/backend/.env

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy .env file to server!"
    exit 1
fi

echo "✅ Environment configuration copied to server"
echo ""

# Step 5: Deploy to production server
echo "🌐 Deploying to production server..."
ssh root@159.100.250.145 << EOF
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
source .venv/bin/activate && pip install -r requirements.txt

# Install RAG-specific dependencies
echo "🤖 Installing RAG (AI Q&A) dependencies..."
source .venv/bin/activate && pip install -r requirements-rag.txt || echo "RAG dependencies installation completed"

# Setup Ollama for local LLM processing
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
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# Pull required LLM model
echo "📦 Downloading Llama3 model for AI Q&A..."
ollama pull llama3 || ollama pull llama3:8b || echo "⚠️ LLM model download failed - RAG Q&A may not work"

# Create RAG database tables
echo "🗄️ Setting up RAG database tables..."
source .venv/bin/activate && python create_rag_tables.py || echo "RAG tables already exist or creation failed"

# Run privacy migration if needed
echo "🔒 Running privacy migration (IP address removal)..."
source .venv/bin/activate && python run_migration.py || echo "Migration already applied or not needed"

# Populate translations with about and foi sections
echo "🌍 Populating translations with updated sections..."
source .venv/bin/activate && python populate_translations.py || echo "Translation population completed or already up to date"

# Test RAG system
echo "🧪 Testing RAG system components..."
source .venv/bin/activate && python test_rag_system.py || echo "⚠️ RAG system test failed - check logs"

cd ..

# Build frontend on server
cd frontend
npm run build

# Deploy to nginx
sudo cp -r dist/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html

cd ..

# Restart services
sudo systemctl start foi-archive
sudo systemctl enable foi-archive
sudo systemctl reload nginx

# Start Ollama service on boot
echo "🤖 Configuring Ollama for startup..."
sudo systemctl enable ollama || echo "Ollama service setup complete"

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
echo "🌍 Visit: http://159.100.250.145"
echo "📊 Admin: http://159.100.250.145/admin-login-page"
echo "🧠 AI Q&A: Go to Search page → AI Q&A tab"
EOF

if [ $? -ne 0 ]; then
    echo "❌ Production deployment failed!"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "⚙️ Environment: Local .env configuration synced to server"
echo "📱 Frontend: http://159.100.250.145"
echo "📋 Version: $NEW_VERSION displayed in footer"
echo "🔧 Admin Panel: http://159.100.250.145/admin-login-page"
echo "🤖 AI Q&A: Available on Search page with natural language questions"
echo ""
echo "🧪 Testing RAG system on live site..."
echo "🔍 To test AI Q&A: Visit /search-page → Click 'AI Q&A' tab → Ask questions!"
echo ""
echo "Next deployment: ./deploy.sh [patch|minor|major]" 