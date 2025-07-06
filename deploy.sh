#!/bin/bash

# =================================
# FOI Archive - Modern Git-Based Deployment
# =================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="https://github.com/main-salman/fadih.git"
SERVER_IP="159.100.250.145"
SERVER_USER="root"
DEPLOY_PATH="/opt/foi-archive"
SERVICE_NAME="foi-archive"

# Helper functions
log() {
    echo -e "${BLUE}📋 $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if git repo is clean
check_git_status() {
    log "Checking git repository status..."
    
    if ! git diff-index --quiet HEAD --; then
        warning "You have uncommitted changes!"
        echo "Uncommitted files:"
        git status --porcelain
        echo
        log "Auto-committing changes with message 'update'..."
        git add .
        git commit -m "update"
        success "Changes committed automatically"
    fi
}

# Push to GitHub
push_to_github() {
    log "Pushing latest changes to GitHub..."
    
    # Get current branch
    current_branch=$(git branch --show-current)
    
    git push origin "$current_branch"
    success "Code pushed to GitHub successfully"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection to server..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
        success "SSH connection successful"
    else
        error "Cannot connect to server via SSH"
        echo "Please ensure:"
        echo "1. Server is running: $SERVER_IP"
        echo "2. SSH keys are properly configured"
        echo "3. You can connect manually: ssh $SERVER_USER@$SERVER_IP"
        exit 1
    fi
}

# Deploy to server
deploy_to_server() {
    log "Deploying to server: $SERVER_IP"
    
    # Create deployment script that will run on the server
    cat << 'DEPLOY_SCRIPT' > /tmp/deploy_remote.sh
#!/bin/bash

set -e

DEPLOY_PATH="/opt/foi-archive"
SERVICE_NAME="foi-archive"
GITHUB_REPO="https://github.com/main-salman/fadih.git"

echo "🚀 Starting deployment on server..."

# Handle deployment directory
if [ ! -d "$DEPLOY_PATH" ]; then
    echo "📁 Creating deployment directory and cloning repository..."
    mkdir -p "$DEPLOY_PATH"
    cd "$DEPLOY_PATH"
    git clone "$GITHUB_REPO" .
elif [ ! -d "$DEPLOY_PATH/.git" ]; then
    echo "📁 Deployment directory exists but no git repo. Reinitializing..."
    # Backup existing directory and start fresh
    if [ "$(ls -A $DEPLOY_PATH)" ]; then
        echo "📦 Backing up existing directory..."
        backup_dir="/tmp/foi-backup-$(date +%s)"
        mv "$DEPLOY_PATH" "$backup_dir"
        echo "📦 Backup saved to: $backup_dir"
    fi
    # Create fresh directory and clone
    mkdir -p "$DEPLOY_PATH"
    cd "$DEPLOY_PATH"
    git clone "$GITHUB_REPO" .
else
    echo "📦 Updating existing git repository..."
    cd "$DEPLOY_PATH"
    
    # Ensure we're on the main branch and pull latest changes
    git fetch origin
    git reset --hard origin/main
fi

echo "✅ Code updated successfully"

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get update
    apt-get install -y git
fi

# Install system dependencies for Python packages
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y \
    pkg-config \
    libmysqlclient-dev \
    mysql-client \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    wget

echo "✅ System dependencies installed"

# Install/update Python dependencies
echo "📦 Installing Python dependencies..."
cd "$DEPLOY_PATH/backend"

# Install UV if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create virtual environment and install dependencies
if [ ! -d ".venv" ]; then
    uv venv --python python3
fi

source .venv/bin/activate
uv pip install -r requirements.txt

echo "✅ Python dependencies installed"

# Install/update Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd "$DEPLOY_PATH/frontend"

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    apt-get install -y nodejs
fi

# Install dependencies and build
npm install
npm run build

echo "✅ Frontend built successfully"

# Update environment file
echo "🔧 Setting up environment..."
cd "$DEPLOY_PATH"

if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating production .env file..."
    cat << ENV_FILE > .env
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=False

# Database Configuration
DATABASE_URL=${DATABASE_URL}

# JWT Configuration
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin User Configuration
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# S3 Configuration
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_BUCKET_NAME=foi-archive-documents
AWS_REGION=ch-dk-2
S3_ENDPOINT=https://sos-ch-dk-2.exo.io

# Email Configuration
SENDGRID_API_KEY=${SENDGRID_API_KEY}
FROM_EMAIL=noreply@foiarchive.com

# Security Configuration
ALLOWED_ORIGINS=http://159.100.250.145,https://159.100.250.145
ALLOWED_HOSTS=159.100.250.145,localhost,127.0.0.1

# File Upload Configuration
UPLOAD_DIR=/opt/foi-archive/uploads
MAX_FILE_SIZE=50000000

# Application Configuration
HOST=0.0.0.0
PORT=8000
ENV_FILE
    echo "✅ Production .env file created with proper configuration"
else
    echo "✅ Using existing .env file"
fi

# Create uploads directory
mkdir -p /opt/foi-archive/uploads
chmod 755 /opt/foi-archive/uploads

# Create or update systemd service
echo "🔧 Setting up systemd service..."
cat << 'SERVICE_FILE' > /etc/systemd/system/foi-archive.service
[Unit]
Description=FOI Archive Application
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/foi-archive/backend
Environment=PATH=/opt/foi-archive/backend/.venv/bin
ExecStart=/opt/foi-archive/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_FILE

# Create nginx configuration
echo "🔧 Setting up Nginx..."

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt-get update
    apt-get install -y nginx
fi

cat << 'NGINX_CONFIG' > /etc/nginx/sites-available/foi-archive
server {
    listen 80;
    server_name _;
    
    # Frontend static files
    location / {
        root /opt/foi-archive/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONFIG

# Enable the site
if [ ! -L "/etc/nginx/sites-enabled/foi-archive" ]; then
    ln -s /etc/nginx/sites-available/foi-archive /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
fi

# Test nginx configuration
nginx -t || {
    echo "❌ Nginx configuration error"
    exit 1
}

# Reload services
echo "🔄 Restarting services..."
systemctl daemon-reload
systemctl enable foi-archive

# Initialize database
echo "🔧 Initializing database..."
cd "$DEPLOY_PATH/backend"
source .venv/bin/activate

# Test database connection first
echo "🔍 Testing database connection..."
python -c "
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
if not db_url:
    raise Exception('DATABASE_URL not found in .env file')

print(f'Connecting to database...')
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
" || {
    echo "❌ Database connection failed"
    echo "📋 Environment variables:"
    cd "$DEPLOY_PATH/backend"
    grep -E "(DATABASE_URL|MYSQL)" .env || echo "No database config found"
    exit 1
}

# Initialize database tables
echo "🔧 Creating database tables..."
python -c "
from app.database.database import init_db
init_db()
print('✅ Database tables created successfully')
" || {
    echo "❌ Database initialization failed"
    exit 1
}

# Stop service if running
systemctl stop foi-archive 2>/dev/null || true

# Start the service
echo "🚀 Starting FOI Archive service..."
if systemctl start foi-archive; then
    echo "✅ FOI Archive service started successfully"
    
    # Wait a moment for service to start
    sleep 3
    
    # Check if service is actually running
    if systemctl is-active --quiet foi-archive; then
        echo "✅ Service is running"
        
        # Test if the API is responding
        echo "🔍 Testing API endpoint..."
        for i in {1..10}; do
            if curl -s http://localhost:8000/health > /dev/null; then
                echo "✅ API is responding on port 8000"
                break
            elif [ $i -eq 10 ]; then
                echo "❌ API not responding after 10 attempts"
                echo "📋 Service logs:"
                journalctl -u foi-archive --no-pager -n 20
                exit 1
            else
                echo "⏳ Waiting for API to start (attempt $i/10)..."
                sleep 2
            fi
        done
    else
        echo "❌ Service failed to start properly"
        echo "📋 Service logs:"
        journalctl -u foi-archive --no-pager -n 20
        exit 1
    fi
else
    echo "❌ FOI Archive service failed to start"
    echo "📋 Service logs:"
    journalctl -u foi-archive --no-pager -n 20
    exit 1
fi

# Reload nginx
if systemctl reload nginx; then
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx reload failed"
    nginx -t
    exit 1
fi

echo "✅ Deployment completed successfully!"

# Show service status and helpful information
echo
echo "📊 Service Status:"
echo "==================="
systemctl status foi-archive --no-pager -l || true
echo
echo "📊 Nginx Status:"
echo "================"
systemctl status nginx --no-pager -l || true
echo
echo "🔍 Port Status:"
echo "==============="
ss -tlnp | grep -E "(8000|80)" || echo "No services found on ports 80/8000"
echo
echo "🌐 Application URLs:"
echo "==================="
server_ip=$(curl -s http://ipinfo.io/ip 2>/dev/null || echo "YOUR_SERVER_IP")
echo "• Frontend: http://$server_ip"
echo "• Backend API: http://$server_ip/api"
echo "• Health Check: http://$server_ip/api/health"
echo
echo "🔧 Troubleshooting:"
echo "==================="
echo "• Backend logs: journalctl -u foi-archive -f"
echo "• Nginx logs: journalctl -u nginx -f"
echo "• Config test: nginx -t"
echo "• Service restart: systemctl restart foi-archive"

DEPLOY_SCRIPT

    # Copy and execute the deployment script on the server
    scp /tmp/deploy_remote.sh "$SERVER_USER@$SERVER_IP:/tmp/"
    ssh "$SERVER_USER@$SERVER_IP" "chmod +x /tmp/deploy_remote.sh && /tmp/deploy_remote.sh"
    
    # Clean up
    rm /tmp/deploy_remote.sh
    
    success "Deployment completed successfully!"
}

# Show deployment info
show_deployment_info() {
    echo
    log "Deployment Summary:"
    echo "• Repository: $GITHUB_REPO"
    echo "• Server: $SERVER_IP"
    echo "• Deploy Path: $DEPLOY_PATH"
    echo "• Service: $SERVICE_NAME"
    echo
    echo "🌐 Your application should be available at: http://$SERVER_IP"
    echo
    echo "📊 To check logs:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
}

# Load production environment variables
load_production_env() {
    if [ -f ".env.production" ]; then
        log "Loading production environment variables..."
        export $(cat .env.production | grep -v '^#' | xargs)
        success "Production environment variables loaded"
    else
        error "Production environment file '.env.production' not found"
        echo "Please create .env.production with your production secrets:"
        echo "  DATABASE_URL=mysql://..."
        echo "  JWT_SECRET_KEY=..."
        echo "  ADMIN_EMAIL=..."
        echo "  ADMIN_PASSWORD=..."
        echo "  AWS_ACCESS_KEY_ID=..."
        echo "  AWS_SECRET_ACCESS_KEY=..."
        echo "  SENDGRID_API_KEY=..."
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🚀 FOI Archive - Git-Based Deployment${NC}"
    echo "======================================"
    echo
    
    # Deployment workflow
    load_production_env
    check_git_status
    push_to_github  
    test_ssh_connection
    deploy_to_server
    show_deployment_info
    
    success "Deployment process completed! 🎉"
}

# Run main function
main "$@" 