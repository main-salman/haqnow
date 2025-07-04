#!/bin/bash

# =================================
# FOI Archive - Local Development Script
# =================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check Python version compatibility
check_python_version() {
    log "Checking Python version compatibility..."
    
    python_version=$(python3 --version 2>&1 | cut -d" " -f2)
    python_major=$(echo $python_version | cut -d"." -f1)
    python_minor=$(echo $python_version | cut -d"." -f2)
    
    if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 8 ]; then
        success "Python $python_version is compatible"
    else
        error "Python $python_version is not compatible. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Warn about Python 3.13 issues
    if [ "$python_major" -eq 3 ] && [ "$python_minor" -eq 13 ]; then
        warning "Python 3.13 detected. Some packages may have build issues."
        warning "Consider using Python 3.11 or 3.12 for better compatibility."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Please install Python 3.11 or 3.12 for optimal compatibility"
            exit 1
        fi
    fi
}

# Setup environment
setup_environment() {
    log "Setting up local environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            success "Created .env file from example"
            warning "Please configure your .env file with appropriate values"
        else
            error ".env.example file not found"
            exit 1
        fi
    fi
    
    # Check if MySQL is configured
    if grep -q "mysql" .env 2>/dev/null; then
        warning "MySQL configuration detected in .env"
        log "Local development will use SQLite instead"
    fi
}

# Setup Python backend
setup_backend() {
    log "Setting up Python backend..."
    
    cd backend
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        success "UV installed successfully"
    fi
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        log "Creating Python virtual environment..."
        uv venv --python python3
        success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies with fallback
    log "Installing Python dependencies (local development mode)..."
    
    if uv pip install -r requirements-local.txt; then
        success "Python dependencies installed successfully"
    else
        warning "UV installation failed. Trying with pip..."
        pip install -r requirements-local.txt
        success "Python dependencies installed with pip"
    fi
    
    cd ..
}

# Setup Node.js frontend
setup_frontend() {
    log "Setting up Node.js frontend..."
    
    cd frontend
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        echo "Please install Node.js 18+ from: https://nodejs.org/"
        exit 1
    fi
    
    # Check Node.js version
    node_version=$(node --version | cut -d"v" -f2)
    node_major=$(echo $node_version | cut -d"." -f1)
    
    if [ "$node_major" -lt 18 ]; then
        error "Node.js version $node_version is too old. Please install Node.js 18+"
        exit 1
    fi
    
    success "Node.js $node_version is compatible"
    
    # Install dependencies
    log "Installing Node.js dependencies..."
    
    # Try yarn first, fallback to npm
    if command -v yarn &> /dev/null; then
        yarn install
        success "Frontend dependencies installed with Yarn"
    else
        npm install
        success "Frontend dependencies installed with NPM"
    fi
    
    cd ..
}

# Start development servers
start_servers() {
    log "Starting development servers..."
    
    # Create log directory
    mkdir -p logs
    
    # Start backend server
    log "Starting Python backend server..."
    cd backend
    source .venv/bin/activate
    
    # Set environment for local development
    export DATABASE_URL="sqlite:///./foi_archive_local.db"
    export ENVIRONMENT="development"
    
    # Start backend in background
    nohup python main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Check if backend is running
    if ps -p $BACKEND_PID > /dev/null; then
        success "Backend server started (PID: $BACKEND_PID)"
        log "Backend logs: tail -f logs/backend.log"
    else
        error "Backend server failed to start"
        log "Check logs: cat logs/backend.log"
        exit 1
    fi
    
    # Start frontend server
    log "Starting Node.js frontend server..."
    cd frontend
    
    # Start frontend in background  
    if command -v yarn &> /dev/null; then
        nohup yarn dev > ../logs/frontend.log 2>&1 &
    else
        nohup npm run dev > ../logs/frontend.log 2>&1 &
    fi
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    cd ..
    
    # Wait for frontend to start
    sleep 5
    
    # Check if frontend is running
    if ps -p $FRONTEND_PID > /dev/null; then
        success "Frontend server started (PID: $FRONTEND_PID)"
        log "Frontend logs: tail -f logs/frontend.log"
    else
        error "Frontend server failed to start"
        log "Check logs: cat logs/frontend.log"
        exit 1
    fi
}

# Show development info
show_dev_info() {
    echo
    success "🎉 FOI Archive Local Development Started!"
    echo
    log "📊 Service Information:"
    echo "• Frontend: http://localhost:5173"
    echo "• Backend API: http://localhost:8000"
    echo "• API Documentation: http://localhost:8000/docs"
    echo "• Database: SQLite (local file)"
    echo
    log "📋 Development Commands:"
    echo "• View backend logs: tail -f logs/backend.log"
    echo "• View frontend logs: tail -f logs/frontend.log"
    echo "• Stop servers: ./stop-local.sh"
    echo "• Update dependencies: ./update-local.sh"
    echo
    log "🔧 Troubleshooting:"
    echo "• Backend not starting? Check: cat logs/backend.log"
    echo "• Frontend issues? Check: cat logs/frontend.log"
    echo "• Port conflicts? Check processes: lsof -i :8000 -i :5173"
}

# Create stop script
create_stop_script() {
    cat << 'STOP_SCRIPT' > stop-local.sh
#!/bin/bash

echo "🛑 Stopping FOI Archive local development..."

# Stop backend
if [ -f "logs/backend.pid" ]; then
    backend_pid=$(cat logs/backend.pid)
    if ps -p $backend_pid > /dev/null; then
        kill $backend_pid
        echo "✅ Backend server stopped"
    fi
    rm -f logs/backend.pid
fi

# Stop frontend  
if [ -f "logs/frontend.pid" ]; then
    frontend_pid=$(cat logs/frontend.pid)
    if ps -p $frontend_pid > /dev/null; then
        kill $frontend_pid
        echo "✅ Frontend server stopped"
    fi
    rm -f logs/frontend.pid
fi

echo "🎉 All servers stopped"
STOP_SCRIPT

    chmod +x stop-local.sh
    success "Created stop-local.sh script"
}

# Main execution
main() {
    echo -e "${BLUE}🚀 FOI Archive - Local Development Setup${NC}"
    echo "========================================"
    echo
    
    check_python_version
    setup_environment
    warning "MySQL not configured, using SQLite for local development"
    log "Installing dependencies..."
    setup_backend
    setup_frontend
    create_stop_script
    start_servers
    show_dev_info
    
    log "Press Ctrl+C to stop all servers, or run: ./stop-local.sh"
    
    # Keep script running
    while true; do
        sleep 60
    done
}

# Handle Ctrl+C gracefully
trap 'echo; log "Stopping servers..."; ./stop-local.sh; exit 0' INT

# Run main function
main "$@" 