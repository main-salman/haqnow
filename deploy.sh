#!/bin/bash

# =================================
# Fadih.org - Modern Git-Based Deployment
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

# Check if we're in a git repository
check_git_repo() {
    log "Checking if we're in a git repository..."
    
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "This directory is not a git repository!"
        echo "Please run this script from the root of your Fadih.org project repository."
        exit 1
    fi
    
    success "Git repository detected"
}

# Check if git repo is clean and handle uncommitted changes
check_git_status() {
    log "Checking git repository status..."
    
    # Check if there are any unstaged changes
    if ! git diff-files --quiet; then
        warning "You have unstaged changes!"
        git status --porcelain
        echo
        read -p "Do you want to add and commit these changes? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Adding all changes to git..."
            git add .
        else
            error "Please commit or stash your changes before deploying"
            exit 1
        fi
    fi
    
    # Check if there are any staged but uncommitted changes
    if ! git diff-index --quiet --cached HEAD --; then
        warning "You have staged changes that aren't committed!"
        echo "Staged files:"
        git diff --name-only --cached
        echo
        read -p "Enter commit message (or press Enter for 'Deployment update'): " commit_message
        if [ -z "$commit_message" ]; then
            commit_message="Deployment update"
        fi
        
        log "Committing staged changes..."
        git commit -m "$commit_message"
        success "Changes committed successfully"
    fi
    
    # Check if there are any unstaged changes after potential staging
    if ! git diff-index --quiet HEAD --; then
        warning "You still have uncommitted changes!"
        echo "Uncommitted files:"
        git status --porcelain
        echo
        read -p "Enter commit message (or press Enter for 'Deployment update'): " commit_message
        if [ -z "$commit_message" ]; then
            commit_message="Deployment update"
        fi
        
        log "Committing all changes..."
        git add .
        git commit -m "$commit_message"
        success "All changes committed successfully"
    fi
    
    success "Repository is clean and ready for deployment"
}

