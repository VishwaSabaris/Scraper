import asyncio
import os
import sys
import json
import urllib3
import urllib.parse
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match

urllib3.disable_warnings()

async def scrape_timesjobs_jobs(job_role, location="", max_pages=5, page_size=50, filter_params=None, **kwargs):
    """
    Scrapes job listings from timesjobs.com using its search API endpoint.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_keywords = fp.get("keywords") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] TimesJobs: Fetching job listings for '{effective_keywords}' in '{effective_loc or 'India'}'...")
    
    headers = {
        'authority': 'tjapi.timesjobs.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://www.timesjobs.com',
        'referer': 'https://www.timesjobs.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        url = "https://tjapi.timesjobs.com/search/api/v1/search/jobs/list"
        payload = {
            "keywords": effective_keywords,
            "location": effective_loc,
            "page": page,
            "size": page_size
        }
        for k in ["cboWorkExp1", "cboWorkExp2", "postDate", "workMode", "function", "industry"]:
            if fp.get(k):
                payload[k] = fp[k]
                
        print(f"[*] TimesJobs: Querying page {page} with keywords '{effective_keywords}' (size {page_size})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.post,
                url,
                json=payload,
                headers=headers,
                impersonate="chrome120",
                verify=False,
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] TimesJobs: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            data = res.json()
            job_list = data.get("jobs", [])
            total = data.get("total", 0)
            print(f"[+] TimesJobs: Found {len(job_list)} jobs on page {page} (Total available: {total}).")
            
            if not job_list:
                break
                
            added_on_page = 0
            for item in job_list:
                title = item.get("title") or item.get("jobTitle") or ""
                title = title.strip()
                skills = item.get("skills", "") or ""
                desc = item.get("description", "") or ""
                
                # Check match across title, skills, description
                if not (is_role_match(title, job_role) or is_role_match(skills, job_role) or any(t.lower() in (title + " " + skills + " " + desc).lower() for t in job_role.split() if len(t) > 2)):
                    continue
                    
                company = item.get("company") or item.get("companyName") or "TimesJobs Recruiter"
                
                loc = item.get("location") or item.get("locations") or (location or "India")
                if isinstance(loc, list):
                    job_location = ", ".join(loc)
                else:
                    job_location = str(loc)
                    
                apply_link = item.get("jobDetailUrl") or item.get("applyUrl") or ""
                if not apply_link and item.get("jobId"):
                    apply_link = f"https://www.timesjobs.com/job-detail/{item.get('jobId')}"
                    
                low_sal = item.get("lowSalary")
                high_sal = item.get("highSalary")
                if low_sal and high_sal and low_sal != -1 and high_sal != -1:
                    salary = f"INR {low_sal} - {high_sal}"
                elif low_sal and low_sal != -1:
                    salary = f"INR {low_sal}+"
                else:
                    salary = "Not disclosed"
                    
                exp_from = item.get("experienceFrom", "")
                exp_to = item.get("experienceTo", "")
                exp = f"{exp_from}-{exp_to} yrs" if (exp_from or exp_to) else "N/A"
                
                post_date = item.get("postDate") or "Recent"
                app_cnt = item.get("applicationCount", "N/A")
                applicants_str = str(app_cnt) if app_cnt is not None else "N/A"
                
                details = f"Company: {company} | Exp: {exp} | Salary: {salary} | Skills: {skills} | {desc}"
                
                if apply_link and not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": str(post_date),
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": applicants_str,
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "TimesJobs"
                    })
                    added_on_page += 1
                    
            print(f"[+] TimesJobs: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0 and len(job_list) < page_size:
                break
                
            await asyncio.sleep(1.0)
            
        except Exception as err:
            print(f"[!] TimesJobs: Error scraping page {page}: {err}")
            break
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = "Python Developer"
        loc = "Bangalore"
        
    results = asyncio.run(scrape_timesjobs_jobs(role, loc, max_pages=3))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "timesjobs_jobs.csv")
