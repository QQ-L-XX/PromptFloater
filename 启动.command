#!/bin/bash
# PromptFloater — macOS launcher (double-click in Finder)

cd "$(dirname "$0")"
PYTHON=".venv/bin/python3"

if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 not found.\nPlease install Python 3.8+ from python.org or brew." buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

if [ ! -x "$PYTHON" ]; then
    python3 -m venv .venv || exit 1
fi

if ! "$PYTHON" -c "import webview, pyperclip" 2>/dev/null; then
    echo "Installing dependencies..."
    "$PYTHON" -m pip install -r requirements.txt || exit 1
fi

nohup "$PYTHON" app.py > /dev/null 2>&1 &
