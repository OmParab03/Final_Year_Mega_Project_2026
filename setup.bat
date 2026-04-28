@echo off

echo ==============================
echo Installing Backend...
echo ==============================

cd Backend
pip install -r requirements.txt

echo ==============================
echo Installing Frontend...
echo ==============================

cd ../Frontend

IF EXIST node_modules (
    echo Cleaning old node_modules...
    rmdir /s /q node_modules
)

IF EXIST package-lock.json (
    del package-lock.json
)

npm install

echo ==============================
echo Setup Complete!
echo ==============================

pause