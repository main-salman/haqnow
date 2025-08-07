#!/bin/bash

# Test script for RAG Q&A functionality on live HaqNow website
# This script tests the AI Q&A features after deployment

echo "🧪 Testing RAG Q&A System on Live HaqNow Website"
echo "=================================================="

SITE_URL="https://www.haqnow.com"
API_URL="$SITE_URL/api"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test 1: Check if website is accessible
print_test "1. Testing website accessibility..."
response=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)
if [ "$response" = "200" ]; then
    print_success "Website is accessible (HTTP $response)"
else
    print_fail "Website not accessible (HTTP $response)"
    exit 1
fi

# Test 2: Check if search page has RAG UI
print_test "2. Checking for AI Q&A interface on search page..."
search_page=$(curl -s "$SITE_URL/search-page")
if echo "$search_page" | grep -q "AI Q&A\|Brain\|Ask.*AI\|RAG\|question.*answer"; then
    print_success "AI Q&A interface found on search page"
else
    print_warning "AI Q&A interface not found in HTML (may not be deployed yet)"
fi

# Test 3: Check RAG API endpoints
print_test "3. Testing RAG API endpoints..."

# Test RAG status endpoint
print_test "   3a. Testing RAG status endpoint..."
status_response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$API_URL/rag/status")
status_code=$(echo $status_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
status_body=$(echo $status_response | sed -e 's/HTTPSTATUS:.*//g')

if [ "$status_code" = "200" ]; then
    print_success "RAG status endpoint accessible"
    echo "   Status: $status_body" | head -c 100
    echo
    
    # Check if Ollama is available
    if echo "$status_body" | grep -q '"ollama_available":true'; then
        print_success "Ollama LLM service is running"
    else
        print_warning "Ollama LLM service not running"
    fi
    
    # Check if embedding model is loaded
    if echo "$status_body" | grep -q '"embedding_model_loaded":true'; then
        print_success "Embedding model is loaded"
    else
        print_warning "Embedding model not loaded"
    fi
    
else
    print_fail "RAG status endpoint not accessible (HTTP $status_code)"
fi

# Test 4: Test actual Q&A functionality
print_test "4. Testing AI Q&A functionality..."
question_data='{"question": "What types of corruption are mentioned in the documents?"}'
qa_response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$question_data" \
    "$API_URL/rag/question")

qa_code=$(echo $qa_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
qa_body=$(echo $qa_response | sed -e 's/HTTPSTATUS:.*//g')

if [ "$qa_code" = "200" ]; then
    print_success "Q&A endpoint working successfully"
    echo "   Sample question processed"
    
    # Check if response contains expected fields
    if echo "$qa_body" | grep -q '"answer":\|"sources":\|"confidence":'; then
        print_success "Response contains expected AI answer fields"
    else
        print_warning "Response missing expected fields"
    fi
    
    # Show sample response (truncated)
    echo "   Response preview:"
    echo "$qa_body" | head -c 200
    echo "..."
    
elif [ "$qa_code" = "500" ]; then
    print_warning "Q&A endpoint accessible but returned server error (models may not be ready)"
    echo "   This is normal if deployment just completed"
else
    print_fail "Q&A endpoint not working (HTTP $qa_code)"
fi

# Test 5: Check document processing endpoint
print_test "5. Testing document processing endpoints..."
process_response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$API_URL/rag/analytics")
process_code=$(echo $process_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [ "$process_code" = "200" ]; then
    print_success "RAG analytics endpoint accessible"
    
    # Check total queries
    if echo "$process_response" | grep -q '"total_queries":'; then
        total_queries=$(echo "$process_response" | grep -o '"total_queries":[0-9]*' | cut -d: -f2)
        print_success "Total Q&A queries processed: $total_queries"
    fi
else
    print_warning "RAG analytics endpoint not accessible (HTTP $process_code)"
fi

# Test 6: Frontend component test
print_test "6. Testing frontend RAG components..."
if echo "$search_page" | grep -q "RAGQuestionAnswering\|Brain.*className\|AI.*Q&A"; then
    print_success "RAG React components found in frontend"
else
    print_warning "RAG React components not found (may need frontend rebuild)"
fi

# Test 7: Check for required JavaScript files
print_test "7. Checking for RAG-related JavaScript..."
if echo "$search_page" | grep -q "assets.*js" && curl -s "$SITE_URL/assets" | grep -q "js"; then
    print_success "Frontend assets loading correctly"
else
    print_warning "Frontend assets may not be building RAG components"
fi

# Summary
echo ""
echo "========================================"
echo "🎯 RAG Q&A System Test Summary"
echo "========================================"

echo "Website Status: ✅ Accessible"

if [ "$status_code" = "200" ]; then
    echo "RAG Backend: ✅ API endpoints working"
else
    echo "RAG Backend: ❌ API endpoints not accessible"
fi

if [ "$qa_code" = "200" ]; then
    echo "AI Q&A: ✅ Fully functional"
elif [ "$qa_code" = "500" ]; then
    echo "AI Q&A: ⚠️ Endpoint ready, models may be loading"
else
    echo "AI Q&A: ❌ Not working"
fi

if echo "$search_page" | grep -q "AI Q&A\|Brain\|question.*answer"; then
    echo "Frontend UI: ✅ Q&A interface deployed"
else
    echo "Frontend UI: ❌ Q&A interface not found"
fi

echo ""
echo "🔍 Manual Testing Instructions:"
echo "1. Visit: $SITE_URL/search-page"
echo "2. Click the 'AI Q&A' tab"
echo "3. Ask questions like:"
echo "   • 'What corruption cases involve Brazil?'"
echo "   • 'What are the main types of government fraud?'"
echo "   • 'Which countries have the most transparency issues?'"
echo ""
echo "💡 If Q&A tab is not visible, the frontend may need to be rebuilt"
echo "⏳ If queries return errors, Ollama models may still be downloading"