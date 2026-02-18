@echo off
title RAG Project Setup

echo ================================
echo Creating Python Virtual Environment
echo ================================
python -m venv env

echo.
echo Activating Environment
call env\Scripts\activate

echo.
echo Installing Backend Requirements
cd be
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Installing Frontend Requirements
cd ..\fe
npm install

cd ..

echo.
echo ====================================
echo Setup Complete. Starting Servers...
echo ====================================

:: Start Backend in new terminal
start cmd /k "call env\Scripts\activate && cd be && python app.py"

:: Start Frontend in new terminal
start cmd /k "cd fe && npm run dev"

pause
