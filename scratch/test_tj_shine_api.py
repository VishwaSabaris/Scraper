import requests
import json
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://www.timesjobs.com',
    'Referer': 'https://www.timesjobs.com/',
}

print("=== Testing TimesJobs API ===")
try:
    url = "https://tjapi.timesjobs.com/search/api/v1/search/jobs/list"
    payload = {
        "txtKeywords": "python",
        "txtLocation": "bangalore",
        "page": 1,
        "pageSize": 25
    }
    # Test GET and POST
    r = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
    print("TimesJobs POST status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Timesjobs JSON keys:", list(data.keys()))
        if 'data' in data:
            print("Timesjobs data keys:", list(data['data'].keys()) if isinstance(data['data'], dict) else len(data['data']))
    else:
        # Try GET
        r2 = requests.get(url + "?txtKeywords=python&txtLocation=bangalore&page=1", headers=headers, verify=False, timeout=10)
        print("TimesJobs GET status:", r2.status_code)
        if r2.status_code == 200:
            print("Timesjobs GET data keys:", list(r2.json().keys()))
except Exception as e:
    print("TimesJobs API err:", e)

print("\n=== Testing Shine API ===")
try:
    shine_url = "https://www.shine.com/api/v2/search/simple/?q=python-jobs-in-bangalore&loc=bangalore"
    r = requests.get(shine_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
    print("Shine API status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Shine API keys:", list(data.keys()) if isinstance(data, dict) else len(data))
        if isinstance(data, dict) and 'jobData' in data:
            print("Shine jobData count:", len(data['jobData']))
            if data['jobData']:
                print("Sample shine job:", data['jobData'][0].get('job_title'), "|", data['jobData'][0].get('company_name'))
except Exception as e:
    print("Shine API err:", e)
