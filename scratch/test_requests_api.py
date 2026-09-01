import requests

url = "https://himalayas.app/jobs/api/search?q=Software+Development&country=United+Kingdom"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print("Status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Success! Jobs count:", len(data.get("jobs", [])))
        print("Keys:", list(data.keys()))
        print("Offset:", data.get("offset"), "Limit:", data.get("limit"))
    else:
        print("Response text:", resp.text[:200])
except Exception as e:
    print("Error:", e)
