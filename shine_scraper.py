import asyncio
import os
import sys
import json
import urllib.parse
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match, normalize_date_posted, get_company_website

async def scrape_shine_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from shine.com using its search JSON API.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("qActual") or fp.get("q") or job_role
    effective_loc = fp.get("loc") or fp.get("location") or location or ""
    
    print(f"[*] Shine: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'www.shine.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': f'https://www.shine.com/job-search/{urllib.parse.quote(effective_role)}-jobs',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        params = {
            "q": effective_role,
            "page": page
        }
        if effective_loc:
            params["loc"] = effective_loc
        for k in ["fexp", "exp", "fsalary", "salary", "posted_date", "work_mode", "functional_area", "industry", "emp_type", "sort"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://www.shine.com/api/v2/search/simple/?{urllib.parse.urlencode(params)}"
        print(f"[*] Shine: Querying page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Shine: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            data = res.json()
            results = data.get("results", [])
            print(f"[+] Shine: Found {len(results)} job items on page {page}.")
            
            if not results:
                break
                
            added_on_page = 0
            for item in results:
                title = item.get("jJT") or item.get("title") or ""
                title = title.strip()
                company_cand = str(item.get("jCName") or item.get("company_name") or "").lower()
                is_company_match = bool(fp.get("company")) or (len(job_role) >= 3 and job_role.lower() in company_cand)
                if not is_company_match and not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                company = item.get("jCName") or item.get("company_name") or "Shine Recruiter"
                
                # Locations
                loc_raw = item.get("jLoc") or item.get("loc_details") or []
                if isinstance(loc_raw, list):
                    job_location = ", ".join(loc_raw) if loc_raw else (location or "India / Various")
                else:
                    job_location = str(loc_raw) or (location or "India")
                    
                # Apply Link
                slug = item.get("jSlug") or ""
                if slug:
                    apply_link = f"https://www.shine.com/jobs/{slug}"
                else:
                    job_id = item.get("id") or item.get("doc_id")
                    apply_link = f"https://www.shine.com/jobs/detail/{job_id}" if job_id else f"https://www.shine.com/job-search/{urllib.parse.quote(effective_role)}-jobs"
                    
                salary = item.get("jSal") or item.get("salary_details") or "Competitive"
                exp = item.get("jExp") or item.get("exp_details") or "0-5 Yrs"
                posted_date = item.get("jPDate") or "Recent"
                posted_date = normalize_date_posted(str(posted_date))
                
                # Applicants
                applicants = item.get("jACnt")
                applicants_str = f"{applicants} Applicants" if (applicants is not None and str(applicants).isdigit()) else "Actively Hiring"
                
                # Details
                desc = item.get("jJD") or item.get("job_desc") or ""
                comp_clean = company if (company and company != "N/A") else "Shine Verified Employer"
                loc_clean = job_location if (job_location and job_location != "N/A") else (location or "Bengaluru, Karnataka, India")
                details = f"Company: {comp_clean} | Salary: {salary} | Exp: {exp} | {desc}" if desc else f"Company: {comp_clean} | Location: {loc_clean} | Role: {title} | Source: Shine"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": comp_clean,
                        "Location": loc_clean,
                        "Date Posted": str(posted_date),
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(comp_clean, fallback_portal_url="https://www.shine.com"),
                        "No. of Applicants": applicants_str,
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Shine"
                    })
                    added_on_page += 1
                    
            print(f"[+] Shine: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Shine: Error scraping page {page}: {err}")
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
        role = "Sales Development Representative"
        loc = "Bangalore"
        
    results = asyncio.run(scrape_shine_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "shine_jobs.csv")
