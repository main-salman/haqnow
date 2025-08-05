#!/bin/bash
# Quick database performance testing script

echo "🚀 HaqNow.com RAG Database Performance Test"
echo "============================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "backend/quick_perf_test.py" ]]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo "📋 This test will measure:"
echo "   • Network latency to PostgreSQL RAG database"
echo "   • Vector search query performance"
echo "   • Database connection overhead"
echo ""
echo "⏱️  Estimated time: 30-60 seconds"
echo ""

read -p "Press Enter to start the test..."
echo ""

# Change to backend directory and run the test
cd backend

echo "🔧 Setting up environment..."
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  Warning: No .env file found in backend directory"
fi

echo ""
echo "🚀 Running performance test..."
echo ""

# Run the quick performance test
python3 quick_perf_test.py

echo ""
echo "✅ Performance test completed!"
echo ""
echo "🔍 For detailed analysis, run:"
echo "   cd backend && python3 test_performance.py"
echo ""

# Return to original directory
cd ..