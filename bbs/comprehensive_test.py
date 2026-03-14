import requests
from io import BytesIO
import json

print("=" * 60)
print("Testing Enhanced Document Verification System")
print("=" * 60)

# Test data samples
test_cases = [
    {
        'name': 'Satyajit Dutta (Aadhar)',
        'file': 'test_aadhar_satyajit.txt',
        'user_name': 'Satyajit Dutta',
        'user_father': 'Rajesh Kumar Dutta',
        'user_percentage': '0'
    },
    {
        'name': 'Priya Sharma (Aadhar)',
        'file': 'sample_aadhar_priya.txt',
        'user_name': 'Priya Sharma',
        'user_father': 'Vikram Sharma',
        'user_percentage': '0'
    },
    {
        'name': 'Arjun Singh (Aadhar)',
        'file': 'sample_aadhar_arjun.txt',
        'user_name': 'Arjun Kumar Singh',
        'user_father': 'Rajendra Singh',
        'user_percentage': '0'
    },
    {
        'name': 'Anisha Patel (Marksheet)',
        'file': 'sample_marksheet_anisha.txt',
        'user_name': 'Anisha Patel',
        'user_father': 'Ramesh Kumar Patel',
        'user_percentage': '87.43'
    },
    {
        'name': 'Rohan Verma (Marksheet)',
        'file': 'sample_marksheet_rohan.txt',
        'user_name': 'Rohan Verma',
        'user_father': 'Suresh Kumar Verma',
        'user_percentage': '86.67'
    }
]

url = 'http://127.0.0.1:5000/api/verify'

for test_case in test_cases:
    print(f"\n--- Testing: {test_case['name']} ---")
    
    try:
        # Read the test file
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
            'percentage': test_case['user_percentage']
        }

        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {result.get('status', 'Unknown')}")
            print(f"📄 Document Type: {result.get('document_type', 'Unknown')}")
            print(f"🔍 Overall Match: {result.get('match', False)}")
            
            if 'verification_results' in result:
                vr = result['verification_results']
                
                # Name verification
                if 'name' in vr:
                    name_data = vr['name']
                    print(f"\n  👤 Name Verification:")
                    print(f"     You provided: {name_data.get('user_provided', 'N/A')}")
                    print(f"     Found: {name_data.get('matched_value', 'N/A')}")
                    print(f"     Match: {name_data.get('status', 'Unknown')} ({name_data.get('match_score', 0)}%)")
                
                # Father name verification
                if 'father_name' in vr:
                    father_data = vr['father_name']
                    print(f"\n  👨 Father Name Verification:")
                    print(f"     You provided: {father_data.get('user_provided', 'N/A')}")
                    print(f"     Found: {father_data.get('matched_value', 'N/A')}")
                    print(f"     Match: {father_data.get('status', 'Unknown')} ({father_data.get('match_score', 0)}%)")
                
                # Percentage verification (if applicable)
                if 'percentage' in vr:
                    pct_data = vr['percentage']
                    print(f"\n  📊 Percentage Verification:")
                    print(f"     You provided: {pct_data.get('user_provided', 'N/A')}%")
                    print(f"     Found: {pct_data.get('matched_value', 'N/A')}%")
                    print(f"     Match: {pct_data.get('status', 'Unknown')} ({pct_data.get('match_score', 0)}%)")
            
            print("\n✅ Test Passed!")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
    
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")

# Test verified documents list
print("\n" + "=" * 60)
print("Testing Verified Documents List")
print("=" * 60)

try:
    response = requests.get('http://127.0.0.1:5000/api/verified', timeout=10)
    if response.status_code == 200:
        docs = response.json()
        print(f"\n📋 Total Verified Documents: {len(docs)}")
        
        for doc in docs[:3]:  # Show first 3
            print(f"\n  ID: {doc.get('id', 'N/A')}")
            print(f"  Name: {doc.get('name', 'N/A')} (Provided: {doc.get('user_provided_name', 'N/A')})")
            print(f"  Father: {doc.get('father_name', 'N/A')} (Provided: {doc.get('user_provided_father', 'N/A')})")
            print(f"  Type: {doc.get('document_type', 'Unknown')}")
            print(f"  Scores: Name={doc.get('name_match_score', 'N/A')}% | Father={doc.get('father_match_score', 'N/A')}% | Overall={doc.get('overall_match_score', 'N/A')}%")
            print(f"  Date: {doc.get('date', 'N/A')}")
except Exception as e:
    print(f"Error: {str(e)}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)