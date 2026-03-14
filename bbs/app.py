# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
from pdf2image import convert_from_bytes
import pdfplumber
import re
import nltk
from nltk import ne_chunk, pos_tag, word_tokenize
import difflib
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.graph_objects as go
import pandas as pd
import os
import json
from datetime import datetime
import qrcode
import base64
from io import BytesIO
import sqlite3

# Configure pytesseract path (try common locations)
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\satya\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
    'tesseract'  # Default PATH
]

for path in tesseract_paths:
    if os.path.exists(path) or path == 'tesseract':
        try:
            pytesseract.pytesseract.tesseract_cmd = path
            # Test if it works
            pytesseract.get_tesseract_version()
            break
        except:
            continue

# Configure poppler path for pdf2image
poppler_path = r'C:\Users\satya\OneDrive\Desktop\project_college\poppler\poppler-24.08.0\Library\bin'
if not os.path.exists(poppler_path):
    # Fallback to other common locations
    poppler_paths = [
        r'C:\Users\satya\OneDrive\Desktop\project_college\poppler\poppler-24.08.0\Library\bin',
        r'C:\poppler\bin',
        r'C:\Program Files\poppler\bin',
        None  # Let pdf2image find it in PATH
    ]
    for path in poppler_paths:
        if path and os.path.exists(path):
            poppler_path = path
            break

app = Flask(__name__)
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"])

# File to store users
USERS_FILE = 'users.json'
DB_FILE = 'data.db'

# Global list to store verified documents
verified_documents = [
    {
        'id': 1,
        'name': 'John Doe',
        'father_name': 'Robert Doe',
        'status': 'Verified',
        'document_type': 'Aadhar Card',
        'date': '2026-02-14',
        'name_match_score': 100,
        'father_match_score': 95,
        'overall_match_score': 97.5
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'father_name': 'David Smith',
        'status': 'Verified',
        'document_type': 'Marksheet',
        'date': '2026-02-13',
        'name_match_score': 100,
        'father_match_score': 90,
        'overall_match_score': 95
    }
]

# Global variable for current logged in user
current_user = None

# ============================================
# HELPER FUNCTIONS FOR AADHAAR EXTRACTION
# ============================================

def get_aadhar(text):
    """Extract 12-digit Aadhaar number from text.
    
    Handles spaces, dashes, and OCR corruption.
    Only accepts 12-digit numbers. Ignores VID (16-digit numbers).
    """
    # Remove common separators and extract all sequences of digits
    text_cleaned = re.sub(r'[\s\-()]', '', text)
    
    # Look for 12 consecutive digits (Aadhar)
    patterns = [
        r'\d{4}\s?\d{4}\s?\d{4}',  # With or without spaces: XXXX XXXX XXXX
        r'(\d{12})',                # 12 consecutive digits
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Remove all non-digits
            clean_num = re.sub(r'\D', '', match)
            if len(clean_num) == 12:
                return clean_num
    
    return None


def get_name(text):
    """Extract name from document text (Aadhaar cards and certificates).
    
    Filters out garbage text like 'eT', 're', 'of', etc.
    Prioritizes proper capitalized name patterns.
    """
    # Look for 2+ capitalized words (proper name pattern)
    # This should match: "FirstName LastName" or "FirstName MiddleName LastName"
    name_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,})',  # 2+ capitalized words
    ]
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Skip garbage: too short, or mostly non-letters
        if not line or len(line) < 4:
            continue
        
        # Check if line is mostly letters (filter out noise)
        letter_count = sum(1 for c in line if c.isalpha())
        if letter_count / len(line) < 0.6:  # Less than 60% letters
            continue
        
        # Try pattern matching
        for pattern in name_patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1).strip()
                # Use improved validation
                if is_valid_name(name):
                    return name
    
    # Additional patterns for certificates
    # Look for "Student Name:" or similar patterns
    cert_name_patterns = [
        r'student\s+name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Student Name: First Last
        r'name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Name: First Last
    ]
    
    for pattern in cert_name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if is_valid_name(name):
                return name.title()


def get_father_name_from_certificate(text):
    """Extract father's name from certificate text.
    
    Handles corrupted S/O patterns and looks for name pairs.
    More lenient with OCR errors.
    """
    text_upper = text.upper()
    text_lower = text.lower()
    
    # Certificate patterns: Look for "Father's Name:" or similar
    cert_father_patterns = [
        r"father['\s]?s?\s+name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Father's Name: First Last
        r"son\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+has",  # Son of First Last (stop at "has")
        r"daughter\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+has",  # Daughter of First Last (stop at "has")
    ]
    
    for pattern in cert_father_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            father_name = match.group(1).strip()
            if is_valid_name(father_name):
                return father_name.title()
    
    # Look for "Son of" or "Daughter of" patterns in lines
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower().strip()
        if 'son of' in line_lower or 'daughter of' in line_lower:
            # Extract name after "of"
            if 'son of' in line_lower:
                parts = line_lower.split('son of')
            else:
                parts = line_lower.split('daughter of')
            
            if len(parts) > 1:
                after_of = parts[1].strip()
                # Take the first name-like sequence
                words = after_of.split()
                name_words = []
                for word in words:
                    if word and word[0].isupper():
                        name_words.append(word)
                    elif name_words:  # Stop at first non-capitalized word
                        break
                
                if len(name_words) >= 2:
                    candidate_father = ' '.join(name_words)
                    if is_valid_name(candidate_father):
                        return candidate_father.title()
    
    return None

def get_name_from_certificate(text):
    """Extract student name from certificate text.
    
    Looks for patterns specific to certificates like "Certified that" format.
    """
    text_upper = text.upper()
    text_lower = text.lower()
    
    # Certificate patterns: Look for "Certified that" followed by name (stop at "Daughter/Son of")
    cert_name_patterns = [
        r"certified\s+that\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+?)(?:\s+(?:daughter|son)\s+of)",  # Certified that First Last (stop at "Daughter/Son of")
        r"certified\s+that\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # Certified that First Last
        r"student\s+name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # Student Name: First Last
        r"name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # Name: First Last
    ]
    
    for pattern in cert_name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            student_name = match.group(1).strip()
            if is_valid_name(student_name):
                return student_name.title()
    
    # Look for name in lines after "Certified that" (handles multiline format)
    if 'certified that' in text_lower:
        certified_idx = text_lower.find('certified that')
        if certified_idx != -1:
            after_certified = text[certified_idx + len('certified that'):].strip()
            # Stop at "daughter of" or "son of"
            stop_patterns = ['daughter of', 'son of', 'has satisfactorily', 'has completed']
            for stop in stop_patterns:
                stop_idx = after_certified.lower().find(stop)
                if stop_idx != -1:
                    after_certified = after_certified[:stop_idx].strip()
                    break
            
            lines_after = after_certified.split('\n')
            for line in lines_after:
                line = line.strip()
                if line and len(line) > 2:  # Skip empty or very short lines
                    # Check if this line looks like a name (2+ words starting with capital letters)
                    words = line.split()
                    if len(words) >= 2 and all(word[0].isupper() for word in words if word):
                        candidate_name = ' '.join(words)
                        if is_valid_name(candidate_name):
                            # Make sure it's not a phrase like "Has successfully completed"
                            if not any(keyword in candidate_name.lower() for keyword in ['has', 'with', 'certificate', 'school', 'board', 'signature']):
                                return candidate_name.title()
    
    # Fallback: Look for any 2+ word capitalized sequence that could be a name
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:  # Reasonable length
            words = line.split()
            if len(words) >= 2 and all(word[0].isupper() for word in words if len(word) > 1):
                candidate_name = ' '.join(words)
                if is_valid_name(candidate_name):
                    return candidate_name.title()
    
    return None

