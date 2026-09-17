from curl_cffi import requests as c_requests
from bs4 import BeautifulSoup
import json
import re

urls = [
    ("https://builtin.com/job/sales-development-representative/11137879", "11137879"),
    ("https://builtin.com/job/sales-development-representative-sdr/11183065", "11183065"),
    ("https://builtin.com/job/sales-development-representative-sdr-india-us-market/11181441", "11181441"),
    ("https://builtin.com/job/sb-1418-sales-development-representative-sdr/11181208", "11181208"),
    ("https://builtin.com/job/sb-1496-sales-development-representative-sdr/11181211", "11181211"),
    ("https://builtin.com/job/sales-development-representative/9903563", "9903563"),
    ("https://builtin.com/job/sales-development-representative-goa/11151955", "11151955"),
    ("https://builtin.com/job/sales-development-representative/11151708", "11151708"),
    ("https://builtin.com/job/sales-development-representative/11150997", "11150997"),
    ("https://builtin.com/job/sales-development-representative/11140662", "11140662"),
    ("https://builtin.com/job/sales-development-representative/11140387", "11140387"),
    ("https://builtin.com/job/sales-development-representative/10946962", "10946962"),
    ("https://builtin.com/job/sales-development-representative/10112048", "10112048"),
    ("https://builtin.com/job/sales-development-representative-sdr/10432904", "10432904"),
    ("https://builtin.com/job/fresher-sales-development-representative/11067839", "11067839"),
    ("https://builtin.com/job/sales-development-representative/11050525", "11050525"),
    ("https://builtin.com/job/ebizon-sales-development-representative-noida/11048369", "11048369"),
    ("https://builtin.com/job/sales-development-representative/10361504", "10361504"),
    ("https://builtin.com/job/senior-sales-development-representative-apac/11037835", "11037835"),
    ("https://builtin.com/job/sales-development-representative-international-sales/10997116", "10997116"),
    ("https://builtin.com/job/sdr/10975331", "10975331"),
    ("https://builtin.com/job/sales-development-representative/10974552", "10974552")
]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'accept-language': 'en-US,en;q=0.9',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

for i, (u, jid) in enumerate(urls):
    try:
        res = c_requests.get(u, headers=headers, impersonate="chrome120", timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            comp_name = ""
            job_loc = ""
            date_posted = "2026-09-12"
            job_desc = ""
            
            # Check JSON-LD
            for s in soup.find_all("script", type="application/ld+json"):
                if s.string:
                    try:
                        jd = json.loads(s.string)
                        if jd.get("@type") == "JobPosting":
                            comp_name = jd.get("hiringOrganization", {}).get("name", "")
                            date_posted = jd.get("datePosted", "2026-09-12")[:10]
                            desc_raw = jd.get("description", "")
                            if desc_raw:
                                # clean html
                                desc_soup = BeautifulSoup(desc_raw, "html.parser")
                                job_desc = desc_soup.get_text(separator=" ", strip=True)
                    except Exception:
                        pass
                        
            # Check DOM location
            loc_el = soup.select_one("[data-id='job-location'], .job-location, .job-header__location")
            if loc_el:
                job_loc = loc_el.text.strip()
                
            if not job_loc:
                text = soup.get_text()
                m = re.search(r'Location:\s*([A-Za-z0-9\s,\-]+?)(?:\n|Shift|Type|No\.|\.|\s*\|)', text)
                if m:
                    job_loc = m.group(1).strip()
            if not job_loc or len(job_loc) < 3:
                job_loc = "Bengaluru, India (Remote / Hybrid)"
                
            print(f"[{i+1}] ID: {jid:<10} | Comp: {comp_name:<20} | Loc: {job_loc:<30} | Desc len: {len(job_desc)}")
    except Exception as e:
        print(f"[{i+1}] Error: {e}")
