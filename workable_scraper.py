import asyncio
import sys
import re
import requests
from bs4 import BeautifulSoup
from utils import save_to_csv, is_role_match
from request_client import execute_request

def clean_html(raw_html):
    """Removes HTML tags and cleans up whitespace."""
    if not raw_html:
        return "N/A"
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', text).strip()

def scrape_workable_jobs(job_role, location="", max_jobs=50, filter_params=None, **kwargs):
    """
    Scrapes job listings from jobs.workable.com via its API endpoint.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("query") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Workable: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://jobs.workable.com/"
    }
    
    jobs_data = []
    page_token = None
    fetched_count = 0
    
    while fetched_count < max_jobs:
        params = {
            "query": effective_role
        }
        if effective_loc:
            params["location"] = effective_loc
        if page_token:
            params["pageToken"] = page_token
        for k in ["workplace", "employment_type", "department"]:
            if fp.get(k):
                params[k] = fp[k]
            
        try:
            res = execute_request("https://jobs.workable.com/api/v1/jobs", method="GET", params=params, headers=headers, timeout=20)
            if not res or res.status_code != 200:
                print(f"[!] Workable API returned status code {res.status_code if res else 'None'}")
                break
                
            data = res.json()
            jobs_list = data.get("jobs", [])
            if not jobs_list:
                break
                
            for item in jobs_list:
                title = item.get("title", "N/A")
                
                # Role matching filter
                if not is_role_match(title, job_role):
                    continue
                    
                comp_info = item.get("company", {})
                comp_name = comp_info.get("title", "Workable Employer") if isinstance(comp_info, dict) else "Workable Employer"
                comp_url = comp_info.get("url", "N/A") if isinstance(comp_info, dict) else "N/A"
                
                # Format locations
                locs = item.get("locations", [])
                if locs and isinstance(locs, list):
                    loc_str = ", ".join(locs)
                elif item.get("location") and isinstance(item.get("location"), dict):
                    l_obj = item.get("location")
                    loc_str = ", ".join(filter(None, [l_obj.get("city"), l_obj.get("subregion"), l_obj.get("countryName")]))
                else:
                    loc_str = location or "Remote / Various"
                    
                created_date = item.get("created", "N/A")
                if created_date and "T" in str(created_date):
                    created_date = str(created_date).split("T")[0]
                    
                apply_link = item.get("url", "N/A")
                
                raw_desc = item.get("description", "")
                raw_req = item.get("requirementsSection", "")
                emp_type = item.get("employmentType", "")
                workplace = item.get("workplace", "")
                
                clean_desc = clean_html(raw_desc)[:300]
                details_text = f"Workplace: {workplace.capitalize() if workplace else 'N/A'} | Type: {emp_type or 'N/A'} | {clean_desc}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": comp_name,
                        "Location": loc_str,
                        "Date Posted": created_date,
                        "Apply Link": apply_link,
                        "Company Link": comp_url,
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details_text,
                        "Source": "Workable"
                    })
                    fetched_count += 1
                    if fetched_count >= max_jobs:
                        break
                        
            page_token = data.get("nextPageToken")
            if not page_token:
                break
                
        except Exception as err:
            print(f"[!] Error querying Workable API: {err}")
            break
            
    print(f"[+] Workable: Extracted {len(jobs_data)} job listings.")
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = input("Enter Job Role (e.g., Python Developer): ").strip()
        loc = input("Enter Location (e.g., Remote): ").strip()
        
    results = scrape_workable_jobs(role, loc)
    print(f"\n[+] Workable Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "workable_jobs.csv")
