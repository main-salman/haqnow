#!/bin/bash

# Comprehensive deployment script for HaqNow.com
# Usage: ./deploy.sh [patch|minor|major]
# Default: patch

set -e  # Exit on any error

VERSION_TYPE=${1:-patch}

echo "🚀 Starting HaqNow.com deployment process..."
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

# Step 4: Deploy to production server
echo "🌐 Deploying to production server..."
ssh root@159.100.250.145 << EOF
echo "=== Deploying HaqNow.com v$NEW_VERSION ==="

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

# Run privacy migration if needed
echo "🔒 Running privacy migration (IP address removal)..."
source .venv/bin/activate && python run_migration.py || echo "Migration already applied or not needed"

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

echo ""
echo "✅ HaqNow.com v$NEW_VERSION deployed successfully!"
echo "🔒 Privacy-compliant with complete IP address removal"
echo "🌍 Visit: http://159.100.250.145"
echo "📊 Admin: http://159.100.250.145/admin-login-page"
EOF

if [ $? -ne 0 ]; then
    echo "❌ Production deployment failed!"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📱 Frontend: http://159.100.250.145"
echo "📋 Version: $NEW_VERSION displayed in footer"
echo "🔧 Admin Panel: http://159.100.250.145/admin-login-page"
echo ""
echo "Next deployment: ./deploy.sh [patch|minor|major]" 