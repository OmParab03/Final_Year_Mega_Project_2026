#!/bin/bash

echo "=============================="
echo "Installing backend requirements..."
echo "=============================="

cd Backend || exit
pip install -r requirements.txt

echo "=============================="
echo "Installing frontend packages..."
echo "=============================="

cd ../Frontend || exit

# Clean old installation (IMPORTANT)
if [ -d "node_modules" ]; then
  echo "Removing old node_modules..."
  rm -rf node_modules
fi

if [ -f "package-lock.json" ]; then
  echo "Removing old package-lock.json..."
  rm -f package-lock.json
fi

# Fresh install
npm install

echo "=============================="
echo "Setup complete!"
echo "=============================="