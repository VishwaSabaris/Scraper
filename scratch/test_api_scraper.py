import datetime
import requests
import os
import sys
sys.path.append(os.path.abspath("."))
from utils import is_role_match

def test_himalayas_scrape(job_role, location=""):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    # Construct search parameters
    params = {
        "q": job_role,
        "page": 1
    }
    if location:
        params["country"] = location

    print(f"[*] Querying Himalayas API for '{job_role}' in '{location or 'Worldwide'}'...")
    
    jobs_data = []
    max_pages = 5
    
    for page in range(1, max_pages + 1):
        params["page"] = page
        url = "https://himalayas.app/jobs/api/search"
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"[!] API returned status {resp.status_code}")
                break
                
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            if not raw_jobs:
                print(f"[-] No more jobs returned on page {page}.")
                break
                
            added = 0
            for item in raw_jobs:
                title = item.get("title", "")
                if not is_role_match(title, job_role):
                    continue
                    
                loc_list = item.get("locationRestrictions", [])
                job_location = ", ".join(loc_list) if loc_list else "Worldwide / Remote"
                
                # Check location filter if specified
                if location:
                    loc_lower = location.lower().strip()
                    if loc_lower in ["uk", "united kingdom", "gb", "great britain"]:
                        loc_check = ["united kingdom", "uk", "great britain", "worldwide", "anywhere"]
                    elif loc_lower in ["us", "usa", "united states"]:
                        loc_check = ["united states", "us", "usa", "worldwide", "anywhere"]
                    else:
                        loc_check = [loc_lower, "worldwide", "anywhere"]
                        
                    # If location restriction doesn't include target location or worldwide
                    if loc_list and not any(any(c in l.lower() for c in loc_check) for l in loc_list):
                        continue
                        
                # Date posted
                pub_date = item.get("pubDate")
                if pub_date:
                    try:
                        date_str = datetime.datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = "N/A"
                else:
                    date_str = "N/A"
                    
                apply_link = item.get("applicationLink") or item.get("guid") or ""
                company_slug = item.get("companySlug", "")
                company_link = f"https://himalayas.app/companies/{company_slug}" if company_slug else "N/A"
                
                emp_type = item.get("employmentType", "")
                seniority = ", ".join(item.get("seniority", [])) if isinstance(item.get("seniority"), list) else ""
                cats = ", ".join(item.get("categories", [])) if isinstance(item.get("categories"), list) else ""
                
                details_parts = []
                if emp_type: details_parts.append(f"Type: {emp_type}")
                if seniority: details_parts.append(f"Seniority: {seniority}")
                if cats: details_parts.append(f"Categories: {cats}")
                details = " | ".join(details_parts) if details_parts else "N/A"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": item.get("companyName", "Himalayas Employer"),
                        "Location": job_location,
                        "Date Posted": date_str,
                        "Apply Link": apply_link,
                        "Company Link": company_link,
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details,
                        "Source": "Himalayas"
                    })
                    added += 1
                    
            print(f"[+] Page {page}: extracted {added} matching jobs out of {len(raw_jobs)} returned.")
            
        except Exception as e:
            print(f"[!] Error fetching page {page}: {e}")
            break
            
    print(f"\n[+] Total scraped: {len(jobs_data)}")
    for j in jobs_data[:5]:
        print(" -", j["Job Role"], "|", j["Company Name"], "|", j["Location"])

if __name__ == "__main__":
    test_himalayas_scrape("Software Development", "United Kingdom")
