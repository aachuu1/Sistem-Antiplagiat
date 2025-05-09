import os
import requests

url = 'http://localhost:5000/upload' 

folder_path = './documente'  

files = []
for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        filepath = os.path.join(folder_path, filename)
        files.append(('files', (filename, open(filepath, 'rb'), 'text/plain')))

response = requests.post(url, files=files)

print(response.status_code)
print(response.json())
