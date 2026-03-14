@echo off
REM AI Document Verification System - Startup Script
REM This script ensures proper PATH configuration and starts the Flask server

echo Starting AI Document Verification System...
echo.

REM Set paths for required binaries
set POPPLER_PATH=%~dp0poppler\poppler-24.08.0\Library\bin
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR

REM Add to PATH
set PATH=%POPPLER_PATH%;%TESSERACT_PATH%;%PATH%

echo Environment configured:
echo - Poppler path: %POPPLER_PATH%
echo - Tesseract path: %TESSERACT_PATH%
echo.

REM Change to bbs directory
cd bbs

REM Start the Flask server
echo Starting Flask server on http://127.0.0.1:5000
python app.py

pause