import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match

async def scrape_adzuna_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from adzuna.in using SSR HTML card extraction.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("w") or location or ""
    
    print(f"[*] Adzuna: Fetching job listings for '{effective_role}' in '{effective_loc or 'India'}'...")
    
    headers = {
        'authority': 'www.adzuna.in',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        params = {
            "q": effective_role,
            "p": page
        }
        if effective_loc:
            params["w"] = effective_loc
        for k in ["distance", "salary_min", "salary_max", "contract_type", "working_hours", "category", "sort_by"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://www.adzuna.in/search?{urllib.parse.urlencode(params)}"
        print(f"[*] Adzuna: Navigating to page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Adzuna: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("article[data-aid], .a-job-search-result, article")
            print(f"[+] Adzuna: Found {len(cards)} job card elements on page {page}.")
            
            if not cards:
                break
                
            added_on_page = 0
            for card in cards:
                title_el = card.select_one("h2 a, a.text-base, h2")
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                if not is_role_match(title, job_role):
                    continue
                    
                apply_link = title_el.get("href", "") if title_el.name == "a" else (title_el.find("a").get("href") if title_el.find("a") else "")
                if apply_link and not apply_link.startswith("http"):
                    apply_link = "https://www.adzuna.in" + apply_link
                    
                comp_el = card.select_one(".ui-company, [data-qa='company-name'], .text-neutral-500, .company")
                company = comp_el.text.strip() if comp_el else "Adzuna Employer"
                
                loc_el = card.select_one(".ui-location, .location, [data-qa='location']")
                job_location = loc_el.text.strip() if loc_el else (location or "India")
                
                sal_el = card.select_one(".ui-salary, .salary, [data-qa='salary']")
                salary = sal_el.text.strip() if sal_el else "Not disclosed"
                
                desc_el = card.select_one(".ui-snippet, .snippet, p")
                desc = desc_el.text.strip() if desc_el else ""
                
                date_el = card.select_one(".ui-date, .date, time")
                date_posted = date_el.text.strip() if date_el else "Recent"
                
                details = f"Company: {company} | Location: {job_location} | Salary: {salary} | {desc}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Adzuna"
                    })
                    added_on_page += 1
                    
            print(f"[+] Adzuna: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Adzuna: Error scraping page {page}: {err}")
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
        
    results = asyncio.run(scrape_adzuna_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "adzuna_jobs.csv")
