# Universal Document Verification Test Cases

This file contains test cases to verify that the improved document verification system works for every type of Aadhaar card and certificate.

## Test Case 1: Standard Aadhaar Card
Name: Raj Kumar Sharma
Father: Om Prakash Sharma
Aadhar: 2341 5678 9012
Content: 
```
GOVERNMENT OF INDIA
Aadhaar Card
Raj Kumar Sharma
S/O Om Prakash Sharma
2341 5678 9012
Date of Birth: 15/08/1990
Male
```

## Test Case 2: Regional Language Aadhaar
Name: ସତ୍ୟଜିତ କୁମାର
Father: ରମେଶ କୁମାର
Aadhar: 3456 7890 1234
Content:
```
ଆଧାର କାର୍ଡ
ସତ୍ୟଜିତ କୁମାର
S/O ରମେଶ କୁମାର
3456 7890 1234
```

## Test Case 3: Academic Certificate
Name: Priya Singh
Father: Rajendra Singh
Percentage: 85.5
Content:
```
CENTRAL BOARD OF SECONDARY EDUCATION
ACADEMIC CERTIFICATE

Certified that Priya Singh daughter of Rajendra Singh
has successfully completed the course
Secured: 85.5% marks
Date: 15/03/2023
```

## Test Case 4: Marksheet
Name: Amit Kumar
Father: Suresh Kumar
Percentage: 78.2
Content:
```
BOARD OF INTERMEDIATE EDUCATION
MARKSHEET

Student Name: Amit Kumar
Father Name: Suresh Kumar
Total Marks: 78.2%
```

## Test Case 5: Certificate with Different Format
Name: Anjali Mehta
Father: Ramesh Mehta
Percentage: 92.0
Content:
```
UNIVERSITY CERTIFICATE

This is to certify that Anjali Mehta
daughter of Ramesh Mehta
has passed with distinction
Percentage: 92.0%
```

## Test Case 6: Minimal Information Certificate
Name: Rahul Verma
Father: Late Shri K. Verma
Content:
```
CERTIFICATE OF COMPLETION

Rahul Verma
Son of Late Shri K. Verma
has completed the program
```

## Test Case 7: Poor Quality OCR Simulation
Name: JohnDoe
Father: PeterDoe
Aadhar: 123456789012
Content:
```
A4DH44R C44RD
J0hn D0e
S/0 Peter D0e
1234 5678 9012
```

## Expected Results:
- All test cases should be properly detected as their respective document types
- Name matching should work with various formats (exact, partial, OCR errors)
- Father name matching should handle S/O, Son of, Daughter of patterns
- Aadhaar number detection should work with different spacing formats
- Percentage extraction should handle various formats
- The system should provide appropriate confidence levels for each match
