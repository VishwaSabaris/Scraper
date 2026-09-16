import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match, normalize_date_posted

async def scrape_apna_jobs(job_role, location="Bengaluru", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from apna.co using SSR HTML and clean job card extraction.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("text") or job_role
    effective_loc = fp.get("location_name") or fp.get("location") or location or "Bengaluru"
    
    print(f"[*] Apna: Fetching job listings for '{effective_role}' in '{effective_loc or 'India'}'...")
    
    headers = {
        'authority': 'apna.co',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page_idx in range(1, max_pages + 1):
        params = {
            "search": "true",
            "text": effective_role,
            "page": page_idx
        }
        if effective_loc:
            params["location_name"] = effective_loc if "Region" in effective_loc else f"{effective_loc} Region"
            params["location"] = effective_loc
            
        for k in ["minExperience", "workType", "workMode", "postedIn", "salary", "workLocationType", "workShift", "minSalary", "experience", "department", "sort"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://apna.co/jobs?{urllib.parse.urlencode(params)}"
        print(f"[*] Apna: Navigating to page {page_idx} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                print(f"[!] Apna: Received HTTP {res.status_code} on page {page_idx}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            job_links = soup.find_all("a", href=re.compile(r"^/job/"))
            print(f"[+] Apna: Found {len(job_links)} job card elements on page {page_idx}.")
            
            if not job_links:
                break
                
            added_on_page = 0
            for a in job_links:
                href = a.get("href", "")
                apply_link = f"https://apna.co{href}" if href.startswith("/") else href
                
                if any(j["Apply Link"] == apply_link for j in jobs_data):
                    continue
                    
                # Exact title extraction
                h2 = a.find("h2")
                title = h2.text.strip() if h2 else ""
                
                # Fallback title
                if not title:
                    title_el = a.find(["h3", "h4", "p", "span"])
                    title = title_el.text.strip() if title_el else ""
                    
                if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                # Exact company extraction
                comp_el = a.find("span", class_=lambda c: c and ("text-xs" in c or "secondary-text" in c))
                company = comp_el.text.strip() if comp_el else "Apna Employer"
                
                # Exact location and salary extraction
                spans_sm = a.find_all("span", class_=lambda c: c and "text-sm" in c)
                job_location = spans_sm[0].text.strip() if len(spans_sm) > 0 else (location or "India")
                salary = spans_sm[1].text.strip() if len(spans_sm) > 1 else "Not disclosed"
                
                # If first span looks like "Urgently hiring", adjust
                if "urgently hiring" in job_location.lower() and len(spans_sm) > 1:
                    job_location = spans_sm[1].text.strip()
                    salary = spans_sm[2].text.strip() if len(spans_sm) > 2 else "Not disclosed"
                    
                # Tags: work mode, job type, experience, date
                tags = [t.text.strip() for t in a.find_all("div", class_=lambda c: c and "bg-[#F2F2F3]" in c)]
                tags_str = ", ".join(tags) if tags else "Full Time"
                
                date_posted = "Recent"
                for tag_text in tags:
                    if any(w in tag_text.lower() for w in ["ago", "today", "yesterday", "day", "week", "just"]):
                        date_posted = normalize_date_posted(tag_text)
                        break
                        
                details = f"Company: {company} | Location: {job_location} | Salary: {salary} | Tags: {tags_str}"
                
                jobs_data.append({
                    "Job Role": title,
                    "Company Name": company,
                    "Location": job_location,
                    "Date Posted": date_posted,
                    "Apply Link": apply_link,
                    "Company Link": "N/A",
                    "No. of Applicants": "N/A",
                    "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                    "Source": "Apna"
                })
                added_on_page += 1
                
            print(f"[+] Apna: Extracted {added_on_page} matching jobs from page {page_idx}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Apna: Error scraping page {page_idx}: {err}")
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
        loc = "Bengaluru"
        
    results = asyncio.run(scrape_apna_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "apna_jobs.csv")
