#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill 0
  wait
}

trap cleanup SIGINT SIGTERM

echo "Starting backend..."
(cd "$ROOT_DIR/backend" && source .venv/bin/activate && uvicorn main:app --reload) &

echo "Starting frontend..."
(cd "$ROOT_DIR/frontend" && npm run dev) &

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

wait
