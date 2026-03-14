import requests
from io import BytesIO

print("="*60)
print("Testing Enhanced Document Verification")
print("="*60)

# Test cases
test_cases = [
    {
        'name': 'Satyajit Dutta (Aadhar)',
        'file': 'test_aadhar_satyajit.txt',
        'user_name': 'Satyajit Dutta',
        'user_father': 'Rajesh Kumar Dutta',
        'user_percentage': '0',
        'user_aadhar': '123456789012'
    },
    {
        'name': 'Priya Sharma (Aadhar)',
        'file': 'sample_aadhar_priya.txt',
        'user_name': 'Priya Sharma',
        'user_father': 'Vikram Sharma',
        'user_percentage': '0',
        'user_aadhar': '987654321098'
    },
    {
        'name': 'John Smith (Certificate)',
        'file': 'test_certificate.txt',
        'user_name': 'John Smith',
        'user_father': 'Robert Smith',
        'user_percentage': '85.5',
        'user_aadhar': ''
    }
]

url = 'http://127.0.0.1:5000/api/verify'

for test_case in test_cases:
    print("\nTesting: " + test_case['name'])
    print("-"*60)
    
    try:
        with open(test_case['file'], 'rb') as f:
            file_content = f.read()

        files = {
            'document': (
                test_case['file'],
                BytesIO(file_content),
                'text/plain'
            )
        }
        
        data = {
            'name': test_case['user_name'],
            'fatherName': test_case['user_father'],
            'percentage': test_case['user_percentage'],
            'aadharNumber': test_case.get('user_aadhar', '')
        }

        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("Status: " + result.get('status', 'Unknown'))
            print("Document: " + result.get('document_type', 'Unknown'))
            print("Match: " + str(result.get('match', False)))
            
            if 'verification_results' in result:
                vr = result['verification_results']
                if 'name' in vr:
                    n = vr['name']
                    print("Name: Found=" + str(n.get('matched_value')) + " Score=" + str(n.get('match_score')) + "%")
                
                if 'father_name' in vr:
                    f = vr['father_name']
                    print("Father: Found=" + str(f.get('matched_value')) + " Score=" + str(f.get('match_score')) + "%")
            
            print("PASSED")
        else:
            print("ERROR: " + str(response.status_code))
    
    except Exception as e:
        print("FAILED: " + str(e))

# Check verified list
print("\n" + "="*60)
print("Verified Documents List")
print("="*60)

try:
    response = requests.get('http://127.0.0.1:5000/api/verified', timeout=10)
    if response.status_code == 200:
        docs = response.json()
        print("Total: " + str(len(docs)))
        
        for doc in docs[-2:]:
            print("\nID: " + str(doc.get('id')))
            print("Name: " + str(doc.get('name')))
            print("Father: " + str(doc.get('father_name')))
            print("Type: " + str(doc.get('document_type')))
            print("Scores: Name=" + str(doc.get('name_match_score')) + "% Father=" + str(doc.get('father_match_score')) + "% Overall=" + str(doc.get('overall_match_score')) + "%")
except Exception as e:
    print("Error: " + str(e))

print("\nDone!")