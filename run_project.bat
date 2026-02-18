@echo off
title RAG Project Runner

echo Starting Backend and Frontend...

:: Backend
start cmd /k "call env\Scripts\activate && cd be && python app.py"

:: Frontend
start cmd /k "cd fe && npm run dev"

exit