# Push to GitHub
push_to_github() {
    log "Pushing latest changes to GitHub..."
    
    # Get current branch
    current_branch=$(git branch --show-current)
    log "Current branch: $current_branch"
    
    # Check if remote exists
    if ! git remote get-url origin > /dev/null 2>&1; then
        error "No 'origin' remote found!"
        echo "Please add your GitHub repository as origin:"
        echo "  git remote add origin $GITHUB_REPO"
        exit 1
    fi
    
    # Fetch to check for any remote changes
    log "Fetching latest changes from remote..."
    git fetch origin
    
    # Check if we're behind the remote
    local_commit=$(git rev-parse HEAD)
    remote_commit=$(git rev-parse origin/$current_branch 2>/dev/null || echo "")
    
    if [ -n "$remote_commit" ] && [ "$local_commit" != "$remote_commit" ]; then
        log "Remote has changes. Checking if we need to merge..."
        
        # Check if we can fast-forward
        merge_base=$(git merge-base HEAD origin/$current_branch)
        if [ "$merge_base" = "$local_commit" ]; then
            # We can fast-forward
            log "Fast-forwarding to latest remote changes..."
            git merge --ff-only origin/$current_branch
        elif [ "$merge_base" = "$remote_commit" ]; then
            # Remote is behind us, safe to push
            log "Local is ahead of remote, proceeding with push..."
        else
            # Diverged branches
            warning "Local and remote branches have diverged!"
            echo "Local commit:  $local_commit"
            echo "Remote commit: $remote_commit"
            echo
            read -p "Do you want to pull and merge first? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git pull origin $current_branch
            else
                error "Please resolve the divergence manually before deploying"
                exit 1
            fi
        fi
    fi
    
    # Push to GitHub
    log "Pushing to origin/$current_branch..."
    git push origin "$current_branch"
    success "Code pushed to GitHub successfully"
    
    # Get the latest commit hash for verification
    latest_commit=$(git rev-parse HEAD)
    log "Latest commit: $latest_commit"
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
    
    # Get the commit hash we're deploying
    deploy_commit=$(git rev-parse HEAD)
    deploy_branch=$(git branch --show-current)
    
    log "Deploying commit: $deploy_commit on branch: $deploy_branch"
    
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
    echo "✅ Repository cloned successfully"
elif [ ! -d "$DEPLOY_PATH/.git" ]; then
    echo "📁 Deployment directory exists but no git repo. Reinitializing..."
    # Backup existing directory and start fresh
    if [ "$(ls -A $DEPLOY_PATH)" ]; then
        echo "📦 Backing up existing directory..."
        backup_dir="/tmp/fadih-backup-$(date +%s)"
        mv "$DEPLOY_PATH" "$backup_dir"
        echo "📦 Backup saved to: $backup_dir"
    fi
    # Create fresh directory and clone
    mkdir -p "$DEPLOY_PATH"
    cd "$DEPLOY_PATH"
    git clone "$GITHUB_REPO" .
    echo "✅ Repository cloned successfully"
else
    echo "📦 Updating existing git repository..."
    cd "$DEPLOY_PATH"
    
    # Ensure we have the latest remote references
    echo "🔄 Fetching latest changes from GitHub..."
    git fetch origin
    
    # Get current branch or default to main
    current_branch=$(git branch --show-current 2>/dev/null || echo "main")
    echo "📋 Current branch: $current_branch"
    
    # Reset to latest origin version (force update)
    echo "🔄 Resetting to latest origin/$current_branch..."
    git reset --hard origin/$current_branch
    
    # Clean any untracked files
    git clean -fd
    
    echo "✅ Repository updated to latest version"
fi

# Show current commit for verification
current_commit=$(git rev-parse HEAD)
echo "📋 Current commit: $current_commit"

# Install git if not present (shouldn't be needed but just in case)
if ! command -v git &> /dev/null; then
    echo "📦 Installing git..."
    apt-get update
    apt-get install -y git
fi

# Install/update system dependencies for Python packages
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

# Setup MySQL if not already configured
if ! mysql -u foi_user -p***REMOVED*** -e "USE foi_archive;" 2>/dev/null; then
    echo "🗄️ Setting up MySQL database..."
    mysql -e "CREATE DATABASE IF NOT EXISTS foi_archive;"
    mysql -e "CREATE USER IF NOT EXISTS 'foi_user'@'localhost' IDENTIFIED BY '***REMOVED***';"
    mysql -e "GRANT ALL PRIVILEGES ON foi_archive.* TO 'foi_user'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    echo "✅ MySQL database configured"
else
    echo "✅ MySQL database already configured"
fi

# Install/update Python dependencies
echo "📦 Installing Python dependencies..."
cd "$DEPLOY_PATH/backend"

# Install UV if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create virtual environment and install dependencies
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    uv venv --python python3
fi

source .venv/bin/activate
echo "📦 Installing Python packages..."
uv pip install -r requirements.txt

echo "✅ Python dependencies installed"

# Install/update Node.js dependencies and build frontend
echo "📦 Installing Node.js dependencies..."
cd "$DEPLOY_PATH/frontend"

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    apt-get install -y nodejs
fi

# Install dependencies and build
echo "📦 Installing npm packages..."
npm install --legacy-peer-deps

echo "🏗️ Building frontend..."
npm run build

echo "✅ Frontend built successfully"

# Ensure environment file exists with correct configuration
echo "🔧 Setting up environment configuration..."
cd "$DEPLOY_PATH"

if [ ! -f ".env" ]; then
    echo "⚠️ No .env file found. Creating default .env file..."
    cat << ENV_FILE > .env
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=False

# Database Configuration - Local MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=foi_user
MYSQL_PASSWORD=***REMOVED***
MYSQL_DATABASE=foi_archive
DATABASE_URL=mysql+pymysql://foi_user:***REMOVED***@localhost:3306/foi_archive

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin User Configuration
ADMIN_EMAIL=admin@fadih.org
ADMIN_PASSWORD=admin123

# S3 Configuration (Update with your actual credentials)
AWS_ACCESS_KEY_ID=your-s3-access-key
AWS_SECRET_ACCESS_KEY=your-s3-secret-key
AWS_BUCKET_NAME=foi-archive-documents
AWS_REGION=ch-dk-2
S3_ENDPOINT=https://sos-ch-dk-2.exo.io

# Email Configuration
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@fadih.org

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
    echo "✅ Default .env file created"
    echo "⚠️ Please update .env with your actual credentials!"
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
Description=Fadih.org Application
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
    echo "📦 Installing nginx..."
    apt-get update
    apt-get install -y nginx
fi

cat << 'NGINX_CONFIG' > /etc/nginx/sites-available/foi-archive
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
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
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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

# Initialize database
echo "🗄️ Initializing database..."
cd "$DEPLOY_PATH/backend"
source .venv/bin/activate

# Test database connection first
echo "🔍 Testing database connection..."
python -c "
import os
import sys
from sqlalchemy import create_engine, text

# Set up environment
sys.path.append('.')
from app.database.database import engine

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# Initialize database tables
echo "🗄️ Creating database tables..."
python -c "
import sys
sys.path.append('.')
from app.database.database import init_db
try:
    init_db()
    print('✅ Database tables created successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
"

# Reload services
echo "🔄 Restarting services..."
systemctl daemon-reload
systemctl enable foi-archive

# Stop service if running
systemctl stop foi-archive 2>/dev/null || true

# Start the service
echo "🚀 Starting Fadih.org service..."
if systemctl start foi-archive; then
    echo "✅ Fadih.org service started successfully"
    
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
    echo "❌ Fadih.org service failed to start"
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
server_ip=$(curl -s http://ipinfo.io/ip 2>/dev/null || echo "159.100.250.145")
echo "• Frontend: http://$server_ip"
echo "• Backend API: http://$server_ip/api"
echo "• Health Check: http://$server_ip/api/health"
echo "• Admin Login: http://$server_ip/admin-login-page"
echo
echo "🔧 Troubleshooting:"
echo "==================="
echo "• Backend logs: journalctl -u foi-archive -f"
echo "• Nginx logs: journalctl -u nginx -f"
echo "• Config test: nginx -t"
echo "• Service restart: systemctl restart foi-archive"

DEPLOY_SCRIPT

    # Copy and execute the deployment script on the server
    log "Copying deployment script to server..."
    scp /tmp/deploy_remote.sh "$SERVER_USER@$SERVER_IP:/tmp/"
    
    log "Executing deployment on server..."
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
    echo "• Deployed Commit: $(git rev-parse HEAD)"
    echo "• Deployed Branch: $(git branch --show-current)"
    echo
    echo "🌐 Your Fadih.org application should be available at: http://$SERVER_IP"
    echo
    echo "📊 To check logs:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Fadih.org - Git-Based Deployment${NC}"
    echo "======================================"
    echo
    
    # Deployment workflow
    check_git_repo
    check_git_status
    push_to_github  
    test_ssh_connection
    deploy_to_server
    show_deployment_info
    
    success "Deployment process completed! 🎉"
    echo
    echo "🎯 Next steps:"
    echo "1. Visit http://$SERVER_IP to see your application"
    echo "2. Update the .env file on the server with your actual credentials"
    echo "3. Test the upload functionality"
    echo "4. Access admin panel at http://$SERVER_IP/admin-login-page"
}

# Run main function
main "$@" 