#!/bin/bash

# Run both backend and frontend servers

echo "🚀 Starting A2UI Image Generation servers..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your GOOGLE_API_KEY"
    exit 1
fi

# Start backend in background
echo "🔧 Starting backend server on port 10002..."
venv/bin/python server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🌐 Starting frontend server on port 8080..."
python3 serve_frontend.py &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo ""
echo "📍 Backend:  http://localhost:10002"
echo "📍 Frontend: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '👋 Servers stopped'; exit" INT

# Keep script running
wait
