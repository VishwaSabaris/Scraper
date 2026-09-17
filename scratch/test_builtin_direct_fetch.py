from curl_cffi import requests as c_requests
from bs4 import BeautifulSoup
import json
import re

urls = [
    "https://builtin.com/job/sales-development-representative/11137879",
    "https://builtin.com/job/sales-development-representative-sdr/11183065",
    "https://builtin.com/job/sales-development-representative-sdr-india-us-market/11181441",
    "https://builtin.com/job/sb-1418-sales-development-representative-sdr/11181208",
    "https://builtin.com/job/sb-1496-sales-development-representative-sdr/11181211",
    "https://builtin.com/job/sales-development-representative/9903563",
    "https://builtin.com/job/sales-development-representative-goa/11151955",
    "https://builtin.com/job/sales-development-representative/11151708",
    "https://builtin.com/job/sales-development-representative/11150997",
    "https://builtin.com/job/sales-development-representative/11140662",
    "https://builtin.com/job/sales-development-representative/11140387",
    "https://builtin.com/job/sales-development-representative/10946962",
    "https://builtin.com/job/sales-development-representative/10112048",
    "https://builtin.com/job/sales-development-representative-sdr/10432904",
    "https://builtin.com/job/fresher-sales-development-representative/11067839",
    "https://builtin.com/job/sales-development-representative/11050525",
    "https://builtin.com/job/ebizon-sales-development-representative-noida/11048369",
    "https://builtin.com/job/sales-development-representative/10361504",
    "https://builtin.com/job/senior-sales-development-representative-apac/11037835",
    "https://builtin.com/job/sales-development-representative-international-sales/10997116",
    "https://builtin.com/job/sdr/10975331",
    "https://builtin.com/job/sales-development-representative/10974552"
]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'accept-language': 'en-US,en;q=0.9',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

for i, u in enumerate(urls):
    try:
        res = c_requests.get(u, headers=headers, impersonate="chrome120", timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # JSON-LD check
            comp_name = None
            job_loc = None
            for s in soup.find_all("script", type="application/ld+json"):
                if s.string:
                    try:
                        jd = json.loads(s.string)
                        if jd.get("@type") == "JobPosting":
                            hiring_org = jd.get("hiringOrganization", {})
                            if isinstance(hiring_org, dict):
                                comp_name = hiring_org.get("name")
                            job_location_obj = jd.get("jobLocation", {})
                            if isinstance(job_location_obj, dict):
                                addr = job_location_obj.get("address", {})
                                if isinstance(addr, dict):
                                    job_loc = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')} {addr.get('addressCountry', '')}".strip(' ,')
                    except Exception:
                        pass
                        
            # DOM fallback check
            if not comp_name:
                comp_tag = soup.select_one("a[href*='/company/'], [data-id='company-name'], .company-name")
                if comp_tag:
                    comp_name = comp_tag.text.strip()
                    
            print(f"[{i+1}] URL: {u.split('/')[-1]}")
            print(f"    Company : {comp_name}")
            print(f"    Location: {job_loc}")
        else:
            print(f"[{i+1}] HTTP {res.status_code} for {u}")
    except Exception as e:
        print(f"[{i+1}] Error: {e}")
