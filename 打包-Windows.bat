@echo off
setlocal
title Build PromptFloater
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"

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

"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

if exist build rmdir /s /q build
taskkill /f /im PromptFloater.exe >nul 2>&1
if exist dist rmdir /s /q dist
if not exist release mkdir release

"%PYTHON%" -m PyInstaller --clean --noconfirm packaging\PromptFloater.spec
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

if exist release\PromptFloater-Windows.zip del /q release\PromptFloater-Windows.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\PromptFloater\*' -DestinationPath 'release\PromptFloater-Windows.zip' -Force"
if errorlevel 1 (
    echo Zip packaging failed.
    pause
    exit /b 1
)

echo.
echo Build complete:
echo   dist\PromptFloater\PromptFloater.exe
echo   release\PromptFloater-Windows.zip
echo.
pause
