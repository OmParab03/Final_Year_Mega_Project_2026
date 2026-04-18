#!/bin/bash

echo "=============================="
echo "Installing backend..."
echo "=============================="

cd Backend || exit
pip install -r requirements.txt

echo "=============================="
echo "Starting backend..."
echo "=============================="

# Run backend in background
python app.py &

echo "=============================="
echo "Installing frontend..."
echo "=============================="

cd ../Frontend || exit

# Clean install
rm -rf node_modules package-lock.json
npm install

echo "=============================="
echo "Starting frontend..."
echo "=============================="

ng serve