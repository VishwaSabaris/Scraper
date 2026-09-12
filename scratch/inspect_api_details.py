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

# 1. Timesjobs API details
print("=== 1. TIMESJOBS API SAMPLE ===")
url = "https://tjapi.timesjobs.com/search/api/v1/search/jobs/list"
payload = {
    "txtKeywords": "python",
    "txtLocation": "bangalore",
    "page": 1,
    "pageSize": 25
}
r = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
if r.status_code == 200:
    data = r.json()
    print("Total jobs:", data.get("total"))
    jobs = data.get("jobs", [])
    print("Jobs returned:", len(jobs))
    if jobs:
        j = jobs[0]
        print("Sample TimesJobs keys:", list(j.keys()))
        print("Sample TimesJobs Data:", {
            "title": j.get("jobTitle") or j.get("title"),
            "company": j.get("companyName") or j.get("company"),
            "location": j.get("location") or j.get("locations"),
            "experience": j.get("experience") or j.get("workExp"),
            "salary": j.get("salary") or j.get("salaryRange"),
            "posted": j.get("postedDate") or j.get("createdDate"),
            "link": j.get("jobDetailUrl") or j.get("applyUrl") or j.get("url"),
            "desc": (j.get("jobDescription") or j.get("description") or "")[:100]
        })

# 2. Shine API details
print("\n=== 2. SHINE API SAMPLE ===")
shine_url = "https://www.shine.com/api/v2/search/simple/?q=python&loc=bangalore"
r_shine = requests.get(shine_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
if r_shine.status_code == 200:
    data = r_shine.json()
    print("Total shine count:", data.get("count"))
    results = data.get("results", [])
    print("Results returned:", len(results))
    if results:
        j = results[0]
        print("Sample Shine keys:", list(j.keys()))
        print("Sample Shine Data:", {
            "title": j.get("job_title") or j.get("title"),
            "company": j.get("company_name") or j.get("company"),
            "location": j.get("loc_details") or j.get("locations"),
            "experience": j.get("exp_details") or j.get("experience"),
            "salary": j.get("salary_details") or j.get("salary"),
            "posted": j.get("date_posted") or j.get("time_ago") or j.get("posted_date"),
            "link": j.get("job_url") or j.get("canonical_url"),
            "desc": (j.get("job_desc") or j.get("description") or "")[:100]
        })

