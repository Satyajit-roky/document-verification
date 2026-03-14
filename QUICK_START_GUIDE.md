# Quick Start Guide - Enhanced Document Verification

## 🚀 Getting Started

### Step 1: Start the Server

```bash
cd bbs
python app.py
```

Server will run at: `http://127.0.0.1:5000`

### Step 2: Open Application

Visit `http://127.0.0.1:5000` in your web browser

### Step 3: Choose Document Type

Select one of:

- 🆔 **Aadhar Card** - Government ID
- 🛂 **Passport** - Travel document
- 🚗 **Driving License** - Driving permit
- 📜 **Certificate** - Educational document

## 📝 Quick Reference: What to Provide

### For Aadhar Cards

```
✓ Your Full Name:     Satyajit Dutta
✓ Father's Name:      Rajesh Kumar Dutta
✗ Percentage:         NOT REQUIRED (leave empty)
✓ Upload Document:    PDF or clear photo
```

### For Marksheets/Certificates

```
✓ Student Name:       Anisha Patel
✓ Father's Name:      Ramesh Kumar Patel
✓ Percentage/Score:   87.43
✓ Upload Document:    PDF or clear photo
```

### For Passports

```
✓ Full Name:          [As in passport]
✓ Father's Name:      [If applicable]
✗ Percentage:         NOT REQUIRED
✓ Upload Document:    Scanned passport
```

## ✅ Expected Results

### Perfect Match Example (100%)

```
You Provide:        Satyajit Dutta
Document Shows:     Satyajit Dutta
Result:            ✅ MATCH (100%)
Status:            VERIFIED
```

### Good Match Example (90%+)

```
You Provide:        Arjun Kumar Singh
Document Shows:     Arjun Kumar Singh (Father Name in that line)
Result:            ✅ GOOD MATCH (90%)
Status:            VERIFIED
```

### Partial Match (70-85%)

```
You Provide:        Rohan Verma
Document Shows:     Rohan Verma Son of...
Result:            ⚠️ PARTIAL MATCH (85%)
Status:            VERIFIED (acceptable)
```

## 🧪 Test with Samples

### Ready-to-Test Files:

1. **Aadhar - Satyajit Dutta**
   - File: `sample_aadhar_satyajit.txt`
   - Name: Satyajit Dutta
   - Father: Rajesh Kumar Dutta
   - ✅ Guaranteed: 100% match

2. **Aadhar - Priya Sharma**
   - File: `sample_aadhar_priya.txt`
   - Name: Priya Sharma
   - Father: Vikram Sharma
   - ✅ Expected: 90%+ match

3. **Marksheet - Anisha Patel**
   - File: `sample_marksheet_anisha.txt`
   - Name: Anisha Patel
   - Father: Ramesh Kumar Patel
   - Percentage: 87.43
   - ✅ Expected: 90%+ on all fields

4. **Marksheet - Rohan Verma**
   - File: `sample_marksheet_rohan.txt`
   - Name: Rohan Verma
   - Father: Suresh Kumar Verma
   - Percentage: 86.67
   - ✅ Expected: 90%+ on all fields

## 📊 Understanding the Results

### Verification Report Shows:

```
┌─ Name Verification ────────────────────────┐
│ You Provided:    Satyajit Dutta            │
│ Found in Doc:    Satyajit Dutta            │
│ Match Score:     100%                      │
│ Status:          ✅ MATCH                   │
└────────────────────────────────────────────┘

┌─ Father Name Verification ─────────────────┐
│ You Provided:    Rajesh Kumar Dutta        │
│ Found in Doc:    Rajesh Kumar Dutta        │
│ Match Score:     100%                      │
│ Status:          ✅ MATCH                   │
└────────────────────────────────────────────┘

┌─ Overall Result ───────────────────────────┐
│ Status:          ✅ VERIFIED                │
│ Confidence:      100%                      │
│ Document Type:   Aadhar Card               │
└────────────────────────────────────────────┘
```

## 🔍 Verified Documents List

After verification, your document appears in the "Verified Documents" section showing:

| Field         | Example            |
| ------------- | ------------------ |
| ID            | 3                  |
| Name          | Satyajit Dutta     |
| Father Name   | Rajesh Kumar Dutta |
| Document Type | Aadhar Card        |
| Name Match    | 100%               |
| Father Match  | 100%               |
| Overall Score | 100%               |
| Status        | ✅ Verified        |
| Date          | 2026-02-17         |

## 💡 Pro Tips

### 1. Use Exact Spelling

Best results when you use exact spelling from your document

### 2. Clear Documents

Better quality scans = better OCR = better accuracy

### 3. Complete Information

Provide full names, not abbreviations

### 4. Check "Verified Documents"

View all verified documents with scores to track history

### 5. No Exact Match Needed

System accepts 70%+ matches, so minor variations are OK

## ⚡ Quick Test Sequence

1. **Test 1: Exact Match (Baseline)**
   - Use: `Satyajit Dutta` with `sample_aadhar_satyajit.txt`
   - Expected: 100% match
   - Purpose: Verify system is working

2. **Test 2: Acceptable Variation**
   - Use: `Arjun Kumar Singh` with `sample_aadhar_arjun.txt`
   - Expected: 90% match
   - Purpose: Confirm flexibility works

3. **Test 3: Marksheet**
   - Use: `Anisha Patel` (87.43%) with `sample_marksheet_anisha.txt`
   - Expected: 90%+ on all fields
   - Purpose: Test multi-field verification

4. **Test 4: Your Own Document**
   - Use: Your own document and data
   - Expected: Varies
   - Purpose: Real-world testing

## 🎯 Success Indicators

✅ **System is Working When:**

- Document type is correctly identified
- Names appear in the extraction
- Match scores are calculated
- Document appears in verified list

⚠️ **Check These If Issues:**

- Is Flask server running? (Check terminal)
- Is document file readable?
- Is provided data matching document content?
- Try with sample documents first

## 📞 Support Information

For issues:

1. Check logs in Flask terminal
2. Verify document quality
3. Try with sample documents
4. Check provided data accuracy

## 🔗 Key Files

- **Main App**: `bbs/app.py`
- **Web Interface**: `index.html`
- **JavaScript**: `script.js`
- **Styles**: `style.css`
- **Samples**: `sample_aadhar_*.txt`, `sample_marksheet_*.txt`
- **Guides**: `VERIFICATION_FEATURES.md`, `SAMPLE_DOCUMENTS_GUIDE.md`

---

**Start verifying:** Visit `http://127.0.0.1:5000` 🚀
