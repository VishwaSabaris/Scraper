import asyncio
import os
import sys
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match

async def scrape_dice_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from dice.com using Next.js streaming RSC payload parsing.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Dice: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'www.dice.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        params = {
            "q": effective_role,
            "pageSize": 30,
            "page": page
        }
        if effective_loc:
            params["location"] = effective_loc
        for k in ["workplaceTypes", "employmentType", "postedDate", "experienceLevel", "easyApply"]:
            if fp.get(k):
                params[f"filters.{k}"] = fp[k]
                
        url = f"https://www.dice.com/jobs?{urllib.parse.urlencode(params)}"
        print(f"[*] Dice: Navigating to page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=25
            )
            
            if res.status_code != 200:
                print(f"[!] Dice: Received HTTP {res.status_code} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            
            raw_job_items = []
            for s in soup.find_all("script"):
                if s.string and "jobList" in s.string:
                    txt = s.string
                    idx = txt.find('{"jobList":')
                    if idx == -1:
                        idx = txt.find('{\\"jobList\\":')
                        
                    if idx != -1:
                        raw_str = txt[idx:]
                        try:
                            cleaned = raw_str.encode('utf-8').decode('unicode_escape')
                        except Exception:
                            cleaned = raw_str
                            
                        idx2 = cleaned.find('{"jobList":')
                        if idx2 != -1:
                            sub = cleaned[idx2:]
                            depth = 0
                            end_idx = 0
                            for i, char in enumerate(sub):
                                if char == '{':
                                    depth += 1
                                elif char == '}':
                                    depth -= 1
                                    if depth == 0:
                                        end_idx = i + 1
                                        break
                            if end_idx > 0:
                                try:
                                    parsed = json.loads(sub[:end_idx])
                                    data_list = parsed.get("jobList", {}).get("data", [])
                                    if data_list:
                                        raw_job_items.extend(data_list)
                                except Exception:
                                    pass
                                    
            print(f"[+] Dice: Extracted {len(raw_job_items)} raw job objects from page {page}.")
            
            if not raw_job_items:
                break
                
            added_on_page = 0
            for item in raw_job_items:
                title = item.get("title", "").strip()
                if not is_role_match(title, job_role):
                    continue
                    
                company = item.get("companyName") or "Dice Employer"
                
                loc_data = item.get("jobLocation")
                if isinstance(loc_data, dict):
                    job_location = loc_data.get("displayName") or loc_data.get("city") or (location or "USA / Remote")
                else:
                    job_location = str(loc_data) if loc_data else (location or "USA / Remote")
                    
                apply_link = item.get("detailsPageUrl") or ""
                if not apply_link and item.get("guid"):
                    apply_link = f"https://www.dice.com/job-detail/{item.get('guid')}"
                elif not apply_link and item.get("id"):
                    apply_link = f"https://www.dice.com/job-detail/{item.get('id')}"
                    
                posted_date = item.get("postedDate") or "Recent"
                salary = item.get("salary") or "Not disclosed"
                emp_type = item.get("employmentType") or "Full-time"
                
                details = f"Company: {company} | Type: {emp_type} | Salary: {salary} | Location: {job_location}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": str(posted_date),
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Dice"
                    })
                    added_on_page += 1
                    
            print(f"[+] Dice: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Dice: Error scraping page {page}: {err}")
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
        loc = "Remote"
        
    results = asyncio.run(scrape_dice_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "dice_jobs.csv")
