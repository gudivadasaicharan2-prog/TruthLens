import requests

url = "http://localhost:8000/api/v1/image/analyze"
file_path = r"c:\Users\LENOVO\Downloads\TruthLensProject\truthlens\backend\benchmark\human\00cce8739597467db0bef7bff2c8ef25.jpg"

with open(file_path, 'rb') as f:
    files = {'file': ('test.jpg', f, 'image/jpeg')}
    response = requests.post(url, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
