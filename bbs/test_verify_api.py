import requests
from io import BytesIO
import json

# Test the verification API with the test file
url = 'http://127.0.0.1:5000/api/verify'

# Read the test file
with open('test_aadhar_satyajit.txt', 'rb') as f:
    file_content = f.read()

files = {'document': ('test_aadhar_satyajit.txt', BytesIO(file_content), 'text/plain')}
data = {
    'name': 'Satyajit Dutta',
    'fatherName': 'Rajesh Kumar Dutta',
    'percentage': '0'
}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    print('API Response:')
    print(f'Status: {response.status_code}')

    if response.status_code == 200:
        result = response.json()
        print(f'\n=== Overall Verification ===')
        print(f'Document Type: {result.get("document_type", "Unknown")}')
        print(f'Verification Status: {result.get("status", "Unknown")}')
        print(f'Overall Match: {result.get("match", False)}')

        if 'verification_results' in result:
            print(f'\n=== Name Verification ===')
            name_result = result['verification_results']['name']
            print(f'User Provided: {name_result.get("user_provided", "N/A")}')
            print(f'Name Status: {name_result.get("status", "Unknown")}')
            print(f'Name Match Score: {name_result.get("match_score", 0)}%')
            print(f'Best Match: {name_result.get("matched_value", "None")}')
            
            print(f'\n=== Father Name Verification ===')
            father_result = result['verification_results']['father_name']
            print(f'User Provided: {father_result.get("user_provided", "N/A")}')
            print(f'Father Status: {father_result.get("status", "Unknown")}')
            print(f'Father Match Score: {father_result.get("match_score", 0)}%')
            print(f'Best Match: {father_result.get("matched_value", "None")}')

        if 'extracted_details' in result:
            print(f'\n=== Extracted Details ===')
            print(f'All Names Found: {result["extracted_details"].get("names", [])[:5]}...')
            print(f'All Father Names Found: {result["extracted_details"].get("father_names", [])}')
    else:
        print(f'Error Response: {response.text}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()