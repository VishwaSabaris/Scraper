import requests

base_url = "https://himalayas.app/jobs/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Test offset / limit vs page
print("--- Testing offset=0, limit=20 ---")
res0 = requests.get(f"{base_url}?q=Software+Development&country=United+Kingdom&limit=20&offset=0", headers=headers).json()
print("Offset 0 count:", len(res0.get("jobs", [])))
if res0.get("jobs"):
    print("First job title (offset 0):", res0["jobs"][0]["title"])
    print("Last job title (offset 0):", res0["jobs"][-1]["title"])

print("\n--- Testing offset=20, limit=20 ---")
res1 = requests.get(f"{base_url}?q=Software+Development&country=United+Kingdom&limit=20&offset=20", headers=headers).json()
print("Offset 20 count:", len(res1.get("jobs", [])))
if res1.get("jobs"):
    print("First job title (offset 20):", res1["jobs"][0]["title"])

print("\n--- Testing limit=50 ---")
res_limit50 = requests.get(f"{base_url}?q=Software+Development&country=United+Kingdom&limit=50&offset=0", headers=headers).json()
print("Limit 50 count:", len(res_limit50.get("jobs", [])))

print("\n--- Testing without country filter ---")
res_nocountry = requests.get(f"{base_url}?q=Software+Development&limit=20&offset=0", headers=headers).json()
print("No country count:", len(res_nocountry.get("jobs", [])))

