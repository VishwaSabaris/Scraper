import asyncio
import os
import sys
import json
import urllib.parse
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match, normalize_date_posted, get_company_website

async def scrape_foundit_jobs(job_role, location="", max_pages=1, limit_per_page=20, filter_params=None, **kwargs):
    """
    Scrapes job listings from foundit.in (formerly Monster India) using the middleware search API.
    Supports dynamic filter parameter adaptation and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("query") or job_role
    effective_loc = fp.get("locations") or fp.get("location") or location or ""
    
    print(f"[*] Foundit: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'www.foundit.in',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://www.foundit.in',
        'referer': f'https://www.foundit.in/srp/results?query={urllib.parse.quote(effective_role)}&locations={urllib.parse.quote(effective_loc)}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page_idx in range(max_pages):
        start_offset = page_idx * limit_per_page
        
        # Build query params
        params = {
            "query": effective_role,
            "locations": effective_loc,
            "limit": limit_per_page,
            "start": start_offset,
            "sort": fp.get("sort", "1"),
            "queryDerived": "true"
        }
        for k in ["experienceRanges", "salaryRanges", "postedDate", "jobFreshness", "workMode", "jobTypes", "industries", "functions", "companyTypes", "employerTypes", "postedBy"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://www.foundit.in/middleware/jobsearch?{urllib.parse.urlencode(params)}"
        print(f"[*] Foundit: Querying page {page_idx + 1} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Foundit: Received HTTP {res.status_code} on page {page_idx + 1}. Stopping.")
                break
                
            data = res.json()
            job_list = data.get("jobSearchResponse", {}).get("data", [])
            print(f"[+] Foundit: Retrieved {len(job_list)} raw listings from page {page_idx + 1}.")
            
            if not job_list:
                break
                
            added_on_page = 0
            for item in job_list:
                title = item.get("title", "").strip()
                if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                # Extract company
                company = item.get("companyName") or item.get("company", {}).get("name") or "Foundit Recruiter"
                if isinstance(company, dict):
                    company = company.get("name", "Foundit Recruiter")
                    
                # Extract location
                locations_raw = item.get("locations", [])
                if isinstance(locations_raw, list):
                    city_names = [loc.get("city") for loc in locations_raw if isinstance(loc, dict) and loc.get("city")]
                    job_location = ", ".join(city_names) if city_names else (location or "India / Various")
                else:
                    job_location = str(locations_raw) or (location or "India")
                    
                # Extract apply URL
                apply_link = item.get("redirectUrl") or item.get("applyUrl") or item.get("jdUrl") or ""
                if not apply_link and item.get("id"):
                    apply_link = f"https://www.foundit.in/job/{item.get('id')}"
                elif apply_link and not apply_link.startswith("http"):
                    apply_link = "https://www.foundit.in" + apply_link
                    
                # Extract dates
                created_at = item.get("createdAt") or item.get("freshness") or item.get("lastUpdated") or "Recent"
                date_posted = normalize_date_posted(created_at)
                
                # Applicants
                applicants = item.get("totalApplicants", "N/A")
                applicants_str = str(applicants) if applicants is not None else "N/A"
                
                # Description and salary
                salary = item.get("salary", "Not disclosed")
                skills_raw = item.get("skills", [])
                if isinstance(skills_raw, list):
                    skills = ", ".join([s.get("text", "") if isinstance(s, dict) else str(s) for s in skills_raw if s])
                else:
                    skills = str(skills_raw)
                    
                functions_raw = item.get("functions", [])
                if isinstance(functions_raw, list):
                    functions = ", ".join([f.get("text", "") if isinstance(f, dict) else str(f) for f in functions_raw if f])
                else:
                    functions = str(functions_raw)
                    
                industries_raw = item.get("industries", [])
                if isinstance(industries_raw, list):
                    industries = ", ".join([ind.get("text", "") if isinstance(ind, dict) else str(ind) for ind in industries_raw if ind])
                else:
                    industries = str(industries_raw)
                    
                exp = item.get("exp") or f"{item.get('minimumExperience', 0)}-{item.get('maximumExperience', 0)} Years"
                
                detail_parts = []
                if exp and exp != "0-0 Years":
                    detail_parts.append(f"Experience: {exp}")
                if salary and salary != "0-0 INR" and salary != "Not disclosed":
                    detail_parts.append(f"Salary: {salary}")
                if skills:
                    detail_parts.append(f"Key Skills: {skills}")
                if industries:
                    detail_parts.append(f"Industry: {industries}")
                if functions:
                    detail_parts.append(f"Function: {functions}")
                    
                comp_clean = company if (company and company != "Foundit Recruiter" and company != "N/A") else "Foundit Verified Employer"
                loc_clean = job_location if (job_location and job_location != "N/A") else (location or "Bengaluru, Karnataka, India")
                details = " | ".join(detail_parts) if detail_parts else f"Job Role: {title} at {comp_clean} in {loc_clean}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": comp_clean,
                        "Location": loc_clean,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(comp_clean, fallback_portal_url="https://www.foundit.in"),
                        "No. of Applicants": applicants_str if (applicants_str and applicants_str != "N/A") else "Actively Hiring",
                        "Company / Job Details": details[:600] + "..." if len(details) > 600 else details,
                        "Source": "Foundit"
                    })
                    added_on_page += 1
                    
            print(f"[+] Foundit: Extracted {added_on_page} matching jobs from page {page_idx + 1}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Foundit: Error scraping page {page_idx + 1}: {err}")
            break
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = "Sales Development Representative"
        loc = "Bengaluru"
        
    results = asyncio.run(scrape_foundit_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "foundit_jobs.csv")
