#!/bin/bash

# FOI Archive - Local Update Script
# This script updates the local development environment after code changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Updating FOI Archive Local Development...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create a .env file with your Exoscale credentials."
    exit 1
fi

echo -e "${YELLOW}📦 Updating dependencies...${NC}"

# Update backend dependencies
echo "Updating Python dependencies..."
cd backend
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt --upgrade
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt --upgrade
else
    echo -e "${RED}❌ Error: Neither uv nor pip found.${NC}"
    exit 1
fi

# Update frontend dependencies
echo "Updating Node.js dependencies..."
cd ../frontend
if command -v yarn &> /dev/null; then
    yarn install
elif command -v npm &> /dev/null; then
    npm install
else
    echo -e "${RED}❌ Error: Neither yarn nor npm found.${NC}"
    exit 1
fi

cd ..

echo -e "${YELLOW}🗄️ Updating database schema...${NC}"

# Update database schema (create new tables if any)
cd backend
python -c "
from app.database.database import init_db
try:
    init_db()
    print('✅ Database schema updated successfully')
except Exception as e:
    print(f'❌ Database update failed: {e}')
    exit(1)
"

cd ..

echo -e "${YELLOW}🔄 Restarting services...${NC}"

# Kill existing processes
echo "Stopping existing processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "yarn dev\|npm run dev" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Wait a moment
sleep 2

echo -e "${GREEN}🚀 Starting updated services...${NC}"

# Start backend server in background
echo "Starting updated backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend development server
echo "Starting updated frontend server..."
cd frontend

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
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}✅ FOI Archive updated and running!${NC}"
echo ""
echo -e "${YELLOW}📱 Access your application:${NC}"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"

# Wait for user to interrupt
wait 