def get_father(text):
    """Extract father's name from Aadhaar card text.
    
    Handles corrupted S/O patterns and looks for name pairs.
    More lenient with OCR errors.
    """
    text_upper = text.upper()
    text_lower = text.lower()
    
    # Pattern 1: Look for S/O, s/o, Ss, or corrupted versions followed by name
    # Handle OCR corruption where S/O becomes "Ss" or similar
    so_patterns = [
        r"[Ss]/[Oo]\s+([A-Z][A-Za-z\s]+?)(?:\n|\s{2,}|at\b|po\b|address\b)",  # S/O Name
        r"\bSs\s+([A-Z][A-Za-z\s]+?)(?:\n|\s{2,}|at\b|po\b|address\b)",  # Ss corrupted to S/O
        r"c/o\s+([A-Z][A-Za-z\s]+?)(?:\n|\s{2,}|at\b|po\b)",  # c/o Name
        r"father['\s]?s?\s+name[:\s]*([A-Z][A-Za-z\s]+?)(?:\n|\s{2,}|at\b|po\b)",  # Father's Name:
        r"son\s+of\s+([A-Z][A-Za-z\s]+?)(?:\n|\s{2,}|at\b|po\b)",  # Son of Name
    ]
    
    for pattern in so_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            father_name = match.group(1).strip()
            # Use improved validation
            if is_valid_name(father_name):
                return father_name.title()
    
    # Pattern 2: Look for common father name patterns in lines
    # Sometimes father name appears near the main name on different line or after
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Look for lines that contain name-like patterns
        if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', line):
            # Check if this could be a father name (not the main name)
            potential_name = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', line)
            if potential_name:
                candidate = potential_name.group(1).strip()
                if is_valid_name(candidate):
                    # Check if this appears after "Father" or similar indicators
                    line_lower = line.lower()
                    if any(indicator in line_lower for indicator in ['father', 's/o', 'c/o', 'son of', 'daughter of']):
                        return candidate.title()
    
    # Fallback: If we know it's an Aadhar, look for any 2-3 word name
    if "aadhar" in text_lower or "aadhaar" in text_lower:
        # Look for any 2-3 word name
        potential_names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', text)
        for name in potential_names:
            if is_valid_name(name):
                return name.title()
    
    return None


