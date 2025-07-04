#!/bin/bash

# FOI Archive - Local Development Script
# This script runs the application locally connecting to Exoscale MySQL and object storage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting FOI Archive Local Development...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create a .env file with your Exoscale credentials."
    echo "See .env.example for reference."
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables for S3 (MySQL can be local for development)
required_vars=("EXOSCALE_S3_ACCESS_KEY" "EXOSCALE_S3_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: $var is not set in .env file${NC}"
        exit 1
    fi
done

# For local development, use SQLite if MySQL not configured
if [ -z "$MYSQL_HOST" ]; then
    echo -e "${YELLOW}⚠️  MySQL not configured, using SQLite for local development${NC}"
    export DATABASE_URL="sqlite:///./foi_local.db"
fi

echo -e "${YELLOW}📦 Installing dependencies...${NC}"

# Install backend dependencies
echo "Installing Python dependencies..."
cd backend

# Setup Python environment
if command -v uv &> /dev/null; then
    echo "Setting up uv environment..."
    if [ ! -d ".venv" ]; then
        uv venv
    fi
    source .venv/bin/activate
    echo "Installing local development dependencies (no MySQL)..."
    uv pip install -r requirements-local.txt
elif command -v pip &> /dev/null; then
    echo "Using pip..."
    echo "Installing local development dependencies (no MySQL)..."
    pip install -r requirements-local.txt --break-system-packages 2>/dev/null || pip install -r requirements-local.txt
else
    echo -e "${RED}❌ Error: Neither uv nor pip found. Please install Python package manager.${NC}"
    exit 1
fi

# Download spaCy model if not already installed
echo "Checking spaCy model..."
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo "Downloading spaCy model..."
    python -m spacy download en_core_web_sm
}

# Install frontend dependencies
echo "Installing Node.js dependencies..."
cd ../frontend
if command -v yarn &> /dev/null; then
    yarn install
elif command -v npm &> /dev/null; then
    npm install
else
    echo -e "${RED}❌ Error: Neither yarn nor npm found. Please install Node.js package manager.${NC}"
    exit 1
fi

cd ..

echo -e "${YELLOW}🗄️ Setting up database...${NC}"

# Initialize database (create tables)
cd backend
python -c "
from app.database.database import init_db
try:
    init_db()
    print('✅ Database tables created successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

cd ..

echo -e "${YELLOW}🔧 Starting services...${NC}"

# Check if Redis is available for rate limiting
if command -v redis-server &> /dev/null; then
    echo "Starting Redis for rate limiting..."
    redis-server --daemonize yes --port 6379 2>/dev/null || echo "Redis already running or failed to start"
else
    echo "⚠️ Redis not found. Rate limiting will use in-memory storage."
fi

echo -e "${GREEN}🎯 Starting application servers...${NC}"

# Start backend server in background
echo "Starting backend server on http://localhost:8000..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend development server
echo "Starting frontend server on http://localhost:5173..."
cd frontend

# Kill any existing processes on port 5173
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

if command -v yarn &> /dev/null; then
    yarn dev --host 0.0.0.0 &
else
    npm run dev -- --host 0.0.0.0 &
fi
FRONTEND_PID=$!
cd ..

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    # Kill any remaining processes on our ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}✅ FOI Archive is now running!${NC}"
echo ""
echo -e "${YELLOW}📱 Access your application:${NC}"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo -e "${YELLOW}🔧 Database Connection:${NC}"
echo "  Host: $MYSQL_HOST"
echo "  Database: $MYSQL_DATABASE"
echo ""
echo -e "${YELLOW}📦 Object Storage:${NC}"
echo "  Endpoint: $EXOSCALE_S3_ENDPOINT"
echo "  Bucket: $EXOSCALE_BUCKET"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"

# Wait for user to interrupt
wait 