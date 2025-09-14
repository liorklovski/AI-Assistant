#!/bin/bash

# AI Chat Assistant MVP - Frontend Startup Script

echo "💬 Starting AI Chat Assistant MVP Frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Check if backend is running
echo "🔍 Checking if FastAPI backend is running..."
if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "⚠️  FastAPI backend is not running!"
    echo "🚀 Please start the backend first:"
    echo "   cd ../backend && ./run.sh"
    echo ""
    echo "💡 Or run both services with: ./start-all.sh from project root"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ FastAPI backend is running"
fi

# Start React development server
echo "🚀 Starting React development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Backend API: http://localhost:5000"
echo "📚 API docs: http://localhost:5000/docs"
echo ""
echo "🔄 MVP Features: Job-based async processing with polling"
echo "📊 Watch job status: pending → processing → done"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

npm start
