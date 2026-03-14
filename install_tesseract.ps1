# Tesseract OCR Installation and Verification Script
# Run this script to check and install Tesseract OCR

Write-Host "=== AI Document Verification System - Tesseract Setup ===" -ForegroundColor Yellow
Write-Host ""

# Check if Tesseract is already installed
Write-Host "Checking Tesseract installation..." -ForegroundColor Cyan
try {
    $tesseractVersion = & tesseract --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ TESSERACT IS ALREADY INSTALLED!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Version Information:" -ForegroundColor Cyan
        & tesseract --version
        Write-Host ""
        Write-Host "Your system can now process ALL document types!" -ForegroundColor Green
        Write-Host "- Text-based PDFs: Working"
        Write-Host "- Image-based PDFs: Working (with OCR)"
        Write-Host "- Images (JPG, PNG): Working"
        Write-Host ""
        Write-Host "Ready to start your AI Document Verification System!" -ForegroundColor Yellow
        return
    }
} catch {
    Write-Host "✗ Tesseract not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== TESSERACT INSTALLATION REQUIRED ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "To enable 100% PDF processing (including scanned/image-based PDFs),"
Write-Host "you must install Tesseract OCR."
Write-Host ""

# Download options
Write-Host "DOWNLOAD TESSERACT OCR:" -ForegroundColor Green
Write-Host ""
Write-Host "Option 1 - Official GitHub Release:" -ForegroundColor Cyan
Write-Host "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.4.20240514/tesseract-ocr-w64-setup-5.3.4.20240514.exe"
Write-Host ""
Write-Host "Option 2 - Alternative Mirror:" -ForegroundColor Cyan
Write-Host "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.3.4.20240514.exe"
Write-Host ""
Write-Host "Option 3 - Chocolatey (if available):" -ForegroundColor Cyan
Write-Host "choco install tesseract-ocr"
Write-Host ""

# Installation steps
Write-Host "INSTALLATION STEPS:" -ForegroundColor Green
Write-Host "1. Click one of the download links above"
Write-Host "2. Download: tesseract-ocr-w64-setup-5.3.4.20240514.exe (45MB)"
Write-Host "3. Run the installer as Administrator"
Write-Host "4. During installation:"
Write-Host "   ✓ Check 'Add to PATH' option"
Write-Host "   ✓ Choose default installation directory"
Write-Host "5. Restart your computer"
Write-Host "6. Run this script again to verify installation"
Write-Host ""

# What happens after installation
Write-Host "AFTER SUCCESSFUL INSTALLATION:" -ForegroundColor Yellow
Write-Host "✓ Text-based PDFs: Already working"
Write-Host "✓ Image-based PDFs: Will work with OCR"
Write-Host "✓ All image formats: Full support"
Write-Host "✓ AI Document Verification: 100% functional"
Write-Host ""

Write-Host "Your AI system will automatically detect Tesseract and use it for"
Write-Host "processing scanned documents, certificates, and image-based PDFs."
Write-Host ""

# Try to open download link
Write-Host "Opening download page..." -ForegroundColor Cyan
try {
    Start-Process "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.4.20240514/tesseract-ocr-w64-setup-5.3.4.20240514.exe"
} catch {
    Write-Host "Could not open browser. Please manually visit the download links above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")