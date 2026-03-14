# AI Document Verification System

A complete AI-powered document verification system with user authentication and fast document processing.

## Features

- User registration and login
- Document upload and verification
- Support for PDFs and images
- AI-powered text extraction and analysis
- Real-time verification results
- Data visualization

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

#### Tesseract OCR (Required for image-based PDFs)

**Windows:**

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer: `tesseract-ocr-w64-setup-5.3.4.20240514.exe`
3. Make sure it's added to your system PATH

**Alternative (Chocolatey):**

```bash
choco install tesseract-ocr
```

#### Poppler (Required for PDF processing)

**Windows:**

1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract `poppler-24.08.0-0.zip` to your project folder
3. The system will automatically find and use the poppler binaries

**Note:** Poppler is a system library, not a Python package. Do NOT use `pip install poppler`.

### 3. Download NLTK Data

```python
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
```

## Running the Application

### Option 1: Using the Startup Script (Recommended)

**Windows:**

- Double-click `start_server.bat` in the project root folder
- Or run `start_server.ps1` in PowerShell

### Option 2: Manual Start

1. Navigate to the project directory:

```bash
cd your-project-folder
```

2. Set Poppler PATH and start the server:

**Windows (Command Prompt):**

```cmd
set PATH=%~dp0poppler\poppler-24.08.0\Library\bin;%PATH%
cd bbs
python app.py
```

**Windows (PowerShell):**

```powershell
$popplerPath = ".\poppler\poppler-24.08.0\Library\bin"
$env:PATH = "$popplerPath;$env:PATH"
cd bbs
python app.py
```

3. Open your browser and go to: `http://localhost:5000`

## Usage

1. **Register** a new account or **Login** with existing credentials
2. **Upload** a document (PDF or image)
3. **Fill in** verification details (name, father name, percentage)
4. **Click "Verify Document"** for instant AI-powered verification
5. **View results** with detailed analysis and visualization

## Supported Document Types

- **Text-based PDFs**: Direct text extraction (fastest)
- **Image-based PDFs**: OCR processing (requires Tesseract)
- **Images**: JPG, PNG, JPEG (OCR processing)

## API Endpoints

- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `POST /api/verify` - Document verification
- `GET /api/verified` - Get verified documents list

## Troubleshooting

### "Tesseract is not installed" Error

- Install Tesseract OCR from the link above
- Ensure it's in your system PATH
- Restart the application

### "Poppler is not installed" Error

- Install Poppler from the link above
- Add to system PATH
- Or use: `pip install poppler`

### PDF Processing Issues

- Text-based PDFs work without additional setup
- Image-based PDFs require both Tesseract and Poppler
- Check that all dependencies are properly installed

## System Requirements

- Python 3.8+
- Windows/Linux/macOS
- 2GB RAM minimum
- Internet connection for initial setup
