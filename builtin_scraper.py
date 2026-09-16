import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match, normalize_date_posted

async def scrape_builtin_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from builtin.com using SSR HTML card extraction.
    Supports dynamic filter parameters, subpaths (/jobs/office, /jobs/remote, /jobs/hybrid), and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("search") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] BuiltIn: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'builtin.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        params = {
            "search": effective_role,
            "page": page
        }
        if effective_loc:
            params["location"] = effective_loc
            
        for k in ["country", "allLocations", "remote", "experience", "days_since_updated", "category", "company_size"]:
            if fp.get(k):
                params[k] = fp[k]
                
        workplace_path = fp.get("workplace_path", "")
        subpath = f"/{workplace_path}" if workplace_path else ""
        url = f"https://builtin.com/jobs{subpath}?{urllib.parse.urlencode(params)}"
        print(f"[*] BuiltIn: Navigating to page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] BuiltIn: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("[data-id='job-card'], .job-item, .job-card, [id^='job-card-'], div.card")
            print(f"[+] BuiltIn: Found {len(cards)} job card elements on page {page}.")
            
            if not cards:
                break
                
            added_on_page = 0
            for card in cards:
                title_el = card.select_one("h2 a, a[data-id='job-title'], a[href*='/job/'], h2")
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                apply_link = title_el.get("href", "") if title_el.name == "a" else (title_el.find("a").get("href") if title_el.find("a") else "")
                if apply_link and not apply_link.startswith("http"):
                    apply_link = "https://builtin.com" + apply_link
                    
                comp_el = card.select_one("[data-id='company-title'], .company-title, [class*='companyTitle'], [class*='company-name'], a[href*='/company/']")
                company = comp_el.text.strip() if comp_el else "BuiltIn Employer"
                
                comp_url = "N/A"
                if comp_el and comp_el.name == "a" and comp_el.get("href"):
                    comp_href = comp_el.get("href")
                    comp_url = f"https://builtin.com{comp_href}" if comp_href.startswith("/") else comp_href
                
                loc_el = card.select_one("[data-id='location'], .location, [class*='location']")
                job_location = loc_el.text.strip() if loc_el else (location or "USA / Remote")
                
                sal_el = card.select_one("[data-id='salary'], .salary, [class*='salary']")
                salary = sal_el.text.strip() if sal_el else "Not disclosed"
                
                date_el = card.select_one("[data-id='posted-date'], time, [class*='date']")
                date_posted = date_el.text.strip() if date_el else "Recent"
                date_posted = normalize_date_posted(date_posted)
                
                desc_el = card.select_one("[data-id='description'], .description, p")
                desc = desc_el.text.strip() if desc_el else ""
                
                details = f"Company: {company} | Location: {job_location} | Salary: {salary} | {desc}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": comp_url,
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "BuiltIn"
                    })
                    added_on_page += 1
                    
            print(f"[+] BuiltIn: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] BuiltIn: Error scraping page {page}: {err}")
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
        loc = ""
        
    results = asyncio.run(scrape_builtin_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "builtin_jobs.csv")