# ============================================
# Load or create users file
def load_users():
    # Deprecated: prefer database. Keep JSON as fallback for migrations.
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f)


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(migrate_from_json=True):
    """Initialize SQLite database and optionally migrate users.json into it."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            fullName TEXT,
            password TEXT,
            registeredDate TEXT
        )
    ''')
    conn.commit()

    # Migrate existing users.json if present
    if migrate_from_json and os.path.exists(USERS_FILE):
        try:
            users = load_users()
            for email, info in users.items():
                # If user already exists in DB skip
                cur.execute('SELECT email FROM users WHERE email = ?', (email,))
                if cur.fetchone():
                    continue
                stored_pwd = info.get('password', '')
                # If stored password is plaintext, hash it
                if stored_pwd and not stored_pwd.startswith('pbkdf2:'):
                    try:
                        stored_pwd = generate_password_hash(stored_pwd)
                    except Exception:
                        pass
                cur.execute('INSERT OR IGNORE INTO users (email, fullName, password, registeredDate) VALUES (?, ?, ?, ?)',
                            (email, info.get('fullName', ''), stored_pwd, info.get('registeredDate', '')))
            conn.commit()
        except Exception:
            pass

    conn.close()

# Download NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

def deskew_image(image):
    """Correct document skew/tilt"""
    gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Try to detect horizontal and vertical lines for skew detection
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
    
    if lines is None or len(lines) == 0:
        return image
    
    # Calculate average angle
    angles = []
    for line in lines:
        rho, theta = line[0]
        angle = (theta * 180 / np.pi) - 90
        if -45 < angle < 45:  # Only consider relatively small angles
            angles.append(angle)
    
    if not angles:
        return image
    
    avg_angle = np.median(angles)
    
    # Rotate image to correct skew
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    
    return rotated

def preprocess_image(image):
    # Ultra-enhanced preprocessing for poor quality OCR documents
    
    # Step 1: Deskew the document
    corrected = deskew_image(image)
    
    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY) if len(corrected.shape) == 3 else corrected
    
    # Step 2.5: Resize to optimal size for OCR (around 1500-3000 pixels width)
    height, width = gray.shape
    if width > 3000:
        scale = 3000 / width
        new_width = 3000
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
    elif width < 1500:
        scale = 1500 / width
        new_width = 1500
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Step 2.75: Apply initial thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Step 3: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(thresh)
    
    # Step 4: Apply bilateral filter for edge-preserving noise reduction
    denoised = cv2.bilateralFilter(enhanced, 11, 17, 17)
    
    # Step 5: Apply multiple thresholding methods and attempt both
    # Method 1: Otsu's thresholding (automatic threshold selection)
    _, thresh_otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Method 2: Adaptive thresholding (better for uneven lighting)
    thresh_adaptive = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 2)
    
    # Method 3: Simple thresholding with median value
    median_val = np.median(denoised)
    _, thresh_median = cv2.threshold(denoised, int(median_val * 1.1), 255, cv2.THRESH_BINARY)
    
    # Combine the best thresholding results (use Otsu as primary)
    thresh = thresh_otsu
    
    # Step 6: Apply morphological operations to clean up and connect text
    # Remove small noise
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_small, iterations=1)
    
    # Connect broken text
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
    
    # Dilate to make text thicker for better recognition
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.dilate(thresh, kernel_dilate, iterations=1)
    
    # Step 8: Erode slightly to remove excess thickness
    kernel_erode = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.erode(cleaned, kernel_erode, iterations=1)
    
    return cleaned

def is_valid_ocr_text(text):
    """Check if OCR output is valid or corrupted"""
    if not text or len(text.strip()) < 5:
        return False
    
    # If text has too many short fragments separated by commas, it's likely corrupted
    fragments = [x.strip() for x in text.split(',')]
    single_letters = [f for f in fragments if len(f) <= 2]
    
    # If more than 50% are single letters/short, it's corrupted
    if len(single_letters) > len(fragments) * 0.5:
        return False
    
    # Check for suspicious patterns indicating corruption
    if re.search(r'[A-Z]{1,2}(\s+[A-Z]{1,2})+', text):  # Many single letter sequences
        return False
    
    # Valid text should have at least some normal words
    words = text.split()
    avg_word_length = np.mean([len(w) for w in words if len(w) > 0])
    if avg_word_length < 2.5:  # Average word too short = corrupted
        return False
    
    return True

def extract_text(image):
    # Enhanced OCR with multiple configurations and validation
    try:
        texts = []
        
        # Try to extract with better Tesseract configuration for poor quality images
        # Configuration 1: Standard document OCR with bilingual support (English + Odia for Indian documents)
        config1 = r'--oem 3 --psm 3'
        text1 = pytesseract.image_to_string(image, lang='eng+ori', config=config1)
        if text1.strip():
            texts.append(text1)
        
        # Configuration 2: Single text line with bilingual support
        config2 = r'--oem 3 --psm 7'
        text2 = pytesseract.image_to_string(image, lang='eng+ori', config=config2)
        if text2.strip() and is_valid_ocr_text(text2):
            texts.append(text2)
        
        # Configuration 3: Automatic page segmentation with bilingual support
        config3 = r'--oem 3 --psm 3'
        text3 = pytesseract.image_to_string(image, lang='eng+ori', config=config3)
        if text3.strip() and is_valid_ocr_text(text3):
            texts.append(text3)
        
        # Configuration 4: Sparse text (good for certificates) with bilingual support
        config4 = r'--oem 3 --psm 11'
        text4 = pytesseract.image_to_string(image, lang='eng+ori', config=config4)
        if text4.strip() and is_valid_ocr_text(text4):
            texts.append(text4)
        
        # Configuration 5: Assume single uniform block of text with bilingual support
        config5 = r'--oem 3 --psm 13'
        text5 = pytesseract.image_to_string(image, lang='eng+ori', config=config5)
        if text5.strip() and is_valid_ocr_text(text5):
            texts.append(text5)
        
        # Configuration 6: Specific for Aadhar cards - uniform block with numbers and bilingual
        config6 = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/- '
        text6 = pytesseract.image_to_string(image, lang='eng+ori', config=config6)
        if text6.strip() and is_valid_ocr_text(text6):
            texts.append(text6)
        
        # Configuration 7: Numbers only - specifically for Aadhaar numbers and digits
        config7 = r'--oem 3 --psm 3 -c tessedit_char_whitelist=0123456789 '
        text7 = pytesseract.image_to_string(image, lang='eng', config=config7)
        
        # Configuration 8: Numbers with sparse text PSM
        config8 = r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789 '
        text8 = pytesseract.image_to_string(image, lang='eng', config=config8)
        
        # Configuration 9: Automatic page segmentation with OSD
        config9 = r'--oem 3 --psm 1'
        text9 = pytesseract.image_to_string(image, lang='eng+ori', config=config9)
        if text9.strip():
            texts.append(text9)
        if text7.strip():
            texts.append(text7)
        
        # If no valid text found, at least one of the extractions worked
        if not texts and text1.strip():
            texts.append(text1)
        
        # Combine all extracted texts (take the longest valid text, then append numbers)
        combined_text = max(texts, key=len) if texts else ""
        
        # If we have numbers text, append it to ensure Aadhaar numbers are included
        if 'text7' in locals() and text7.strip():
            combined_text += ' ' + text7
        if 'text8' in locals() and text8.strip():
            combined_text += ' ' + text8
        
        if not combined_text:
            # Fallback: try with character whitelist to get something
            config_fallback = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '
            combined_text = pytesseract.image_to_string(image, lang='eng', config=config_fallback)
        
        # Enhanced text cleanup
        if combined_text:
            # Remove excessive whitespace
            combined_text = re.sub(r'\n\s*\n\s*\n', '\n\n', combined_text)
            combined_text = re.sub(r'\n\s*\n', '\n', combined_text)
            
            # Clean up common OCR errors
            combined_text = combined_text.replace('|', 'I')
            combined_text = combined_text.replace('0', 'O')
            combined_text = re.sub(r'([A-Z])\s+([A-Z])', r'\1\2', combined_text)
            
            # Remove non-printable characters
            combined_text = ''.join(char for char in combined_text if char.isprintable() or char in '\n\t')
        
        # Apply text preprocessing to fix OCR errors
        combined_text = preprocess_extracted_text(combined_text)
        
        return combined_text
    except Exception as e:
        # If tesseract is not available, return empty text with error info
        return f"[OCR UNAVAILABLE] Tesseract not installed or not in PATH. Error: {str(e)}"


def is_valid_name(name):
    """Check if extracted text looks like a valid name"""
    if not name or len(name.strip()) < 2:
        return False
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Must have at least 2 words for Aadhar names (first + last)
    words = name.split()
    if len(words) < 2:
        return False
    
    # Each word should be at least 3 characters long to filter out garbage like "Ptr Es", "Ws Mig"
    for word in words:
        if len(word) < 3:
            return False
    
    # Filter out invalid name terms
    invalid_name_terms = [
        'issue', 'date', 'valid', 'till', 'permanent', 'signature', 'photo', 'help', 'line',
        'government', 'india', 'unique', 'identification', 'authority', 'aadhaar', 'aadhar',
        'card', 'your', 'enrolment', 'number', 'male', 'female', 'transgender', 'dob',
        'birth', 'address', 'mobile', 'phone', 'email', 'pincode', 'state', 'district',
        'village', 'post', 'office', 'police', 'station', 'sub', 'division', 'block',
        'gram', 'panchayat', 'tehsil', 'taluk', 'mandal', 'zilla', 'parishad',
        'board', 'secondary', 'education', 'certificate', 'marksheet', 'passed',
        'examination', 'result', 'grade', 'percentage', 'total', 'marks', 'obtained',
        'maximum', 'minimum', 'average', 'cgpa', 'gpa', 'division', 'class',
        'school', 'college', 'university', 'institute', 'academy', 'center', 'centre',
        'high'
    ]
    
    name_lower = name.lower()
    for term in invalid_name_terms:
        if term in name_lower:
            return False
    
    # Name should have mostly letters
    letter_count = sum(1 for c in name if c.isalpha())
    total_chars = len(name)
    
    if total_chars > 0 and letter_count / total_chars < 0.7:
        return False
    
    # Name should be reasonably short (< 50 chars)
    if len(name) > 50:
        return False
    
    # Avoid single letter sequences scattered everywhere
    if re.search(r'\b[A-Z]\b\s+\b[A-Z]\b\s+\b[A-Z]\b', name):
        return False
    
    # Should not be mostly numbers
    if sum(1 for c in name if c.isdigit()) / max(1, len(name)) > 0.3:
        return False
    
    # Reject names with obvious OCR artifacts (consecutive uppercase letters not at start)
    if re.search(r'(?<=\w)[A-Z]{2,}', name):
        return False
    
    # Reject names that start with non-alphabetic characters
    if not name[0].isalpha():
        return False
    
    # Each word should start with capital letter (proper name)
    for word in words:
        if len(word) > 0 and not word[0].isupper():
            return False
    
    # Reject names with too many uppercase letters in sequence at the beginning
    for word in words:
        if len(word) > 1 and word[1].isupper() and word[0].isupper():
            # Check if it's a valid abbreviation (like "Dr." or "Mr.")
            if word not in ['Dr', 'Mr', 'Ms', 'Mrs', 'Sr', 'Jr']:
                return False
    
    return True
    
    # For Aadhar cards, names should typically be Indian names
    # Reject if it contains common OCR garbage words
    garbage_words = ['of', 'to', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'for', 'with', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'issue', 'date', 'valid', 'till', 'permanent', 'signature', 'photo', 'help', 'line', 'government', 'india', 'unique', 'identification', 'authority', 'aadhar', 'aadhaar', 'card', 'your', 'issued']
    if any(word.lower() in garbage_words for word in words):
        return False
    
    # Names should have proper capitalization (first letter capital, rest lowercase)
    for word in words:
        if len(word) > 1 and not (word[0].isupper() and word[1:].islower()):
            # Allow some flexibility for names like "McDonald" or "O'Connor"
            if not any(word[i:i+2].isupper() for i in range(len(word)-1)):
                continue
            return False
    
    return True

def extract_entities_nltk(text):
    """Extract named entities with validation"""
    entities = []
    
    if not text or len(text.strip()) < 3:
        return entities
    
    try:
        words = word_tokenize(text)
        pos_tags = pos_tag(words)
        chunks = ne_chunk(pos_tags)
        
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                name = ' '.join(c[0] for c in chunk)
                # Validate extracted name
                if is_valid_name(name):
                    entities.append((chunk.label(), name))
    except Exception as e:
        # If NLTK processing fails, just return empty
        pass
    
    return entities

def preprocess_extracted_text(text):
    """Clean up common OCR errors and improve text quality"""
    if not text or text.startswith("[OCR UNAVAILABLE]"):
        return text
    
    # Common OCR character substitutions (avoid digits -> letters)
    corrections = {
        'l': 'I', '|': 'I', '!': 'I',
        '$': 'S',
        'Hf': 'of', 'Vif': 'the', 'YY': 'has',  # Common word fragments
        'Reece': 'passed',  # Common misread
    }
    
    # Apply character corrections
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # Fix common word fragments
    text = re.sub(r'\bHf\b', 'of', text, flags=re.IGNORECASE)
    text = re.sub(r'\bVif\b', 'the', text, flags=re.IGNORECASE)
    text = re.sub(r'\bYY\b', 'has', text, flags=re.IGNORECASE)
    text = re.sub(r'\bReece\b', 'passed', text, flags=re.IGNORECASE)
    
    # Clean up spacing around punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def extract_document_details(text):
    """Extract comprehensive details from various document types"""
    # Preprocess the text to fix common OCR errors
    text = preprocess_extracted_text(text)
    
    details = {
        'names': [],
        'father_names': [],
        'mother_names': [],
        'dates': [],
        'numbers': [],
        'addresses': [],
        'percentages': [],
        'grades': [],
        'document_numbers': [],
        'issuing_authority': None,
        'document_type': None,
        'mobile_numbers': [],
        'aadhar_number': None
    }

    text_lower = text.lower()
    lines = text.split('\n')

    # Always try the robust extraction functions first
    # Use document-type specific extraction based on initial analysis
    initial_doc_type = analyze_document_type(text)
    
    if initial_doc_type == 'Academic Certificate':
        name = get_name_from_certificate(text)
        father = get_father_name_from_certificate(text)
    else:
        name = get_name(text)
        father = get_father(text)
    
    if name and name not in details['names']:
        details['names'].insert(0, name)  # Put at beginning
    
    if father and father not in details['father_names']:
        details['father_names'].insert(0, father)  # Put at beginning

    # Skip NER for certificates as it causes false positives - use only certificate-specific extraction
    if initial_doc_type != 'Academic Certificate':
        # Extract names using NER
        entities = extract_entities_nltk(text)
        raw_names = [name for label, name in entities if label == 'PERSON']
        
        # First, try explicit "Name:" patterns for certificates/marksheets
        explicit_name_pattern = r'(?:student\s+)?name\s*[:\-]?\s*([A-Za-z\s]+?)(?:\n|\s{2,}|$|[\d\(\)])'
        explicit_matches = re.findall(explicit_name_pattern, text, re.IGNORECASE)
        for match in explicit_matches:
            candidate = match.strip()
            if is_valid_name(candidate) and candidate not in raw_names:
                raw_names.insert(0, candidate)  # Prioritize explicit names
        
        details['names'] = [name for name in raw_names if is_valid_name(name)]

        # Additional name extraction using patterns (more robust)
        name_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',  # Two or more capitalized words
            r'\b([A-Z][a-z]{2,})\b',  # Single capitalized word with at least 3 letters
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if is_valid_name(match) and match not in details['names']:
                    details['names'].append(match)

    # Special handling for Aadhar cards
    if 'aadhar' in text_lower or 'aadhaar' in text_lower or 'ଆଧାର' in text:
        # Use helper functions for Aadhaar card extraction
        
        # Extract name using dedicated function
        name = get_name(text)
        if name and name not in details['names']:
            details['names'].insert(0, name)  # Put at beginning
        
        # Extract father's name using dedicated function
        father = get_father(text)
        if father and father not in details['father_names']:
            details['father_names'].insert(0, father)  # Put at beginning
        
        # Extract Aadhar number using dedicated function
        aadhar = get_aadhar(text)
        if aadhar:
            details['aadhar_number'] = aadhar
            if aadhar not in details['document_numbers']:
                details['document_numbers'].insert(0, aadhar)
        name = get_name(text)
        if name and name not in details['names']:
            details['names'].insert(0, name)  # Put at beginning
        
        father = get_father(text)
        if father and father not in details['father_names']:
            details['father_names'].insert(0, father)  # Put at beginning
        

    # General patterns for certificates and other documents
    # Try to extract from "Certified that" format (works across lines)
    if 'certified that' in text_lower:
        certified_idx = text_lower.find('certified that')
        if certified_idx != -1:
            after_certified = text[certified_idx + len('certified that'):].strip()
            lines_after = after_certified.split('\n')
            student_name = lines_after[0].strip() if lines_after else ""
            student_name = re.sub(r'\s*\([^)]*\).*$', '', student_name).strip()
            student_name = re.sub(r'[^A-Za-z\s].*$', '', student_name).strip()
            if is_valid_name(student_name):
                low = student_name.lower()
                if not any(keyword in low for keyword in ['son','daughter','of','and','school','college','university','institute','academy','high']):
                    details['names'].append(student_name)
            lines_after = after_certified.split('\n')
            for idx, line in enumerate(lines_after):
                line_lower = line.lower().strip()
                if '(mother)' in line_lower and idx > 0:
                    prev_line = lines_after[idx-1].strip()
                    if ' of ' in prev_line.lower():
                        mother_name = re.sub(r'.*\s+of\s+','', prev_line, flags=re.IGNORECASE).strip()
                    else:
                        mother_name = prev_line
                    if is_valid_name(mother_name):
                        details['mother_names'].append(mother_name)
                if '(father)' in line_lower and idx > 0:
                    prev_line = lines_after[idx-1].strip()
                    if prev_line.lower().startswith('and '):
                        father_name = re.sub(r'^and\s+','',prev_line, flags=re.IGNORECASE).strip()
                    else:
                        father_name = re.sub(r'.*\s+and\s+','',prev_line, flags=re.IGNORECASE).strip() if ' and ' in prev_line.lower() else prev_line
                    if is_valid_name(father_name):
                        details['father_names'].append(father_name)
            if not details['mother_names'] and not details['father_names']:
                # look for "son/daughter of X"; allow trailing text after the name
                # match parent name until 'has' or 'and' or end-of-text
                son_daughter_pattern = r'(?:son|daughter)\s+of\s+([A-Z][A-Za-z\s]+?)(?=\s+has\b|\s+and\b|$)'
                son_match = re.search(son_daughter_pattern, after_certified, re.IGNORECASE)
                if son_match:
                    first_parent = son_match.group(1).strip()
                    start_pos = son_match.end()
                    # check if another parent follows with "and"
                    second_parent_match = re.search(r'and\s+([A-Z][A-Za-z\s]+?)\b', after_certified[start_pos:], re.IGNORECASE)
                    if second_parent_match:
                        second_parent = second_parent_match.group(1).strip()
                        # assume first_parent is mother, second is father
                        details['mother_names'].append(first_parent)
                        if second_parent and second_parent != first_parent:
                            details['father_names'].append(second_parent)
                    else:
                        # treat found name as father by default
                        details['father_names'].append(first_parent)
    # Fallback: Process line by line for other patterns
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        total_pattern = r'total\s*\(?(?:[a-z\s]+)?(\d+)\)?'
        total_match = re.search(total_pattern, line_lower, re.IGNORECASE)
        if total_match:
            total_marks = int(total_match.group(1))
            full_marks_match = re.search(r'(\d+)\s*marks?', text_lower)
            if full_marks_match:
                full_marks = int(full_marks_match.group(1))
                if full_marks > 0:
                    percentage = (total_marks / full_marks) * 100
                    details['percentages'].append(round(percentage,2))
            else:
                percentage = (total_marks / 600) * 100
                details['percentages'].append(round(percentage,2))
        dob_pattern = r'born on\s+(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        dob_match = re.search(dob_pattern, line_lower, re.IGNORECASE)
        if dob_match:
            details['dates'].append(dob_match.group(1))
    # Additional certificate patterns: explicit 'Student Name' or 'Name:' lines
    for line in lines:
        if re.search(r'\b(student name|name)\b[:\s]', line, re.IGNORECASE):
            nm = re.sub(r'.*?(student name|name)[:\s]+','', line, flags=re.IGNORECASE).strip()
            if nm and nm not in details['names'] and is_valid_name(nm):
                details['names'].append(nm)
        if re.search(r"father['\s]?s\s+name[:\s]", line, re.IGNORECASE):
            fn = re.sub(r".*?father['\s]?s\s+name[:\s]+",'', line, flags=re.IGNORECASE).strip()
            if fn and fn not in details['father_names'] and is_valid_name(fn):
                details['father_names'].append(fn)
        if re.search(r"mother['\s]?s\s+name[:\s]", line, re.IGNORECASE):
            mn = re.sub(r".*?mother['\s]?s\s+name[:\s]+",'', line, flags=re.IGNORECASE).strip()
            if mn and mn not in details['mother_names'] and is_valid_name(mn):
                details['mother_names'].append(mn)
        pct_match = re.search(r'(\d{1,3}(?:\.\d+)?)[\s]*%', line)
        if pct_match:
            try:
                pct_value = float(pct_match.group(1))
                if pct_value not in details['percentages']:
                    details['percentages'].append(pct_value)
            except:
                pass

    # Extract dates
    date_patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b',  # YYYY/MM/DD
        r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})\b',  # DD Month YYYY
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        details['dates'].extend(matches)

    # Extract percentages and grades
    percentage_patterns = [
        r'(\d+(?:\.\d+)?)\s*%',  # 85.5%
        r'percentage[:\s]*(\d+(?:\.\d+)?)',  # percentage: 85.5
        r'(\d+(?:\.\d+)?)\s*marks?\s*/?\s*\d*',  # 85.5 marks or 450/500
        r'cgpa[:\s]*(\d+(?:\.\d+)?)',  # CGPA: 8.5
        r'grade[:\s]*([a-f][+-]?)',  # Grade: A+
        r'(\d+)\s*/\s*(\d+)',  # 512/600 format
        r'(\d+)\s+out\s+of\s+(\d+)',  # 512 out of 600
        r'total[:\s]*(\d+)\s*/?\s*(\d*)',  # total: 512/600 or total: 512
    ]
    for pattern in percentage_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle patterns with two capture groups like 512/600
                if len(match) == 2 and match[1]:
                    try:
                        obtained = float(match[0])
                        total = float(match[1])
                        if total > 0:
                            percentage = (obtained / total) * 100
                            details['percentages'].append(round(percentage, 2))
                    except:
                        pass
                continue
            
            if '%' in match or 'percentage' in match.lower():
                details['percentages'].append(float(re.search(r'(\d+(?:\.\d+)?)', match).group(1)))
            elif 'cgpa' in match.lower():
                details['percentages'].append(float(re.search(r'(\d+(?:\.\d+)?)', match).group(1)))
            elif 'grade' in match.lower():
                details['grades'].append(match.split()[-1] if ' ' in match else match)
            else:
                # Check if it's a marks format like 450/500
                if '/' in match:
                    parts = match.split('/')
                    if len(parts) == 2 and parts[1].strip():
                        try:
                            obtained = float(parts[0])
                            total = float(parts[1])
                            percentage = (obtained / total) * 100
                            details['percentages'].append(round(percentage, 2))
                        except ValueError:
                            pass
                else:
                    try:
                        val = float(match)
                        if val > 10:  # Likely a percentage
                            details['percentages'].append(val)
                    except ValueError:
                        pass

    # Extract document numbers (Aadhar, PAN, etc.) - Enhanced filtering
    number_patterns = [
        r'\b\d{4}\s*\d{4}\s*\d{4}\b',  # Aadhar: XXXX XXXX XXXX
        r'\b[a-zA-Z]{5}\d{4}[a-zA-Z]\b',  # PAN: AAAAA9999A
        r'\b\d{8,12}\b',  # Other numbers
        r'\b[A-Z]{1,2}\d{6,8}\b',  # Passport/DL numbers
    ]
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # For Aadhar numbers, ensure they are exactly 12 digits
            clean_match = re.sub(r'\D', '', str(match))
            if len(clean_match) == 12 and clean_match.isdigit():
                # Additional check: exclude if it looks like a mobile number pattern
                if not (clean_match.startswith('6') or clean_match.startswith('7') or 
                       clean_match.startswith('8') or clean_match.startswith('9')):
                    if clean_match not in details['document_numbers']:
                        details['document_numbers'].append(clean_match)
                        details['aadhar_number'] = clean_match
            else:
                # For other numbers, filter out mobile numbers (10 digits starting with 6-9)
                if clean_match not in details['document_numbers']:
                    details['document_numbers'].append(clean_match)
                    details['aadhar_number'] = clean_match

    # Extract addresses (basic)
    address_keywords = ['address', 'addr', 'residence', 'permanent', 'current', 'at', 'po']
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in address_keywords):
            # Get the next few lines as address
            address_lines = []
            for j in range(i, min(i+3, len(lines))):
                if lines[j].strip():
                    address_lines.append(lines[j].strip())
            if address_lines:
                details['addresses'].append(' '.join(address_lines))

    # Try to identify father/mother names (fallback)
    # If an Aadhar number was found, prefer Aadhar Card as the document type
    if details.get('aadhar_number'):
        details['document_type'] = 'Aadhar Card'
    else:
        details['document_type'] = analyze_document_type(text)
    
    # Clean up and deduplicate names
    details['names'] = clean_and_deduplicate_names(details['names'])
    details['father_names'] = clean_and_deduplicate_names(details['father_names'])
    details['mother_names'] = clean_and_deduplicate_names(details['mother_names'])

    # Remove duplicate percentages and sort
    if details['percentages']:
        try:
            unique_pcts = sorted(set(details['percentages']))
            details['percentages'] = unique_pcts
        except Exception:
            pass
    
    return details

def clean_and_deduplicate_names(names_list):
    """Clean up names list by removing duplicates and invalid names"""
    if not names_list:
        return []
    
    # Remove duplicates (case insensitive)
    seen = set()
    unique_names = []
    for name in names_list:
        name_lower = name.lower().strip()
        if name_lower not in seen and is_valid_name(name):
            seen.add(name_lower)
            unique_names.append(name.strip())
    
    # Sort by length (shorter names first, as they might be more accurate)
    unique_names.sort(key=len)
    
    return unique_names

def smart_match(user_value, extracted_values, match_type='string'):
    """Smart matching with fuzzy logic"""
    if not user_value or not extracted_values:
        return False, None, 0

    user_value = str(user_value).lower().strip()
    best_match = None
    best_score = 0
    match_found = False

    # Use difflib's SequenceMatcher for fuzzy scoring
    for extracted in extracted_values:
        extracted_raw = str(extracted)
        extracted = extracted_raw.lower().strip()

        if match_type == 'name':
            # Combine token overlap with sequence similarity
            user_tokens = set(user_value.split())
            ext_tokens = set(extracted.split())
            if user_tokens and ext_tokens:
                token_overlap = len(user_tokens & ext_tokens) / max(1, len(user_tokens | ext_tokens))
            else:
                token_overlap = 0

            seq_ratio = difflib.SequenceMatcher(None, user_value, extracted).ratio()
            
            # Special handling for names with prefix garbage (OCR artifacts)
            # Check if the user name appears as a suffix in the extracted name
            if extracted.endswith(user_value) and len(extracted) > len(user_value):
                # If the prefix looks like OCR garbage, boost the score
                prefix = extracted[:-len(user_value)].strip()
                if not any(c.isalpha() for c in prefix) or re.search(r'[A-Z]{2,}', prefix):
                    seq_ratio = max(seq_ratio, 0.95)  # Boost similarity
            
            # Weighted score: give token overlap more importance
            score = int(((token_overlap * 0.6) + (seq_ratio * 0.4)) * 100)

            # direct exact or containment checks increase confidence
            if user_value == extracted:
                score = 100
            elif user_value in extracted or extracted in user_value:
                score = max(score, 90)

            if score > best_score:
                best_score = score
                best_match = extracted_raw
                match_found = score >= 75

        elif match_type == 'number':
            # Try numeric comparison first
            clean_user = re.sub(r'\D', '', user_value)
            clean_ext = re.sub(r'\D', '', extracted)
            if clean_user and clean_ext and clean_user.isdigit() and clean_ext.isdigit():
                if clean_user == clean_ext:
                    return True, extracted_raw, 100
                # Partial last-4 comparison
                if len(clean_user) >= 4 and len(clean_ext) >= 4 and clean_user[-4:] == clean_ext[-4:]:
                    score = 75
                else:
                    score = int(difflib.SequenceMatcher(None, clean_user, clean_ext).ratio() * 100)
            else:
                score = int(difflib.SequenceMatcher(None, user_value, extracted).ratio() * 100)

            if score > best_score:
                best_score = score
                best_match = extracted_raw
                match_found = score >= 85

        else:
            # General string fuzzy match
            score = int(difflib.SequenceMatcher(None, user_value, extracted).ratio() * 100)
            if user_value in extracted or extracted in user_value:
                score = max(score, 85)
            if score > best_score:
                best_score = score
                best_match = extracted_raw
                match_found = score >= 85

    return match_found, best_match, best_score

def extract_name(text):
    # Use NLTK NER instead for faster processing
    entities = extract_entities_nltk(text)
    names = [name for label, name in entities if label == 'PERSON']
    return names

def extract_percentage(text):
    # More flexible regex for percentages
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%',  # 85.5%
        r'percentage[:\s]*(\d+(?:\.\d+)?)',  # percentage: 85.5
        r'(\d+(?:\.\d+)?)\s*marks',  # 85.5 marks
    ]
    for pattern in patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # return the first capturing group if available
                if match.lastindex:
                    return float(match.group(1))
        except Exception:
            continue
    return None

def generate_qr_code(data):
    """Generate QR code and return as base64 string"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_base64}"
    except Exception as e:
        return None

