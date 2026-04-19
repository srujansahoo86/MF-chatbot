import requests
import json

url = "http://localhost:8004/api/chat"
payload = {"query": "List all the mutual funds you have data for."}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print("STATUS CODE:", response.status_code)
    print("RESPONSE:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("ERROR:", e)
