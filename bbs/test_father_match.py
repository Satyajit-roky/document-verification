import requests
from io import BytesIO

# Test the verification API
url = 'http://127.0.0.1:5000/api/verify'

with open('test_aadhar_satyajit.txt', 'rb') as f:
    file_content = f.read()

files = {
    'document': ('test_aadhar_satyajit.txt', BytesIO(file_content), 'text/plain')
}

data = {
    'name': 'Satyajit Dutta',
    'fatherName': 'Sushanta Kumar Dutta',
    'percentage': '0',
    'aadharNumber': '123456789012'
}

response = requests.post(url, files=files, data=data, timeout=30)

if response.status_code == 200:
    result = response.json()
    print("Status:", result.get('status'))
    print("Document:", result.get('document_type'))
    print("Match:", result.get('match'))

    if 'verification_results' in result:
        vr = result['verification_results']
        print("\nVerification Results:")

        if 'father_name' in vr:
            f = vr['father_name']
            print(f"Father - User: {f.get('user_provided')}, Extracted: {f.get('extracted')}, Matched: {f.get('matched_value')}, Score: {f.get('match_score')}%, Status: {f.get('status')}")
else:
    print("Error:", response.status_code)
    print(response.text)