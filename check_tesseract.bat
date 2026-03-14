@echo off
echo ========================================
echo  TESSERACT OCR INSTALLATION CHECK
echo ========================================
echo.

echo Checking if Tesseract is installed...
tesseract --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ TESSERACT IS INSTALLED!
    echo.
    tesseract --version
    echo.
    echo Your AI Document Verification System can now process:
    echo - Text-based PDFs
    echo - Image-based/scanned PDFs
    echo - All image formats (JPG, PNG, etc.)
    echo.
    echo Ready to start the server!
) else (
    echo ✗ TESSERACT NOT FOUND
    echo.
    echo Please install Tesseract OCR first:
    echo.
    echo DOWNLOAD OPTIONS:
    echo 1. https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.4.20240514/tesseract-ocr-w64-setup-5.3.4.20240514.exe
    echo 2. https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.3.4.20240514.exe
    echo.
    echo INSTALLATION:
    echo 1. Download the .exe file
    echo 2. Run as Administrator
    echo 3. Check "Add to PATH" during installation
    echo 4. Restart computer
    echo 5. Run this script again to verify
    echo.
    echo After installation, your system will support 100%% of PDF types!
)

echo.
pause