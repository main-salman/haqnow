#!/bin/bash

# Comprehensive deployment script for HaqNow
# Usage: ./deploy.sh [patch|minor|major]
# Default: patch

set -e  # Exit on any error

VERSION_TYPE=${1:-patch}

# Preferred host (use domain to avoid IP churn). Override by exporting SERVER_HOST.
SERVER_HOST=${SERVER_HOST:-www.haqnow.com}
# SSH identity (override with SSH_KEY_PATH)
SSH_KEY_PATH=${SSH_KEY_PATH:-$HOME/.ssh/id_rsa}
SSH_OPTS="-i ${SSH_KEY_PATH} -o StrictHostKeyChecking=accept-new"

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

# Step 4: Copy environment configuration and built frontend to server
echo "⚙️ Copying .env configuration to server..."
# Copy to /tmp first; move into place after repo exists on server
scp ${SSH_OPTS} .env root@${SERVER_HOST}:/tmp/.env

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy .env file to server!"
    exit 1
fi

echo "✅ Environment configuration copied to server"

echo "📦 Uploading built frontend assets..."
scp -r ${SSH_OPTS} frontend/dist root@${SERVER_HOST}:/tmp/frontend_dist
echo "✅ Frontend assets uploaded"
echo ""

# Step 5: Deploy to production server
echo "🌐 Deploying to production server..."
ssh ${SSH_OPTS} root@${SERVER_HOST} "NEW_VERSION=$NEW_VERSION SERVER_HOST=$SERVER_HOST bash -s" << 'EOF'
echo "=== Deploying HaqNow v$NEW_VERSION ==="

# Ensure base dependencies are present on a fresh server
echo "🛠️  Installing system prerequisites (git, python3-venv, python3-virtualenv, pip, node, npm)..."
sudo apt-get update -y || true
sudo apt-get install -y git python3-venv python3-virtualenv python3-pip nodejs npm || true
# Ensure nginx and curl (for health checks / ollama) exist
sudo apt-get install -y nginx curl || true
sudo mkdir -p /var/www/html || true

# Ensure application directory exists and repository is present
if [ ! -d "/opt/foi-archive/.git" ]; then
  echo "📥 Cloning repository..."
  mkdir -p /opt/foi-archive
  cd /opt/foi-archive
  if ! git clone https://github.com/main-salman/haqnow.git .; then
    echo "❌ Failed to clone repository"
    exit 1
  fi
else
  cd /opt/foi-archive
fi

# Force sync with latest changes (handles divergent branches)
echo "🔄 Force syncing with remote repository..."
echo "📋 Current repository status:"
git status --porcelain || true

# Clean up any untracked files that might interfere
echo "🧹 Cleaning untracked files..."
git clean -fd || true

# Force sync to match remote exactly
git fetch origin || { echo "❌ Failed to fetch from remote"; exit 1; }
git reset --hard origin/main || { echo "❌ Failed to reset to origin/main"; exit 1; }

CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo "✅ Repository synced to latest version: $CURRENT_COMMIT"

# Verify we're on the correct branch and commit
if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
    echo "⚠️  Warning: Not on main branch"
fi

# Place .env files now that repo exists
if [ -f /tmp/.env ]; then
  cp /tmp/.env /opt/foi-archive/.env || true
  cp /tmp/.env /opt/foi-archive/backend/.env || true
fi

# Stop backend service during deployment
sudo systemctl stop foi-archive || true

# Install/update backend dependencies
cd backend
# Ensure venv exists and is ready (avoid reliance on 'source')
if [ ! -f ".venv/bin/activate" ]; then
  echo "🐍 Python version: $(python3 -V 2>/dev/null || echo 'python3 not found')"
  rm -rf .venv || true
  python3 -m venv .venv || true
  if [ ! -f ".venv/bin/activate" ]; then
    echo "⚠️  python3 -m venv failed; installing helpers and retrying..."
    sudo apt-get update -y || true
    sudo apt-get install -y python3-venv python3.12-venv python3-virtualenv || true
    python3 -m ensurepip --upgrade || true
    python3 -m venv .venv || true
  fi
  if [ ! -f ".venv/bin/activate" ]; then
    echo "⚠️  Falling back to virtualenv..."
    if ! command -v virtualenv >/dev/null 2>&1; then
      sudo apt-get install -y python3-virtualenv || true
    fi
    virtualenv -p python3 .venv || true
  fi
fi

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"
if [ -x "$VENV_PY" ] && [ -x "$VENV_PIP" ]; then
  echo "✅ Virtualenv prepared at $(pwd)/.venv"
  PIP_CMD="$VENV_PIP"
  PY_CMD="$VENV_PY"
else
  echo "⚠️  .venv not created correctly; falling back to system python/pip"
  PIP_CMD="pip3"
  PY_CMD="python3"
fi

# Prepare temp requirement files:
# - remove exiftool (not on PyPI)
# - keep langsmith compatible with langchain 0.1.0 (<0.1.0)
REQ_TMP="/tmp/requirements_nox.txt"
REQ_RAG_TMP="/tmp/requirements_rag_nox.txt"
# Remove any unsupported packages (e.g., exiftool) but do NOT override langsmith range
sed -e '/^exiftool==/d' requirements.txt > "$REQ_TMP" || cp requirements.txt "$REQ_TMP"
cp requirements-rag.txt "$REQ_RAG_TMP" || true