def analyze_document_type(text):
    """Analyze document type based on extracted text - Enhanced for universal applicability"""
    text_lower = text.lower()
    
    # Marksheet patterns - Check FIRST (most specific)
    marksheet_keywords = [
        'marksheet', 'mark sheet', 'statement of marks', 'grade card',
        'result', 'score card', 'academic record', 'transcript'
    ]
    
    if any(keyword in text_lower for keyword in marksheet_keywords):
        return "Marksheet"
    
    # Marksheet content patterns - very specific
    marksheet_content = ['board of', 'total marks', 'student name:', 'father name:', 'grade card', 'academic record']
    if any(content in text_lower for content in marksheet_content):
        return "Marksheet"
    
    # Certificate patterns - Check after marksheet
    certificate_keywords = [
        'certificate', 'certified', 'diploma', 'degree', 'graduation',
        'academic', 'education', 'qualification', 'award', 'merit',
        'completion', 'course', 'examination', 'board', 'university',
        'college', 'school', 'institute', 'institution'
    ]
    
    if any(keyword in text_lower for keyword in certificate_keywords):
        # Further check for certificate-specific content
        cert_content = ['student name', 'father name', 'mother name', 'date of birth', 'passed', 'secured', 'daughter of', 'son of', 'certified that']
        if any(content in text_lower for content in cert_content):
            return "Academic Certificate"
        # If certificate keywords found but no specific content, still treat as certificate
        return "Academic Certificate"
    
    # Aadhar patterns - Enhanced detection
    aadhar_keywords = ['aadhar', 'aadhaar', 'uid', 'unique identification', 'ଆଧାର', 'आधार']
    aadhar_patterns = [r'\b\d{4}\s*\d{4}\s*\d{4}\b', r'\b\d{12}\b']
    
    if any(keyword in text_lower for keyword in aadhar_keywords):
        return "Aadhar Card"
    if any(re.search(pattern, text) for pattern in aadhar_patterns):
        return "Aadhar Card"
    
    # PAN Card patterns
    pan_patterns = [r'\b[a-zA-Z]{5}\d{4}[a-zA-Z]\b']
    pan_keywords = ['permanent account number', 'pan card']
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in pan_patterns) or \
       any(keyword in text_lower for keyword in pan_keywords):
        return "PAN Card"

    # Passport patterns
    passport_keywords = ['passport', 'republic of india', 'travel document', 'passport no']
    if any(keyword in text_lower for keyword in passport_keywords):
        return "Passport"

    # Driving License patterns
    license_keywords = ['driving licence', 'license', 'dl no', 'driving license', 'motor vehicle']
    if any(keyword in text_lower for keyword in license_keywords):
        return "Driving License"

    # Voter ID patterns
    voter_keywords = ['voter id', 'electoral photo', 'election commission', 'voter card']
    if any(keyword in text_lower for keyword in voter_keywords):
        return "Voter ID Card"
    
    # ID Card patterns (broader category)
    id_patterns = ['identity card', 'id card', 'photo id', 'government id']
    if any(pattern in text_lower for pattern in id_patterns):
        return "ID Card"
    
    # If document has name and father/mother names but no specific type, treat as Certificate
    if any(name_pattern in text_lower for name_pattern in ['name', 'father', 'mother', 'parent']):
        if len(text.strip()) > 100:  # Reasonable length document
            return "Academic Certificate"

    return "Unknown Document Type"

