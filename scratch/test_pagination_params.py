import requests

base_url = "https://himalayas.app/jobs/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

print("=== Testing page parameter ===")
for p in range(1, 4):
    url = f"{base_url}?q=Software+Development&country=United+Kingdom&page={p}"
    r = requests.get(url, headers=headers).json()
    jobs = r.get("jobs", [])
    print(f"Page {p}: count={len(jobs)}")
    if jobs:
        print(f"  First job: {jobs[0]['title']} | Guid: {jobs[0]['guid']}")
        print(f"  Last job:  {jobs[-1]['title']} | Guid: {jobs[-1]['guid']}")

print("\n=== Testing offset parameter with different values ===")
for off in [0, 20, 40]:
    url = f"{base_url}?q=Software+Development&country=United+Kingdom&offset={off}"
    r = requests.get(url, headers=headers).json()
    jobs = r.get("jobs", [])
    print(f"Offset {off}: count={len(jobs)}")
    if jobs:
        print(f"  First job: {jobs[0]['title']} | Guid: {jobs[0]['guid']}")

print("\n=== Testing offset & limit on /jobs/api (browse endpoint) ===")
for off in [0, 20, 40]:
    url = f"https://himalayas.app/jobs/api?offset={off}&limit=20"
    r = requests.get(url, headers=headers).json()
    jobs = r.get("jobs", [])
    print(f"Browse Offset {off}: count={len(jobs)}")
    if jobs:
        print(f"  First job: {jobs[0]['title']} | Guid: {jobs[0]['guid']}")

