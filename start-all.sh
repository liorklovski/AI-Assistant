#!/bin/bash

# AI Chat Assistant MVP - Complete Application Startup Script

echo "🤖💬 Starting AI Chat Assistant MVP (Job-Based Architecture)"
echo "============================================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python; then
    echo "❌ Python is not installed. Please install Python 3.8+"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

echo "✅ All prerequisites are installed"

# Start FastAPI backend in background
echo "🚀 Starting FastAPI backend server..."
cd backend
chmod +x run.sh

./run.sh &
BACKEND_PID=$!

cd ..

# Wait for backend to start
echo "⏳ Waiting for FastAPI backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ FastAPI backend is running on http://localhost:5000"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start within 30 seconds"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done

# Start frontend
echo "🚀 Starting React frontend..."
cd frontend
chmod +x start.sh

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm start &
FRONTEND_PID=$!

cd ..

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Services stopped. Goodbye!"
    exit 0
}

# Set trap to catch Ctrl+C and cleanup
trap cleanup INT TERM

echo ""
echo "🎉 AI Chat Assistant MVP is running!"
echo "===================================="
echo "🔧 Backend (FastAPI): http://localhost:5000"
echo "🌐 Frontend (React):  http://localhost:3000"
echo "📚 API Documentation: http://localhost:5000/docs"
echo ""
echo "🔄 MVP Features:"
echo "   • Job-based asynchronous processing"
echo "   • Real-time polling for AI responses"
echo "   • Simulated AI with 3-second delay"
echo "   • In-memory job store"
echo "   • Status tracking: pending → processing → done"
echo ""
echo "📱 Open http://localhost:3000 to start chatting!"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interruption
wait
