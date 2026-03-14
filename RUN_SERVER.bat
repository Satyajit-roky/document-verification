@echo off
REM ==========================================
REM AI Document Verification System - Launcher
REM ==========================================
REM This script ensures the Flask server is always running
REM It will start in a persistent window and keep running

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  AI Document Verification System - Server Launcher  ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Set up environment variables
set POPPLER_PATH=%~dp0poppler\poppler-24.08.0\Library\bin
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR
set PATH=%POPPLER_PATH%;%TESSERACT_PATH%;%PATH%

echo [✓] Environment configured:
echo    - Poppler: %POPPLER_PATH%
echo    - Tesseract: %TESSERACT_PATH%
echo.

REM Check if server is already running
echo [*] Checking if server is already running...
tasklist | findstr /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo [!] Python process found. Waiting 5 seconds before starting new server...
    timeout /t 5 /nobreak
)

REM Change to bbs directory
cd /d "%~dp0bbs"

REM Start the server with title and keep it persistent
echo [*] Starting Flask server...
echo [*] Server will be available at: http://127.0.0.1:5000
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Server running... Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python app.py

echo.
echo [*] Server stopped. Exiting...
pause