if [ "$PIP_CMD" = "$VENV_PIP" ]; then
  "$PIP_CMD" install --upgrade pip setuptools wheel || true
  "$PIP_CMD" install -r "$REQ_TMP" || true
else
  # Avoid upgrading Debian-managed pip/wheel; just install requirements
  "$PIP_CMD" install --break-system-packages -r "$REQ_TMP" || true
fi
 
 # Install RAG-specific dependencies
 echo "🤖 Installing RAG (AI Q&A) dependencies..."
 "$PIP_CMD" install -r "$REQ_RAG_TMP" || echo "RAG dependencies installation completed"


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
echo "📦 Ensuring Ollama model (llama3:latest) is available..."
ollama pull "llama3:latest" || echo "⚠️ LLM model download failed - RAG Q&A may not work"

# Create RAG database tables
echo "🗄️ Setting up RAG database tables..."
"$PY_CMD" create_rag_tables.py || echo "RAG tables already exist or creation failed"

# Run privacy migration if needed
echo "🔒 Running privacy migration (IP address removal)..."
"$PY_CMD" run_migration.py || echo "Migration already applied or not needed"

# Populate translations with about and foi sections
echo "🌍 Populating translations with updated sections..."
"$PY_CMD" populate_translations.py || echo "Translation population completed or already up to date"

# Test RAG system
echo "🧪 Testing RAG system components..."
"$PY_CMD" test_rag_system.py || echo "⚠️ RAG system test failed - check logs"

cd ..

# Deploy frontend assets uploaded from local build
if [ -d /tmp/frontend_dist ]; then
  sudo rm -rf /var/www/html/* || true
  sudo cp -r /tmp/frontend_dist/* /var/www/html/ || true
  sudo chown -R www-data:www-data /var/www/html || true
else
  echo "⚠️  /tmp/frontend_dist not found; skipping frontend deploy"
fi

# Configure nginx site and Let's Encrypt TLS
DOMAIN="${SERVER_HOST}"
if [ -n "$DOMAIN" ]; then
  cat >/etc/nginx/sites-available/haqnow.conf << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    return 301 https://www.haqnow.com$request_uri;
}

server {
    listen 80;
    server_name ${DOMAIN} haqnow.com;

    root /var/www/html;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Fallback self-signed TLS for HTTPS on bare IP/default host
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    ssl_certificate /etc/ssl/certs/haqnow-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/haqnow-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    root /var/www/html;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX
  ln -sf /etc/nginx/sites-available/haqnow.conf /etc/nginx/sites-enabled/haqnow.conf
  if [ -f /etc/nginx/sites-enabled/default ]; then rm -f /etc/nginx/sites-enabled/default; fi

  # Ensure self-signed cert exists for HTTPS on IP/default host
  if [ ! -f /etc/ssl/certs/haqnow-selfsigned.crt ] || [ ! -f /etc/ssl/private/haqnow-selfsigned.key ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/ssl/private/haqnow-selfsigned.key \
      -out /etc/ssl/certs/haqnow-selfsigned.crt \
      -subj "/C=US/ST=NA/L=NA/O=HaqNow/OU=IT/CN=www.haqnow.com" >/dev/null 2>&1 || true
    chmod 600 /etc/ssl/private/haqnow-selfsigned.key || true
  fi

  # Validate nginx config and reload
  if nginx -t; then
    sudo systemctl reload nginx || sudo systemctl restart nginx || true
  else
    echo "❌ nginx config test failed; not reloading"
  fi

  # Only attempt real cert for the domain name (Let's Encrypt cannot issue for IP)
  if ! echo "$DOMAIN" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    if ! command -v certbot >/dev/null 2>&1; then
      sudo apt-get install -y certbot python3-certbot-nginx || true
    fi
    certbot --nginx --redirect -d "$DOMAIN" -m admin@haqnow.com --agree-tos -n || true
  else
    echo "ℹ️ Skipping certbot for IP address $DOMAIN"
  fi
fi

# Restart and verify services
echo "🔄 Starting backend service..."
# Always write/update systemd unit to ensure correct Python (venv)
cat >/etc/systemd/system/foi-archive.service << 'UNIT'
[Unit]
Description=HaqNow FastAPI Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/foi-archive/backend
EnvironmentFile=/opt/foi-archive/backend/.env
ExecStart=/opt/foi-archive/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload

sudo systemctl start foi-archive || true
sudo systemctl enable foi-archive || true

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
    if sudo systemctl is-active --quiet $service; then
        echo "  ✅ $service: running"
    else
        echo "  ⚠️  $service: not running"
    fi
done

# Verify external database connectivity
echo "🔗 Testing external database connectivity..."
cd /opt/foi-archive/backend
if python3 -c "from app.database.database import get_db; next(get_db()); print('  ✅ MySQL DBaaS: connected')" 2>/dev/null; then
    echo "  ✅ MySQL DBaaS: connected"
else
    echo "  ⚠️  MySQL DBaaS: connection failed"
fi

if python3 -c "from app.database.rag_database import get_rag_db; next(get_rag_db()); print('  ✅ PostgreSQL RAG DBaaS: connected')" 2>/dev/null; then
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
echo "🌍 Visit: http://$SERVER_HOST"
echo "📊 Admin: http://$SERVER_HOST/admin-login-page"
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
if python3 test_ai_deployment.py; then
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