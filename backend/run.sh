#!/bin/bash

# AI Chat Assistant MVP - Backend Startup Script

echo "🤖 Starting AI Chat Assistant MVP Backend (FastAPI)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create basic .env file if it doesn't exist (optional for MVP)
if [ ! -f ".env" ]; then
    echo "📝 Creating basic .env file..."
    cat > .env << EOL
ENVIRONMENT=development
DEBUG=True
EOL
    echo "✅ Basic configuration created"
fi

# Start FastAPI server with uvicorn
echo "🚀 Starting FastAPI server with uvicorn..."
echo "🌐 Backend will be available at: http://localhost:5000"
echo "📊 Health check: http://localhost:5000/health"
echo "📚 API docs: http://localhost:5000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

python3 main.py
