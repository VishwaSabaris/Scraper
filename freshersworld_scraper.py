import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match

async def scrape_freshersworld_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from freshersworld.com using SSR HTML card extraction.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("keywords") or job_role
    effective_loc = fp.get("city") or location or ""
    
    print(f"[*] Freshersworld: Fetching job listings for '{effective_role}' in '{effective_loc or 'India'}'...")
    
    headers = {
        'authority': 'www.freshersworld.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    role_slug = effective_role.lower().strip().replace(" ", "-")
    role_slug = "".join(c for c in role_slug if c.isalnum() or c == "-")
    
    loc_slug = ""
    if effective_loc:
        loc_slug = effective_loc.lower().strip().replace(" ", "-")
        loc_slug = "".join(c for c in loc_slug if c.isalnum() or c == "-")
        
    for page in range(1, max_pages + 1):
        offset = (page - 1) * 20
        params = {
            "offset": offset,
            "limit": 20
        }
        for k in ["course", "jobtype"]:
            if fp.get(k):
                params[k] = fp[k]
                
        if loc_slug:
            url = f"https://www.freshersworld.com/jobs/jobsearch/{role_slug}-jobs-in-{loc_slug}?{urllib.parse.urlencode(params)}"
        else:
            url = f"https://www.freshersworld.com/jobs/jobsearch/{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        print(f"[*] Freshersworld: Navigating to page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Freshersworld: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".job-container, .jobs-today, .col-md-12.job-container, [class*='job-container'], .job-contents")
            print(f"[+] Freshersworld: Found {len(cards)} job card elements on page {page}.")
            
            if not cards:
                break
                
            added_on_page = 0
            for card in cards:
                apply_link_el = card.select_one("a[href*='/jobs/']")
                if not apply_link_el:
                    continue
                    
                apply_link = apply_link_el.get("href", "").strip()
                if not apply_link:
                    continue
                if not apply_link.startswith("http"):
                    apply_link = "https://www.freshersworld.com" + apply_link
                    
                # Extract title from card element or slug
                title_el = card.select_one(".seo_title, .job-title, .latest-jobs-title, .wrap-title, h3, h2")
                title = title_el.text.strip() if title_el else ""
                
                # Check if title is actually company name (e.g. 'Client of Freshersworld') or empty
                if not title or "client of" in title.lower():
                    # Parse from URL slug
                    slug_match = re.search(r'/jobs/([a-zA-Z0-9\-]+?)(?:-jobs-opening|-in-|-at-|\d+$)', apply_link)
                    if slug_match:
                        title = slug_match.group(1).replace("-", " ").title()
                    else:
                        title = job_role.title()
                        
                if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                comp_el = card.select_one(".company-name, .latest-jobs-company, [class*='company']")
                company = comp_el.text.strip() if comp_el else "Freshersworld Employer"
                
                loc_el = card.select_one(".job-location, .job-desc .bold, [class*='location']")
                job_location = loc_el.text.strip() if loc_el else (location or "India")
                
                qual_el = card.select_one(".job-qual, .qualifications, [class*='qual']")
                qual = qual_el.text.strip() if qual_el else "Any Graduate"
                
                desc_el = card.select_one(".job-desc, .desc, p")
                desc = desc_el.text.strip() if desc_el else ""
                
                date_el = card.select_one(".job-posted, .posted-date, [class*='date']")
                date_posted = date_el.text.strip() if date_el else "Recent"
                
                details = f"Company: {company} | Location: {job_location} | Qualification: {qual} | {desc}"
                
                if apply_link and not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Freshersworld"
                    })
                    added_on_page += 1
                    
            print(f"[+] Freshersworld: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Freshersworld: Error scraping page {page}: {err}")
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
        
    results = asyncio.run(scrape_freshersworld_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "freshersworld_jobs.csv")
