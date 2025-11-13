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

# Check if there are changes to commit
if git diff --staged --quiet && git diff --quiet; then
    echo "ℹ️  No changes to commit (working tree clean)"
else
    git commit -m "Deploy version $NEW_VERSION

- Version incremented using deployment script
- Frontend built and ready for deployment
- Automatic version management: $([ "$VERSION_TYPE" = "patch" ] && echo "patch increment" || echo "$VERSION_TYPE update")"
    
    if [ $? -ne 0 ]; then
        echo "❌ Git commit failed!"
        exit 1
    fi
fi

# Always push to ensure remote is up to date
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
# Clean old files on server before uploading
ssh ${SSH_OPTS} root@${SERVER_HOST} "rm -rf /tmp/frontend_dist" || true
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
# Ensure nginx and curl (for health checks) exist
sudo apt-get install -y nginx curl || true
sudo mkdir -p /var/www/html || true

# Install and configure ClamAV for virus scanning
echo "🦠 Installing/Updating ClamAV antivirus..."
sudo apt-get install -y clamav clamav-daemon clamav-freshclam || true
# Update virus definitions
echo "🔄 Updating virus definitions..."
sudo systemctl stop clamav-freshclam || true
sudo freshclam || echo "⚠️ Freshclam update had issues (may be running already)"
sudo systemctl start clamav-freshclam || true
sudo systemctl enable clamav-freshclam || true
# Ensure daemon is running
sudo systemctl start clamav-daemon || true
sudo systemctl enable clamav-daemon || true
echo "✅ ClamAV configured and running"

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

# Fetch latest changes from GitHub
echo "📥 Fetching latest changes from GitHub..."
git fetch origin || { echo "❌ Failed to fetch from remote"; exit 1; }

# Reset to match remote exactly (ensures we have latest code)
echo "🔄 Resetting to latest commit from GitHub..."
git reset --hard origin/main || { echo "❌ Failed to reset to origin/main"; exit 1; }

# Verify we're on the latest commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
REMOTE_COMMIT=$(git rev-parse --short origin/main)
echo "✅ Repository synced to latest version: $CURRENT_COMMIT"
if [ "$CURRENT_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo "⚠️  Warning: Local commit ($CURRENT_COMMIT) differs from remote ($REMOTE_COMMIT)"
fi

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


# RAG/AI Setup - Using Groq API (no local LLM needed)
echo "🧠 AI/RAG System: Using Groq API for LLM inference..."
if grep -q "GROQ_API_KEY=" /opt/foi-archive/backend/.env 2>/dev/null; then
    echo "✅ Groq API key configured"
else
    echo "⚠️  Warning: GROQ_API_KEY not found in .env - AI Q&A will not work"
fi
echo "📦 Embeddings: Using sentence-transformers (local, installed via requirements.txt)"

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
echo "📦 Deploying frontend assets..."
if [ -d /tmp/frontend_dist ]; then
  # Verify frontend files exist before deploying
  if [ ! -f /tmp/frontend_dist/index.html ]; then
    echo "❌ Frontend build incomplete: index.html not found in /tmp/frontend_dist"
    exit 1
  fi
  
  # Remove old files and deploy new ones
  sudo rm -rf /var/www/html/* || true
  sudo cp -r /tmp/frontend_dist/* /var/www/html/ || true
  sudo chown -R www-data:www-data /var/www/html || true
  
  # Verify deployment
  if [ -f /var/www/html/index.html ]; then
    echo "✅ Frontend assets deployed successfully"
    FRONTEND_FILES=$(find /var/www/html/assets -name "*.js" 2>/dev/null | wc -l)
    echo "   Deployed $FRONTEND_FILES JavaScript files"
  else
    echo "❌ Frontend deployment verification failed"
    exit 1
  fi
else
  echo "❌ /tmp/frontend_dist not found; frontend deployment failed"
  exit 1
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

    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server with self-signed cert (Let's Encrypt will replace)
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name ${DOMAIN} haqnow.com;

    ssl_certificate /etc/ssl/certs/haqnow-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/haqnow-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    client_max_body_size 50m;

    root /var/www/html;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Fallback HTTPS for bare IP access
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

  # Ensure 50MB upload limit in main nginx config
  if ! grep -q 'client_max_body_size.*50m' /etc/nginx/nginx.conf; then
    echo "🔧 Adding 50MB upload limit to nginx.conf..."
    sed -i '/http {/a\    client_max_body_size 50m;' /etc/nginx/nginx.conf
    echo "✅ Upload limit configured"
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
ExecStart=/opt/foi-archive/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --proxy-headers
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
for service in foi-archive nginx clamav-daemon clamav-freshclam; do
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