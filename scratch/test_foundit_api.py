from curl_cffi import requests
import json

headers = {
    'authority': 'www.foundit.in',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.foundit.in',
    'referer': 'https://www.foundit.in/srp/results?query=Python&locations=Bangalore',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

endpoints = [
    'https://www.foundit.in/middleware/jobsearch?query=Python&locations=Bangalore&limit=15&start=0',
    'https://www.foundit.in/api/jobsearch?query=Python&locations=Bangalore',
    'https://www.foundit.in/srp/api/results?query=Python&locations=Bangalore',
    'https://www.foundit.in/middleware/v2/jobsearch?query=Python&locations=Bangalore&limit=15&start=0'
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=headers, impersonate='chrome120', timeout=10)
        print(f"{ep[:60]}: status {r.status_code}, len {len(r.text)}")
        if r.status_code == 200:
            print("Foundit API Response:", r.text[:200])
    except Exception as e:
        print("Err:", e)
