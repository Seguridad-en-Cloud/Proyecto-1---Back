import urllib.request
import json

url = "https://34-96-107-81.nip.io/api/v1/auth/register"
data = json.dumps({"email": "newtest2@test.com", "password": "New12345!"}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print("STATUS:", response.status)
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print("STATUS:", e.code)
    print(e.read().decode())
except Exception as e:
    print("ERROR:", e)
