#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# ToxiScan — single run script (Backend + Frontend)
# Usage: bash run.sh  (from repo root)
# ─────────────────────────────────────────────────────────────

REPO_ROOT="$(pwd)"

echo "=============================="
echo "🚀 Starting ToxiScan (Backend + Frontend)"
echo "=============================="

# ── BACKEND ───────────────────────────────────────────────────
echo "➡️  Setting up backend..."
cd "$REPO_ROOT/Backend"

# Create venv if missing (Windows Git Bash / Linux / macOS)
if [ ! -d "venv" ]; then
  echo "   Creating Python virtual environment..."
  python -m venv venv
fi

# Activate venv
# shellcheck disable=SC1091
if [ -f "venv/Scripts/activate" ]; then
  # Windows Git Bash
  source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
  # Linux / macOS
  source venv/bin/activate
else
  echo "❌ Could not find venv activation script."
  exit 1
fi

echo "   Installing backend dependencies..."
pip install -r requirements.txt

echo "   Starting Flask backend on http://127.0.0.1:5000 ..."
python app.py &
BACKEND_PID=$!

# Give backend a moment to boot (optional but nice)
sleep 2

# ── FRONTEND ──────────────────────────────────────────────────
echo "➡️  Setting up frontend..."
cd "$REPO_ROOT/Frontend"

if [ ! -d "node_modules" ]; then
  echo "   node_modules not found. Installing npm packages..."
  npm install
else
  echo "   node_modules exists. Skipping npm install."
fi

echo "   Starting Angular frontend on http://localhost:4200 ..."
npx ng serve --open &   # --open opens browser automatically
FRONTEND_PID=$!

# ── CLEANUP ON EXIT ───────────────────────────────────────────
cleanup() {
  echo
  echo "🛑 Shutting down..."
  kill "$FRONTEND_PID" 2>/dev/null || true
  kill "$BACKEND_PID"  2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID"  2>/dev/null || true
  echo "✅ Done."
}
trap cleanup INT TERM EXIT

# Keep script alive while both run
wait "$FRONTEND_PID"
wait "$BACKEND_PID"