@echo off
title RFP Agent Suite
cd /d "%~dp0"
python desktop_app.py
if errorlevel 1 (
    echo.
    echo Failed to start. Make sure Python is installed and in PATH.
    echo Install dependencies: pip install PyPDF2 python-pptx
    pause
)
