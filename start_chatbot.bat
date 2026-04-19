@echo off
title SBI Mutual Fund AI Assistant - Launcher
cls
echo ============================================================
echo   SBI Mutual Fund FAQ Assistant - Implementation Phase 5
echo ============================================================
echo.
echo NOTE: If you don't have an API key yet, you can just press 
echo ENTER to continue in MOCK MODE for UI testing.
echo.
set /p OPENAI_KEY="Paste your OpenAI API Key (sk-...) and press ENTER: "

if "%OPENAI_KEY%"=="" (
    echo.
    echo [INFO] No key provided. Starting in MOCK MODE...
    python api/server.py
) else (
    echo.
    echo [INFO] API Key set. Starting RAG Engine...
    set OPENAI_API_KEY=%OPENAI_KEY%
    python api/server.py
)

pause
