#!/bin/bash

# =================================
# FOI Archive - Local Development
# =================================
# Runs the application locally with SQLite (no MySQL dependency)
# Avoids Python 3.13 compatibility issues

set -e  # Exit on any error

echo "🚀 Starting FOI Archive Local Development..."
echo "⚠️  Using simplified dependencies for Python 3.13 compatibility"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Using Python $PYTHON_VERSION"

# Navigate to backend directory
cd backend

# Create local .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating local .env file..."
    cat > .env << EOF
# Local Development Environment
ENVIRONMENT=development
DEBUG=True

# Database (SQLite for local development)
DATABASE_URL=sqlite:///./local_foi_archive.db

# JWT Settings
JWT_SECRET_KEY=local-development-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin User (for local development)
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123

# File Storage (local directory)
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=50000000

# SendGrid (disabled for local)
SENDGRID_API_KEY=disabled-for-local-development
FROM_EMAIL=noreply@localhost

# AWS S3 (disabled for local)
AWS_ACCESS_KEY_ID=disabled
AWS_SECRET_ACCESS_KEY=disabled
AWS_BUCKET_NAME=local-bucket
AWS_REGION=us-east-1

# Redis (disabled for local)
REDIS_URL=redis://localhost:6379/0
ENABLE_RATE_LIMITING=false
EOF
    print_status "Created .env file with local development settings"
else
    print_status "Using existing .env file"
fi

# Create minimal requirements for local development
print_status "Creating minimal local requirements..."
cat > requirements-minimal.txt << EOF
# Minimal requirements for local development (Python 3.13 compatible)

# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Database (SQLite only)
sqlalchemy==2.0.23
alembic==1.13.1

# HTTP & API
httpx==0.25.2
requests==2.31.0
pydantic==2.5.1
pydantic-settings==2.1.0

# File handling (basic)
python-multipart==0.0.6

# Basic document processing (no image dependencies)
PyPDF2==3.0.1
python-docx==1.1.0

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0
python-dateutil==2.8.2
pytz==2023.3

# Development
ipython
EOF

# Check if uv is available, otherwise use pip
if command -v uv &> /dev/null; then
    print_status "Installing dependencies with uv..."
    uv venv .venv --python python3 || print_warning "Virtual environment already exists"
    source .venv/bin/activate
    uv pip install -r requirements-minimal.txt
else
    print_status "Installing dependencies with pip..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-minimal.txt
fi

print_status "Dependencies installed successfully"

# Initialize database
print_status "Setting up database..."
if [ ! -f "local_foi_archive.db" ]; then
    print_status "Creating database tables..."
    python -c "
from app.auth.user import init_db
init_db()
print('Database initialized successfully')
"
    print_status "Database created and initialized"
else
    print_status "Database already exists"
fi

# Create uploads directory
mkdir -p uploads
print_status "Upload directory ready"

# Start the application
print_status "Starting FOI Archive server..."
print_warning "Access the application at: http://localhost:8000"
print_warning "API documentation at: http://localhost:8000/docs"
print_warning "Press Ctrl+C to stop the server"

echo ""
echo "==================================="
echo "🏃 Server starting on port 8000..."
echo "==================================="

# Start with auto-reload for development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    deactivate 2>/dev/null || true
}

trap cleanup EXIT 