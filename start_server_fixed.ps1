# AI Document Verification System - PowerShell Startup Script
# This script ensures proper PATH configuration and starts the Flask server

Write-Host "Starting AI Document Verification System..." -ForegroundColor Green
Write-Host ""

# Set paths for required binaries
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$popplerPath = Join-Path $projectRoot "poppler\poppler-24.08.0\Library\bin"
$tesseractPath = "C:\Program Files\Tesseract-OCR"

# Add to PATH
$env:PATH = "$popplerPath;$tesseractPath;$env:PATH"

Write-Host "Environment configured:" -ForegroundColor Yellow
Write-Host "- Poppler path: $popplerPath" -ForegroundColor Yellow
Write-Host "- Tesseract path: $tesseractPath" -ForegroundColor Yellow
Write-Host ""

# Change to bbs directory
Set-Location (Join-Path $projectRoot "bbs")

# Start the Flask server
Write-Host "Starting Flask server on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host ""

python app.py