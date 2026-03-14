# AI Document Verification System

A complete AI-powered document verification system with OCR capabilities for processing both text-based and image-based PDFs.

## 🚀 Quick Start

### Method 1: Use the Fixed Startup Script (Recommended)

```bash
# Windows Batch Script
start_server_fixed.bat

# Or PowerShell Script
.\start_server_fixed.ps1
```

### Method 2: Manual Start

```bash
# Set environment variables
set PATH=C:\path\to\poppler\bin;C:\Program Files\Tesseract-OCR;%PATH%

# Start the server
cd bbs
python app.py
```

## 🌐 Access the Application

- **Main Application**: http://127.0.0.1:5000
- **Test Page**: http://127.0.0.1:5000/test
- **Health Check**: http://127.0.0.1:5000/api/health

## 📋 Features

- ✅ User Registration & Login
- ✅ Document Verification (Text & Image-based PDFs)
- ✅ OCR Processing with Tesseract
- ✅ QR Code Generation
- ✅ Document Type Analysis
- ✅ Real-time Verification Results

## 🔧 System Requirements

### Required Software:

- Python 3.8+
- Tesseract OCR 5.0+
- Poppler for PDF processing

### Python Packages:

```
Flask==3.0.0
Flask-CORS==4.0.0
pytesseract==0.3.10
opencv-python==4.8.1.78
Pillow==10.1.0
nltk==3.8.1
plotly==5.17.0
pandas==2.1.3
pdf2image==1.17.0
pdfplumber==0.10.3
```

## 🐛 Troubleshooting

### Connection Failed Error:

1. Ensure the server is running (check for Python process)
2. Use the startup scripts for proper PATH configuration
3. Check that ports 5000 are not blocked by firewall
4. Verify Tesseract and Poppler are properly installed

### OCR Not Working:

1. Ensure Tesseract is installed and in PATH
2. Check that `tesseract --version` works in terminal
3. Verify Poppler binaries are accessible

### Import Errors:

1. Install all requirements: `pip install -r requirements.txt`
2. Download NLTK data: `python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"`

## Technologies Used

- Frontend: HTML, CSS, JavaScript
- Backend: Flask, Python
- OCR: Tesseract
- NER: BERT (transformers)
- Visualization: Plotly
- Data Processing: Pandas
