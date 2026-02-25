#!/bin/bash

# Quick restart script for debugging

echo "🛑 Stopping existing servers..."
pkill -f "python.*server.py" 2>/dev/null
pkill -f "python.*serve_frontend.py" 2>/dev/null
sleep 1

echo "🚀 Starting servers with updated code..."

# Start backend
cd /Users/haotian.li/Repositories/a2ui-image-gen
venv/bin/python server.py &
BACKEND_PID=$!

sleep 2

# Start frontend 
python3 serve_frontend.py &
FRONTEND_PID=$!

echo "✅ Servers restarted!"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "View backend logs to debug:"
echo "  Backend: http://localhost:10002"
echo "  Frontend: http://localhost:8080"
echo ""
echo "To test:"
echo "  1. Open http://localhost:8080"
echo "  2. Open browser console (F12)"
echo "  3. Generate an image"
echo "  4. Use sketch board and click Apply"
echo "  5. Check console for debug logs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" INT
wait
