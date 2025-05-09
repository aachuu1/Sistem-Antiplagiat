import os, requests

url = 'http://localhost:5000/upload'
folder = './documente'

files = [
    ('files', (fname, open(os.path.join(folder, fname), 'rb'), 'text/plain'))
    for fname in os.listdir(folder) if fname.endswith('.txt')
]

resp = requests.post(url, files=files)
print(resp.status_code, resp.json())
