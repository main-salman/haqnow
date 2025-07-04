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
        read -p "Do you want to commit these changes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter commit message: " commit_msg
            git add .
            git commit -m "$commit_msg"
            success "Changes committed"
        else
            error "Please commit or stash your changes before deploying"
            exit 1
        fi
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
    echo "Warning: .env file not found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please configure your .env file with actual values"
    echo "Edit: nano /opt/foi-archive/.env"
fi

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
ExecStart=/opt/foi-archive/backend/.venv/bin/python main.py
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
systemctl restart foi-archive
systemctl reload nginx

echo "✅ Deployment completed successfully!"

# Show service status
echo "📊 Service Status:"
systemctl status foi-archive --no-pager -l || true
echo
echo "🌐 Application should be available at: http://$(curl -s http://ipinfo.io/ip 2>/dev/null || echo 'YOUR_SERVER_IP')"

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

# Main execution
main() {
    echo -e "${BLUE}🚀 FOI Archive - Git-Based Deployment${NC}"
    echo "======================================"
    echo
    
    # Deployment workflow
    check_git_status
    push_to_github  
    test_ssh_connection
    deploy_to_server
    show_deployment_info
    
    success "Deployment process completed! 🎉"
}

# Run main function
main "$@" 