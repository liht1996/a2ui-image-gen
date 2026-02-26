#!/bin/bash

# Run backend (server_new.py) + frontend-lit (Vite) together

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="10002"
FRONTEND_PORT="5173"

cd "$ROOT_DIR"

echo "🚀 Starting A2UI full stack..."
echo ""

if [ ! -d "venv" ]; then
  echo "❌ Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "❌ .env file not found. Create .env with GOOGLE_API_KEY or GEMINI_API_KEY."
  exit 1
fi

if [ ! -d "frontend-lit" ]; then
  echo "❌ frontend-lit directory not found."
  exit 1
fi

if [ ! -f "frontend-lit/package.json" ]; then
  echo "❌ frontend-lit/package.json not found."
  exit 1
fi

echo "🧹 Cleaning up existing processes on ports ${BACKEND_PORT}/${FRONTEND_PORT}..."
BACKEND_OLD_PID=$(lsof -ti tcp:${BACKEND_PORT} || true)
FRONTEND_OLD_PID=$(lsof -ti tcp:${FRONTEND_PORT} || true)

if [ -n "${BACKEND_OLD_PID}" ]; then
  kill ${BACKEND_OLD_PID} 2>/dev/null || true
fi
if [ -n "${FRONTEND_OLD_PID}" ]; then
  kill ${FRONTEND_OLD_PID} 2>/dev/null || true
fi

source venv/bin/activate
set -a
source .env
set +a

echo "🔧 Starting backend on http://localhost:${BACKEND_PORT} ..."
python server_new.py --host localhost --port ${BACKEND_PORT} > /tmp/a2ui-backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "❌ Backend failed to start. Check /tmp/a2ui-backend.log"
  exit 1
fi

echo "🌐 Starting frontend on http://localhost:${FRONTEND_PORT} ..."
cd "$ROOT_DIR/frontend-lit"
npm run dev -- --host localhost --port ${FRONTEND_PORT} > /tmp/a2ui-frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "❌ Frontend failed to start. Check /tmp/a2ui-frontend.log"
  kill "$BACKEND_PID" 2>/dev/null || true
  exit 1
fi

echo ""
echo "✅ Both services are running"
echo "📍 Backend : http://localhost:${BACKEND_PORT}"
echo "📍 Frontend: http://localhost:${FRONTEND_PORT}"
echo "📄 Backend log : /tmp/a2ui-backend.log"
echo "📄 Frontend log: /tmp/a2ui-frontend.log"
echo ""
echo "Press Ctrl+C to stop both"

cleanup() {
  echo ""
  echo "🛑 Stopping services..."
  kill "$BACKEND_PID" 2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  echo "👋 Stopped"
}

trap cleanup INT TERM
wait
