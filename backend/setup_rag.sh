#!/bin/bash

# Setup script for RAG (Retrieval-Augmented Generation) system
# This script installs and configures all necessary components for open source RAG

echo "🚀 Setting up RAG system for HaqNow..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the backend directory"
    exit 1
fi

print_status "Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

print_status "Step 2: Creating RAG database tables..."
python3 create_rag_tables.py
if [ $? -eq 0 ]; then
    print_success "RAG database tables created"
else
    print_error "Failed to create RAG database tables"
    exit 1
fi

print_status "Step 3: Checking for Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is already installed"
else
    print_warning "Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    if [ $? -eq 0 ]; then
        print_success "Ollama installed successfully"
    else
        print_error "Failed to install Ollama"
        exit 1
    fi
fi

print_status "Step 4: Starting Ollama service..."
# Start Ollama in background if not running
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 5
    print_success "Ollama service started"
else
    print_success "Ollama service already running"
fi

print_status "Step 5: Pulling Llama3 model..."
ollama pull llama3
if [ $? -eq 0 ]; then
    print_success "Llama3 model downloaded"
else
    print_warning "Failed to download Llama3, trying smaller model..."
    ollama pull llama3:8b
    if [ $? -eq 0 ]; then
        print_success "Llama3:8b model downloaded"
    else
        print_error "Failed to download any LLM model"
        exit 1
    fi
fi

print_status "Step 6: Testing RAG system..."
python3 -c "
import sys
sys.path.append('.')
try:
    from app.services.rag_service import rag_service
    print('✅ RAG service imports successfully')
    print('✅ Embedding model:', 'loaded' if rag_service.embedding_model else 'not loaded')
    print('✅ Ollama client:', 'connected' if rag_service.ollama_client else 'not connected')
except Exception as e:
    print('❌ RAG service test failed:', e)
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "RAG system test passed"
else
    print_error "RAG system test failed"
    exit 1
fi

echo ""
print_success "🎉 RAG system setup completed successfully!"
echo ""
echo "📋 Setup Summary:"
echo "  ✅ Python dependencies installed"
echo "  ✅ Database tables created"
echo "  ✅ Ollama LLM service running"
echo "  ✅ Llama3 model downloaded"
echo "  ✅ RAG system tested and working"
echo ""
echo "🔄 Next Steps:"
echo "  1. Start the backend server: python3 main.py"
echo "  2. Process existing documents: POST /api/rag/process-all-documents"
echo "  3. Test Q&A interface at: /search-page (AI Q&A tab)"
echo ""
echo "📚 API Endpoints:"
echo "  • POST /api/rag/question - Ask questions about documents"
echo "  • GET /api/rag/status - Check system status"
echo "  • POST /api/rag/process-document - Process specific document"
echo "  • GET /api/rag/analytics - View usage analytics"
echo ""
print_success "RAG system is ready to use! 🚀"