# AI Document Verification System - Server Starter
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AI DOCUMENT VERIFICATION SYSTEM" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set poppler path
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$popplerPath = Join-Path $projectRoot "poppler\poppler-24.08.0\Library\bin"
$env:PATH = "$popplerPath;$env:PATH"

Write-Host "Setting up Poppler PATH..." -ForegroundColor Green
Write-Host "Poppler Path: $popplerPath" -ForegroundColor Gray

# Test poppler
Write-Host ""
Write-Host "Testing Poppler..." -ForegroundColor Green
try {
    $null = & pdfinfo -v 2>$null
    Write-Host "✓ Poppler is working" -ForegroundColor Green
} catch {
    Write-Host "✗ Poppler not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure poppler binaries are in: $popplerPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start server
Write-Host ""
Write-Host "Starting Flask server..." -ForegroundColor Green
Set-Location "bbs"
& python app.py