#!/bin/bash

# AI Chat Assistant - Test Runner Script

echo "🧪 AI Chat Assistant Test Suite"
echo "================================="

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if not already installed
echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx

echo ""
echo "🚀 Running Test Suite..."
echo ""

# Run different test categories
echo "🧪 Unit Tests:"
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "🔗 Integration Tests:"
python -m pytest tests/integration/ -v --tb=short

echo ""
echo "📊 Test Summary:"
python -m pytest tests/ --tb=no -q

echo ""
echo "✅ Testing Complete!"
echo ""
echo "📝 To run specific test categories:"
echo "   Unit only:        python -m pytest tests/unit/"
echo "   Integration only:  python -m pytest tests/integration/"
echo "   Fast tests only:   python -m pytest tests/ -m 'not slow'"
echo "   AI tests only:     python -m pytest tests/ -m 'ai'"
