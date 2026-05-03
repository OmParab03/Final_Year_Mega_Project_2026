#!/bin/bash

echo "=============================="
echo "Setting up backend..."
echo "=============================="

cd Backend || exit

# Create venv if not exists
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python -m venv venv
fi

# Activate venv (Windows Git Bash)
source venv/Scripts/activate

echo "Checking backend dependencies..."
pip install -r requirements.txt

echo "=============================="
echo "Starting backend..."
echo "=============================="

python app.py &

echo "=============================="
echo "Setting up frontend..."
echo "=============================="

cd ../Frontend || exit

if [ ! -d "node_modules" ]; then
  echo "node_modules not found. Installing..."
  npm install
else
  echo "node_modules already exists. Skipping install."
fi

echo "=============================="
echo "Starting frontend..."
echo "=============================="

ng serve