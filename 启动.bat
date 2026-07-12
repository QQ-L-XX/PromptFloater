@echo off
title PromptFloater
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"
set "PYTHONW=.venv\Scripts\pythonw.exe"

:: Create an isolated environment on first launch.
if not exist "%PYTHON%" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo Python 3.8+ is required: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

"%PYTHON%" -c "import webview, pyperclip" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

start "" "%PYTHONW%" app.py
exit /b 0
