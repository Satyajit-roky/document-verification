# Sample Documents Reference Guide

## Quick Reference

### Aadhar Cards

These files contain Aadhar card data for testing the verification system:

| File                       | Name              | Father             | Aadhar         | Status      |
| -------------------------- | ----------------- | ------------------ | -------------- | ----------- |
| `test_aadhar_satyajit.txt` | Satyajit Dutta    | Rajesh Kumar Dutta | 1234 5678 9012 | ✅ Verified |
| `sample_aadhar_priya.txt`  | Priya Sharma      | Vikram Sharma      | 5678 9012 3456 | ✅ Verified |
| `sample_aadhar_arjun.txt`  | Arjun Kumar Singh | Rajendra Singh     | 1111 2222 3333 | ✅ Verified |

### Marksheets/Certificates

These files contain marksheet/certificate data for testing:

| File                          | Name         | Father             | Percentage | Grade | Status      |
| ----------------------------- | ------------ | ------------------ | ---------- | ----- | ----------- |
| `sample_marksheet_anisha.txt` | Anisha Patel | Ramesh Kumar Patel | 87.43%     | A+    | ✅ Verified |
| `sample_marksheet_rohan.txt`  | Rohan Verma  | Suresh Kumar Verma | 86.67%     | A     | ✅ Verified |

## How to Test Each Document

### Test 1: Aadhar Card - Satyajit Dutta

```
1. Select Document Type: Aadhar Card
2. Name: Satyajit Dutta
3. Father's Name: Rajesh Kumar Dutta
4. Leave Percentage empty
5. Upload: test_aadhar_satyajit.txt
6. Expected: ✅ Verified (100% name, 100% father)
```

### Test 2: Aadhar Card - Priya Sharma

```
1. Select Document Type: Aadhar Card
2. Name: Priya Sharma
3. Father's Name: Vikram Sharma
4. Leave Percentage empty
5. Upload: sample_aadhar_priya.txt
6. Expected: ✅ Verified (90%+ match)
```

### Test 3: Aadhar Card - Arjun Singh

```
1. Select Document Type: Aadhar Card
2. Name: Arjun Kumar Singh
3. Father's Name: Rajendra Singh
4. Leave Percentage empty
5. Upload: sample_aadhar_arjun.txt
6. Expected: ✅ Verified (90%+ match)
```

### Test 4: Marksheet - Anisha Patel

```
1. Select Document Type: Certificate
2. Name: Anisha Patel
3. Father's Name: Ramesh Kumar Patel
4. Percentage: 87.43
5. Upload: sample_marksheet_anisha.txt
6. Expected: ✅ Verified (100% all fields)
```

### Test 5: Marksheet - Rohan Verma

```
1. Select Document Type: Certificate
2. Name: Rohan Verma
3. Father's Name: Suresh Kumar Verma
4. Percentage: 86.67
5. Upload: sample_marksheet_rohan.txt
6. Expected: ✅ Verified (90%+ match on all fields)
```

## Document Field Details

### Aadhar Cards Include:

- Full Name (in English)
- Father's Name
- Date of Birth
- Gender
- Aadhar Number (12 digits)
- Address
- Mobile Number
- Issue and Validity Dates

### Marksheets Include:

- Student Name
- Father's Name
- Mother's Name (optional)
- Class/Grade Level
- Subject-wise Scores
- Total Marks and Percentage
- Grade/Result
- Roll Number
- School/Board Information

## Accuracy Expectations

### Expected Match Scores

**Exact Matches (100%)**

- When you provide: Satyajit Dutta
- Document contains: Satyajit Dutta
- Score: 100%

**Close Matches (85-95%)**

- When you provide: Arjun Kumar Singh
- Document contains: Arjun Kumar Singh Father
- Score: 90-95%

**Name with Father Name Issues (70-85%)**

- When you provide: Rohan Verma
- Document contains: Rohan Verma Son
- Score: 80-90%

## Fields That Support Flexibility

### Name Field:

- ✅ Accepts partial matches
- ✅ Ignores extra suffixes like "Father", "Son", "Daughter"
- ✅ Case-insensitive matching
- ✅ Handles spelling variations

### Father Name Field:

- ✅ Accepts "Father's Name:", "c/o", "s/o" patterns
- ✅ Partial matches allowed
- ✅ Handles extra words or additions

### Percentage Field:

- ✅ Exact or very close matches required (within 0.5%)
- ✅ Only required for marksheets/certificates
- ✅ Can be omitted for Aadhar cards

## Verification Workflow

1. **Document Upload** → OCR extracts text
2. **Text Analysis** → System identifies document type and fields
3. **Name Extraction** → Finds all names in document
4. **Father Name Extraction** → Looks for father/parent names
5. **Smart Matching** → Compares your provided data with extracted data
6. **Score Calculation** → Calculates accuracy percentage
7. **Results Display** → Shows matches with accuracy percentages
8. **Record Storage** → Saves to verified documents list with all details

## Tips for Best Results

1. **Exact Spelling**: Use the exact spelling from your document for best accuracy
2. **Full Names**: Include middle names when available
3. **Complete Father Name**: Provide father's full name, not just first name
4. **Correct Percentage**: For marksheets, use the exact percentage shown
5. **Clear Documents**: Use clear, high-quality scans/images for OCR accuracy

## Troubleshooting

### Issue: "No Match" even with correct details

**Solution**: The document text might be formatted differently. Check:

- Extra spaces or line breaks
- Different spelling (e.g., "Kumar" vs "Kumar ")
- OCR extraction errors (common with poor quality scans)
- Try uploading a clearer version

### Issue: Percentage shows 0% match

**Solution**: Make sure you're providing the exact percentage shown in the document

### Issue: Father name not found

**Solution**: Document might use "c/o" or "s/o" instead of "Father's Name:"

## Next Steps

- Upload your own documents (Aadhar cards, certificates, marksheets)
- System will automatically detect document type
- Compare with the provided samples to understand expected accuracy
- View verified documents list to see all successful verifications