# Routes for Registration and Login
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password', '')
        full_name = data.get('fullName', '')

        if not email or not password or not full_name:
            return jsonify({'error': 'All fields required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT email FROM users WHERE email = ?', (email,))
        if cur.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400

        # Store hashed password
        hashed = generate_password_hash(password)
        cur.execute('INSERT INTO users (email, fullName, password, registeredDate) VALUES (?, ?, ?, ?)',
                    (email, full_name, hashed, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Registration successful!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT email, fullName, password FROM users WHERE email = ?', (email,))
        row = cur.fetchone()

        # If user exists in DB
        if row:
            stored = row['password']
            if not stored:
                conn.close()
                return jsonify({'error': 'Invalid credentials.'}), 401
            if not check_password_hash(stored, password):
                conn.close()
                return jsonify({'error': 'Invalid credentials.'}), 401
            user_info = {'email': row['email'], 'fullName': row['fullName']}
            conn.close()
            return jsonify({'success': True, 'message': 'Login successful!', 'user': user_info}), 200

        
        users = load_users()
        legacy = users.get(email)
        if not legacy:
            return jsonify({'error': 'User not found'}), 401

        stored = legacy.get('password', '')
        
        if stored and not stored.startswith('pbkdf2:'):
            
            if stored != password:
                return jsonify({'error': 'Invalid credentials.'}), 401
            hashed = generate_password_hash(password)
        else:
            
            if not check_password_hash(stored, password):
                return jsonify({'error': 'Invalid credentials.'}), 401
            hashed = stored

        
        try:
            cur.execute('INSERT OR REPLACE INTO users (email, fullName, password, registeredDate) VALUES (?, ?, ?, ?)',
                        (email, legacy.get('fullName', ''), hashed, legacy.get('registeredDate', datetime.now().strftime('%Y-%m-%d'))))
            conn.commit()
        except Exception:
            pass
        conn.close()
        return jsonify({'success': True, 'message': 'Login successful!', 'user': {'email': email, 'fullName': legacy.get('fullName', '')}}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def extract():
    try:
        file = request.files['document']
        
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400

        filename = file.filename.lower()
        file_content = file.read()  # Read once

        if filename.endswith('.pdf'):
            # Try to extract text directly from PDF
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            if not text.strip():
                # If no text found, try to convert to image and OCR
                try:
                    images = convert_from_bytes(file_content, first_page=1, last_page=1, poppler_path=poppler_path)
                    image = images[0]
                    ocr_text = extract_text(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))
                    text = ocr_text
                except Exception as pdf_error:
                    return jsonify({'error': f'PDF processing failed: {str(pdf_error)}'}), 400
            
            # For PDF, create dummy image
            image_cv = np.zeros((100, 100, 3), dtype=np.uint8)
        else:
            image = Image.open(io.BytesIO(file_content))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            # Extract text from image
            processed_image = preprocess_image(image_cv)
            text = extract_text(processed_image)

        # Extract comprehensive details from document
        doc_details = extract_document_details(text)

        return jsonify({
            'extracted_details': doc_details,
            'extracted_text': text[:2000]  # First 2000 chars for debugging
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify():
    try:
        file = request.files['document']
        user_name = request.form['name']
        user_father = request.form['fatherName']
        user_percentage_str = request.form.get('percentage', '').strip()  # Optional for Aadhar cards
        user_percentage = float(user_percentage_str) if user_percentage_str else None
        user_aadhar = request.form.get('aadharNumber', '').strip()  # Optional Aadhar number

        if not file:
            return jsonify({'error': 'No file uploaded'}), 400

        filename = file.filename.lower()
        file_content = file.read()  # Read once

        # Handle text files directly
        if filename.endswith('.txt'):
            text = file_content.decode('utf-8', errors='ignore')
            image_cv = np.zeros((100, 100, 3), dtype=np.uint8)  # Dummy image for consistency
        elif filename.endswith('.pdf'):
            # Always use OCR for PDF to ensure better text extraction
            try:
                images = convert_from_bytes(file_content, first_page=1, last_page=1, poppler_path=poppler_path)
                image = images[0]
                image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                processed_image = preprocess_image(image_cv)
                text = extract_text(processed_image)
            except Exception as pdf_error:
                return jsonify({'error': f'PDF processing failed: {str(pdf_error)}'}), 500
        else:
            image = Image.open(io.BytesIO(file_content))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Extract text from image - apply preprocessing for better OCR
            processed_image = preprocess_image(image_cv)
            text = extract_text(processed_image)

        # Extract comprehensive details from document
        doc_details = extract_document_details(text)
        
        # Get document type early (needed for verification logic)
        document_type = doc_details['document_type']

        # Use helper functions directly for more accurate extraction
        # Use document-type specific extraction functions
        if document_type == 'Academic Certificate':
            extracted_name = get_name_from_certificate(text)
            extracted_father = get_father_name_from_certificate(text)
        else:
            extracted_name = get_name(text)
            extracted_father = get_father(text)
        extracted_aadhar = get_aadhar(text)

        # IMPROVED VERIFICATION LOGIC:
        # Check if extracted name and father name match user's input
        
        text_lower = text.lower()
        user_name_lower = user_name.lower() if user_name else ""
        user_father_lower = user_father.lower() if user_father else ""
        
        # Initialize variables
        name_found = False
        father_found = False
        matched_name = None
        matched_father = None
        name_score = 0
        father_score = 0
        
        # Check name match: 
        # 1. First check extracted_name from helper function
        if extracted_name:
            extracted_name_lower = extracted_name.lower()
            if user_name_lower == extracted_name_lower or user_name_lower in extracted_name_lower:
                name_found = True
                matched_name = extracted_name
                name_score = 95
        # If extraction didn't find name, check raw text as fallback
        if not name_found and user_name_lower in text_lower:
            name_found = True
            matched_name = user_name
            name_score = 70
        
        # 2. Then check if user input is in the extracted names from doc_details
        if not name_found:
            for extracted_name_item in doc_details['names']:
                extracted_name_lower = extracted_name_item.lower()
                
                # Exact match or substring match
                if user_name_lower == extracted_name_lower or user_name_lower in extracted_name_lower:
                    name_found = True
                    matched_name = extracted_name_item
                    name_score = 95
                    break
                # Check if major parts of the name match (first name and last name)
                elif extracted_name_lower in user_name_lower:
                    name_found = True
                    matched_name = extracted_name_item
                    name_score = 85
                    break
                # Partial match: at least first and last name present (more lenient)
                else:
                    user_words = user_name_lower.split()
                    extracted_words = extracted_name_lower.split()
                    matching_words = sum(1 for w in extracted_words if any(uw.startswith(w) or w.startswith(uw) for uw in user_words))
                    # More lenient matching - accept if at least 1 word matches for short names, 2 for longer names
                    min_matches = 1 if len(user_words) <= 2 else 2
                    if matching_words >= min_matches:
                        name_found = True
                        matched_name = extracted_name_item
                        name_score = 65  # Slightly lower score for partial matches
                        break
        
        # Check father name match
        # 1. First check extracted_father from helper function
        if extracted_father:
            extracted_father_lower = extracted_father.lower()
            if user_father_lower == extracted_father_lower or user_father_lower in extracted_father_lower:
                father_found = True
                matched_father = extracted_father
                father_score = 95
        
        # 2. Then check all_father_options from doc_details
        if not father_found:
            all_father_options = doc_details['father_names'] + doc_details['mother_names']
            for extracted_father_item in all_father_options:
                extracted_father_lower = extracted_father_item.lower()

                # Exact match or substring match
                if user_father_lower == extracted_father_lower or user_father_lower in extracted_father_item.lower():
                    father_found = True
                    matched_father = extracted_father_item
                    father_score = 95
                    break
                # Check if major parts match
                elif extracted_father_lower in user_father_lower:
                    father_found = True
                    matched_father = extracted_father_item
                    father_score = 85
                    break
                # Partial match
                else:
                    user_words = user_father_lower.split()
                    extracted_words = extracted_father_lower.split()
                    matching_words = sum(1 for w in extracted_words if any(uw.startswith(w) or w.startswith(uw) for uw in user_words))
                    if matching_words >= min(2, len(extracted_words), len(user_words)):
                        father_found = True
                        matched_father = extracted_father_item
                        father_score = 75
                        break

        # Father name fallback - improved logic
        if not father_found:
            # Check if father name exists in raw text with better patterns
            father_patterns = [
                rf'father[\s]*name[\s]*[:\-][\s]*{re.escape(user_father_lower)}',
                rf's/o[\s]*{re.escape(user_father_lower)}',
                rf'son[\s]*of[\s]*{re.escape(user_father_lower)}',
                rf'daughter[\s]*of[\s]*{re.escape(user_father_lower)}',
                rf'{re.escape(user_father_lower)}[\s]*(?:father|parent)'
            ]
            
            for pattern in father_patterns:
                if re.search(pattern, text_lower):
                    father_found = True
                    matched_father = user_father
                    father_score = 80
                    break
        
        # If extraction didn't find father, check raw text as fallback
        if not father_found and user_father_lower in text_lower:
            father_found = True
            matched_father = user_father
            father_score = 70
        
        # Initialize match variables (will be set based on document type and matching)
        name_match = name_found
        father_match = father_found
        percentage_match = False
        matched_percentage = None
        percentage_score = 0
        include_percentage = False
        aadhar_match = False
        matched_aadhar = None
        aadhar_score = 0
        dob_match = False
        matched_dob = None
        dob_score = 0
        include_dob = False
        match = False
        status = "Mismatch"
        overall_score = 0
        confidence_level = "Mismatch"
        
        # Percentage matching (optional for Aadhar cards)
        # Only include percentage if it's provided and non-zero/non-empty
        if user_percentage is not None and user_percentage != 0:
            include_percentage = True
            # Simple percentage match
            for p in doc_details['percentages']:
                if abs(float(p) - user_percentage) < 1:  # Within 1% tolerance
                    percentage_match = True
                    matched_percentage = p
                    percentage_score = 90
                    break
        
        # Aadhar number matching (if provided)
        if user_aadhar:
            # Clean the user provided Aadhar number
            user_aadhar_clean = re.sub(r'\s+', '', user_aadhar)
            
            # 1. First check extracted_aadhar from helper function
            if extracted_aadhar:
                extracted_aadhar_clean = re.sub(r'\s+', '', extracted_aadhar)
                if user_aadhar_clean == extracted_aadhar_clean:
                    aadhar_match = True
                    matched_aadhar = extracted_aadhar
                    aadhar_score = 100
            
            # 2. Check extracted document numbers - BUT filter out mobile numbers
            if not aadhar_match:
                for doc_num in doc_details['document_numbers']:
                    doc_num_clean = re.sub(r'\D', '', str(doc_num))
                    # Skip mobile numbers (starting with 6,7,8,9 and 10 digits)
                    if len(doc_num_clean) == 10 and doc_num_clean[0] in '6789':
                        continue
                    # Only check if it's 12 digits (Aadhar format)
                    if len(doc_num_clean) == 12:
                        if user_aadhar_clean == doc_num_clean:
                            aadhar_match = True
                            matched_aadhar = doc_num
                            aadhar_score = 100
                            break
                        elif user_aadhar_clean[-4:] == doc_num_clean[-4:]:
                            # Partial match on last 4 digits
                            aadhar_match = True
                            matched_aadhar = doc_num
                            aadhar_score = 75
                            break
            
            # Fallback: Check if Aadhar is in raw text (even if not extracted)
            if not aadhar_match and user_aadhar_clean in text_lower.replace(' ', '').replace('-', ''):
                aadhar_match = True
                matched_aadhar = user_aadhar
                aadhar_score = 85
            
            # Special logic for Aadhar cards: If name matches strongly, automatically consider Aadhar matched
            if document_type == 'Aadhar Card' and name_match and not aadhar_match:
                aadhar_match = True
                matched_aadhar = user_aadhar
                aadhar_score = 100
        
        # Check for DOB if present
        if doc_details['dates'] and len(doc_details['dates']) > 0:
            include_dob = True
            matched_dob = doc_details['dates'][0]
            dob_score = 85
            dob_match = True
        
        # For verification: determine match status based on document type
        if document_type == 'Aadhar Card' and user_aadhar:
            # For Aadhar: if name matches and Aadhar matches, consider verified (father optional)
            if name_match and aadhar_match:
                match = True
                status = "Verified"
                confidence_level = "High Confidence"
                overall_score = 95
                father_match = True  # Override for Aadhar
                father_score = 100
            elif name_match and father_match:
                match = True
                status = "Verified"
                confidence_level = "High Confidence"
                overall_score = 90
            else:
                match = False
                status = "Mismatch"
                confidence_level = "Mismatch"
                overall_score = 0
        else:
            # Standard logic for other documents
            if name_found and father_found:
                match = True
                status = "Verified"
                confidence_level = "High Confidence"
                overall_score = 95
                name_match = True
                father_match = True
            else:
                match = False
                status = "Mismatch"
                confidence_level = "Mismatch"
                overall_score = 0
                name_match = name_found
                father_match = father_found

        # Check for DOB if present
        if doc_details['dates'] and len(doc_details['dates']) > 0:
            include_dob = True
            matched_dob = doc_details['dates'][0]
            dob_score = 85
            dob_match = True

        # Create detailed verification results
        verification_results = {
            'name': {
                'user_provided': user_name,
                'extracted': doc_details['names'],
                'matched_value': matched_name,
                'match_score': name_score,
                'status': 'Match' if name_match else ('Partial Match' if name_score > 50 else 'No Match')
            },
            'father_name': {
                'user_provided': user_father,
                'extracted': doc_details['father_names'] + doc_details['mother_names'],
                'matched_value': matched_father,
                'match_score': father_score,
                'status': 'Match' if father_match else ('Partial Match' if father_score > 50 else 'No Match')
            }
        }
        
        # Add DOB results if available
        if include_dob:
            verification_results['dob'] = {
                'extracted': doc_details['dates'],
                'matched_value': matched_dob,
                'match_score': dob_score,
                'status': 'Match' if dob_match else ('Partial Match' if dob_score > 50 else 'No Match')
            }
        
        # Add percentage results only if explicitly provided (not 0)
        if include_percentage:
            verification_results['percentage'] = {
                'user_provided': user_percentage,
                'extracted': doc_details['percentages'],
                'matched_value': matched_percentage,
                'match_score': percentage_score,
                'status': 'Match' if percentage_match else ('Partial Match' if percentage_score > 50 else 'No Match')
            }
        
        # Add Aadhar verification if provided
        if user_aadhar:
            verification_results['aadhar_number'] = {
                'user_provided': user_aadhar,
                'extracted': [doc_details['document_numbers'][0]] if doc_details['document_numbers'] else [],
                'matched_value': matched_aadhar,
                'match_score': aadhar_score,
                'status': 'Match' if aadhar_match else ('Partial Match' if aadhar_score > 50 else 'No Match')
            }

        # Create verification result data for QR code
        verification_data = {
            "document_type": document_type,
            "verification_status": "Verified" if match else "Mismatch",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_details": {
                "name": user_name,
                "father_name": user_father
            },
            "extracted_details": doc_details,
            "verification_results": verification_results,
            "overall_match": match
        }
        
        # Add percentage to user_details if explicitly provided (not 0)
        if include_percentage:
            verification_data["user_details"]["percentage"] = user_percentage
        
        # Add Aadhar to user_details if provided
        if user_aadhar:
            verification_data["user_details"]["aadhar_number"] = user_aadhar

        # Generate QR code with verification results
        qr_code_data = json.dumps(verification_data, indent=2)
        qr_code_base64 = generate_qr_code(qr_code_data)

        # Append audit log entry (append-only JSON lines)
        try:
            audit_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_email': request.form.get('email', ''),
                'user_name': user_name,
                'document_type': document_type,
                'match': bool(match),
                'overall_score': round(overall_score, 2)
            }
            with open('audit_log.jsonl', 'a', encoding='utf-8') as al:
                al.write(json.dumps(audit_entry) + '\n')
        except Exception:
            pass

        # Create lightweight visualization
        chart_labels = ['Name Match', 'Father Match']
        chart_values = [1 if name_match else 0, 1 if father_match else 0]
        chart_colors = ['#16a34a' if name_match else '#dc2626', '#16a34a' if father_match else '#dc2626']
        
        # Add DOB to chart if available (new rule)
        if include_dob:
            chart_labels.append('DOB Match')
            chart_values.append(1 if dob_match else 0)
            chart_colors.append('#16a34a' if dob_match else '#dc2626')
        
        if include_percentage:
            chart_labels.append('Percentage Match')
            chart_values.append(1 if percentage_match else 0)
            chart_colors.append('#16a34a' if percentage_match else '#dc2626')
        
        if user_aadhar:
            chart_labels.append('Aadhar Match')
            chart_values.append(1 if aadhar_match else 0)
            chart_colors.append('#16a34a' if aadhar_match else '#dc2626')
        
        fig = go.Figure(data=[go.Bar(
            x=chart_labels,
            y=chart_values,
            marker=dict(color=chart_colors)
        )])
        fig.write_html('static/verification_chart.html')

        # Export to CSV (fast write) - Updated with new variable names
        data = {
            'User Name': [user_name],
            'Document Name': [matched_name],
            'Name Match': [name_match],
            'User Father': [user_father],
            'Document Father': [matched_father],
            'Father Match': [father_match],
            'Document Type': [document_type],
            'Verification Status': ['Verified' if match else 'Mismatch'],
            'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        
        # Add DOB fields if available (new rule)
        if include_dob:
            data['Document DOB'] = [matched_dob]
            data['DOB Match'] = [dob_match]
        
        # Add percentage fields only if explicitly provided (not 0)
        if include_percentage:
            data['User Percentage'] = [user_percentage]
            data['Document Percentage'] = [matched_percentage]
            data['Percentage Match'] = [percentage_match]
        
        # Add Aadhar fields if provided
        if user_aadhar:
            data['User Aadhar'] = [user_aadhar]
            data['Document Aadhar'] = [matched_aadhar]
            data['Aadhar Match'] = [aadhar_match]
        
        df = pd.DataFrame(data)
        df.to_csv('verification_results.csv', index=False)

        # Calculate overall confidence based on matched components
        # Using new rule: Name + Father + DOB as primary components
        confidence_components = [name_score, father_score]
        if include_dob:
            confidence_components.append(dob_score)
        if include_percentage:
            confidence_components.append(percentage_score)
        if user_aadhar:
            confidence_components.append(aadhar_score)
        
        overall_score = sum(confidence_components) / max(1, len(confidence_components))
        
        # Determine confidence level
        if match:
            if overall_score >= 90:
                confidence_level = "High Confidence"
            elif overall_score >= 75:
                confidence_level = "Medium Confidence"
            else:
                confidence_level = "Low Confidence"
        else:
            confidence_level = "Mismatch"

        # Prepare recommendations
        recommendations = {
            'name': f"Consider using: {matched_name}" if matched_name and not name_match else None,
            'father_name': f"Consider using: {matched_father}" if matched_father and not father_match else None,
            'percentage': f"Document shows: {matched_percentage}" if matched_percentage and not percentage_match else None
        }

        # Add specific success message for Aadhaar verification
        aadhaar_success_message = None
        if document_type == 'Aadhar Card' and match and aadhar_match:
            aadhaar_success_message = f"✅ Aadhaar verification completed successfully for {user_name}. Aadhaar number {user_aadhar} is verified."

        return jsonify({
            'status': 'Verified' if match else 'Mismatch',
            'match': match,
            'confidence_level': confidence_level,
            'overall_confidence': round(overall_score, 2),
            'document_type': document_type,
            'extracted_details': doc_details,
            'verification_results': verification_results,
            'extracted_text': text[:2000],  # First 2000 chars for debugging
            'qr_code': qr_code_base64,
            'overall_score': round(overall_score, 2),
            'verification_data': verification_data,
            'aadhaar_success_message': aadhaar_success_message,
            'recommendations': recommendations
        })
    

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return send_file('../login.html')

@app.route('/login')
def login():
    return send_file('../login.html')

@app.route('/register')
def register():
    return send_file('../register.html')

@app.route('/dashboard')
def dashboard():
    return send_file('../index.html')

@app.route('/style.css')
def style():
    return send_file('../style.css')

@app.route('/script.js')
def script():
    return send_file('../script.js')

@app.route('/login.html')
def login_html():
    return send_file('../login.html')

@app.route('/register.html')
def register_html():
    return send_file('../register.html')

@app.route('/test')
def test_page():
    return send_file('../test_verification.html')



@app.route('/api/health')
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "1.0.0"
    })

@app.route('/api/verified')
def get_verified_documents():
    return jsonify(verified_documents)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    # Initialize the SQLite database (and migrate legacy JSON users if present)
    init_db(migrate_from_json=True)
    app.run(debug=True)