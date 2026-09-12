import asyncio
import os
import sys
import urllib.parse
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match

async def scrape_instahyre_jobs(job_role, location="", max_pages=5, limit_per_page=35, filter_params=None, **kwargs):
    """
    Scrapes job listings from instahyre.com using its REST API with offset pagination.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_skills = fp.get("skills") or job_role
    effective_loc = fp.get("locations") or location or ""
    
    print(f"[*] Instahyre: Fetching job listings for '{effective_skills}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'www.instahyre.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': f'https://www.instahyre.com/search-jobs/?search=true&job_type=0&skills={urllib.parse.quote(effective_skills)}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        offset = (page - 1) * limit_per_page
        
        params = {
            "skills": effective_skills,
            "job_type": fp.get("job_type", "0"),
            "limit": limit_per_page,
            "offset": offset
        }
        if effective_loc:
            params["locations"] = effective_loc
        for k in ["experience", "company_type", "work_mode", "education"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://www.instahyre.com/api/v1/job_search?{urllib.parse.urlencode(params)}"
        print(f"[*] Instahyre: Querying page {page} (offset {offset})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Instahyre: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            data = res.json()
            objects = data.get("objects", [])
            total_count = data.get("meta", {}).get("total_count", 0)
            print(f"[+] Instahyre: Found {len(objects)} jobs on page {page} (Total available: {total_count}).")
            
            if not objects:
                break
                
            added_on_page = 0
            for item in objects:
                title = item.get("title", "").strip()
                keywords = ", ".join(item.get("keywords", []))
                
                # Check role or skills match
                if not is_role_match(title, job_role) and not any(t.lower() in (title + " " + keywords).lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                employer = item.get("employer", {})
                company = employer.get("company_name") or "Instahyre Employer"
                comp_url = employer.get("company_url") or employer.get("website") or "N/A"
                
                loc_raw = item.get("locations", [])
                if isinstance(loc_raw, list):
                    job_location = ", ".join(loc_raw) if loc_raw else (location or "India / Remote")
                else:
                    job_location = str(loc_raw) or (location or "India")
                    
                pub_url = item.get("public_url", "")
                if pub_url and not pub_url.startswith("http"):
                    apply_link = "https://www.instahyre.com" + pub_url
                elif pub_url:
                    apply_link = pub_url
                else:
                    job_id = item.get("id")
                    apply_link = f"https://www.instahyre.com/job-{job_id}" if job_id else f"https://www.instahyre.com/search-jobs/?skills={query_skills}"
                    
                candidate_title = item.get("candidate_title", "")
                details = f"Company: {company} | Skills: {keywords} | Target: {candidate_title}" if keywords else f"Company: {company} | Instahyre Verified Opportunity"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": "Recent",
                        "Apply Link": apply_link,
                        "Company Link": comp_url,
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Instahyre"
                    })
                    added_on_page += 1
                    
            print(f"[+] Instahyre: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0 and len(objects) < limit_per_page:
                break
                
            await asyncio.sleep(1.0)
            
        except Exception as err:
            print(f"[!] Instahyre: Error scraping page {page}: {err}")
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
        role = "Python"
        loc = "Bangalore"
        
    results = asyncio.run(scrape_instahyre_jobs(role, loc, max_pages=3))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "instahyre_jobs.csv")
