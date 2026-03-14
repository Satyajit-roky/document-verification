@echo off
echo ========================================
echo  AI DOCUMENT VERIFICATION SYSTEM
echo ========================================
echo.

echo Setting up Poppler PATH...
set POPPLER_PATH=%~dp0poppler\poppler-24.08.0\Library\bin
set PATH=%POPPLER_PATH%;%PATH%

echo.
echo Testing Poppler...
pdfinfo -v >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Poppler is working
) else (
    echo ✗ Poppler not found in PATH
    echo Please ensure poppler binaries are in: %POPPLER_PATH%
    pause
    exit /b 1
)

echo.
echo Starting Flask server...
cd bbs
python app.py