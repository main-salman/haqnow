#!/bin/bash

# update.sh - Fast update script for HaqNow
# Syncs code changes without full reinstallation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server configuration (prefer domain; override by exporting SERVER_HOST)
SERVER_HOST="${SERVER_HOST:-www.haqnow.com}"
SERVER_USER="root"
SERVER_DIR="/opt/foi-archive"

echo -e "${BLUE}🚀 HaqNow - Fast Update${NC}"
echo "=============================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ This directory is not a git repository${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Checking git repository status...${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes!${NC}"
    git status --porcelain
    echo ""
    read -p "Do you want to add and commit these changes? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📋 Adding all changes to git...${NC}"
        git add .
        
        if ! git diff-index --quiet --cached HEAD --; then
            echo -e "${YELLOW}⚠️  You have staged changes that aren't committed!${NC}"
            echo "Staged files:"
            git diff --cached --name-only | sed 's/^/  /'
            echo ""
            read -p "Enter commit message (or press Enter for 'Quick update'): " commit_msg
            commit_msg=${commit_msg:-"Quick update"}
            
            echo -e "${BLUE}📋 Committing staged changes...${NC}"
            git commit -m "$commit_msg"
            echo -e "${GREEN}✅ Changes committed successfully${NC}"
        fi
    else
        echo -e "${RED}❌ Please commit your changes before updating${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Repository is clean and ready for update${NC}"

# Push to GitHub
echo -e "${BLUE}📋 Pushing latest changes to GitHub...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📋 Current branch: ${CURRENT_BRANCH}${NC}"

echo -e "${BLUE}📋 Fetching latest changes from remote...${NC}"
git fetch origin

# Check if we need to merge
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")

if [ "$REMOTE" != "" ]; then
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}✅ Already up to date with remote${NC}"
    elif [ "$LOCAL" = "$BASE" ]; then
        echo -e "${YELLOW}⚠️  Remote has changes. Pulling...${NC}"
        git pull origin "$CURRENT_BRANCH"
    elif [ "$REMOTE" = "$BASE" ]; then
        echo -e "${BLUE}📋 Local is ahead of remote, proceeding with push...${NC}"
    else
        echo -e "${YELLOW}⚠️  Branches have diverged. Attempting to merge...${NC}"
        git pull origin "$CURRENT_BRANCH"
    fi
fi

echo -e "${BLUE}📋 Pushing to origin/${CURRENT_BRANCH}...${NC}"
git push origin "$CURRENT_BRANCH"
echo -e "${GREEN}✅ Code pushed to GitHub successfully${NC}"

# Get latest commit info
LATEST_COMMIT=$(git rev-parse HEAD)
echo -e "${BLUE}📋 Latest commit: ${LATEST_COMMIT}${NC}"

# Test SSH connection
echo -e "${BLUE}📋 Testing SSH connection to server...${NC}"
if ! ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'SSH connection successful'"; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

echo -e "${BLUE}📋 Updating server: ${SERVER_HOST}${NC}"
echo -e "${BLUE}📋 Updating to commit: ${LATEST_COMMIT} on branch: ${CURRENT_BRANCH}${NC}"

# Create update script for server
cat > update_remote.sh << 'EOF'
#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting fast update on server...${NC}"

# Change to application directory
cd /opt/foi-archive

echo -e "${BLUE}📦 Updating code from GitHub...${NC}"
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📋 Current branch: ${CURRENT_BRANCH}${NC}"

# Store old commit for comparison
OLD_COMMIT=$(git rev-parse HEAD)

echo -e "${BLUE}🔄 Pulling latest changes...${NC}"
git reset --hard origin/"$CURRENT_BRANCH"
echo -e "${GREEN}✅ Repository updated to latest version${NC}"

NEW_COMMIT=$(git rev-parse HEAD)
echo -e "${BLUE}📋 Updated to commit: ${NEW_COMMIT}${NC}"

# Check what files changed
if [ "$OLD_COMMIT" != "$NEW_COMMIT" ]; then
    echo -e "${BLUE}📋 Files changed since last update:${NC}"
    git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT" | sed 's/^/  /'
    
    # Check if frontend files changed
    if git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT" | grep -q "^frontend/"; then
        echo -e "${BLUE}🏗️ Frontend files changed, rebuilding...${NC}"
        cd frontend
        echo -e "${BLUE}📦 Building frontend...${NC}"
        npm run build
        echo -e "${GREEN}✅ Frontend rebuilt successfully${NC}"
        cd ..
        FRONTEND_CHANGED=true
    else
        echo -e "${GREEN}✅ No frontend changes, skipping rebuild${NC}"
        FRONTEND_CHANGED=false
    fi
    
    # Check if backend files changed
    if git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT" | grep -q "^backend/"; then
        echo -e "${BLUE}🔄 Backend files changed, restarting service...${NC}"
        systemctl restart foi-archive
        echo -e "${GREEN}✅ Backend service restarted${NC}"
        BACKEND_CHANGED=true
    else
        echo -e "${GREEN}✅ No backend changes, service restart not needed${NC}"
        BACKEND_CHANGED=false
    fi
    
    # Update nginx if frontend changed
    if [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${BLUE}🔄 Reloading nginx...${NC}"
        nginx -t && nginx -s reload
        echo -e "${GREEN}✅ Nginx reloaded${NC}"
    fi
    
    # Wait a moment and check service status
    if [ "$BACKEND_CHANGED" = true ]; then
        echo -e "${BLUE}🔍 Checking service status...${NC}"
        sleep 2
        if systemctl is-active --quiet foi-archive; then
            echo -e "${GREEN}✅ Service is running${NC}"
        else
            echo -e "${RED}❌ Service failed to start${NC}"
            systemctl status foi-archive --no-pager
            exit 1
        fi
    fi
    
else
    echo -e "${GREEN}✅ No changes detected, nothing to update${NC}"
fi

echo -e "${BLUE}🔍 Testing application health...${NC}"
if curl -s -f http://localhost/api/health > /dev/null; then
    echo -e "${GREEN}✅ Application is healthy and responding${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed, but continuing...${NC}"
fi

echo -e "${GREEN}🎉 Fast update completed successfully!${NC}"
echo -e "${BLUE}📋 Application URL: http://${SERVER_HOST}${NC}"
EOF

# Copy update script to server and execute
echo -e "${BLUE}📋 Copying update script to server...${NC}"
scp update_remote.sh "$SERVER_USER@$SERVER_HOST":/tmp/
rm update_remote.sh

echo -e "${BLUE}📋 Executing fast update on server...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" "chmod +x /tmp/update_remote.sh && /tmp/update_remote.sh && rm /tmp/update_remote.sh"

echo ""
echo -e "${GREEN}🎉 Fast update completed successfully!${NC}"
echo -e "${BLUE}📋 Your application is available at: http://${SERVER_HOST}${NC}"
echo -e "${BLUE}📋 Updated to commit: ${LATEST_COMMIT}${NC}"
echo ""
echo -e "${YELLOW}💡 Use this script for quick iterations. Use ./deploy.sh for full deployments.${NC}" 