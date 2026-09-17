import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests
from utils import save_to_csv, is_role_match, normalize_date_posted, get_company_website

async def scrape_internshala_jobs(job_role, location="", max_pages=1, filter_params=None, **kwargs):
    """
    Scrapes job listings from internshala.com using SSR HTML parsing.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("role") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Internshala: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'authority': 'internshala.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    jobs_data = []
    
    role_slug = effective_role.lower().strip().replace(" ", "-")
    role_slug = "".join(c for c in role_slug if c.isalnum() or c == "-")
    
    # Normalize common technical roles to Internshala's exact category slugs
    slug_mappings = {
        "python-developer": "python-django",
        "python-engineer": "python-django",
        "python": "python-django",
        "software-engineer": "software-development",
        "software-developer": "software-development",
        "developer": "software-development",
        "programmer": "software-development",
        "frontend-engineer": "front-end-development",
        "frontend-developer": "front-end-development",
        "backend-engineer": "backend-development",
        "backend-developer": "backend-development",
        "full-stack-engineer": "full-stack-development",
        "full-stack-developer": "full-stack-development",
        "data-scientist": "data-science",
        "data-analyst": "data-analytics",
        "ml-engineer": "machine-learning",
        "ai-engineer": "artificial-intelligence-ai"
    }
    role_slug = slug_mappings.get(role_slug, role_slug)
    
    loc_slug = ""
    if effective_loc:
        loc_slug = effective_loc.lower().strip().replace(" ", "-")
        loc_slug = "".join(c for c in loc_slug if c.isalnum() or c == "-")
        
    exp_str = f"/experience-{fp['experience']}" if fp.get("experience") else ""
    sal_str = f"/salary-{fp['salary']}" if fp.get("salary") else ""
    
    for page in range(1, max_pages + 1):
        page_str = f"/page-{page}" if page > 1 else ""
        if loc_slug:
            url = f"https://internshala.com/jobs/{role_slug}-jobs-in-{loc_slug}{exp_str}{sal_str}{page_str}/"
        else:
            url = f"https://internshala.com/jobs/{role_slug}-jobs{exp_str}{sal_str}{page_str}/"
            
        print(f"[*] Internshala: Navigating to page {page} ({url})...")
        
        try:
            res = await asyncio.to_thread(
                c_requests.get,
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=20
            )
            
            if res.status_code != 200:
                # Fallback to search query parameter
                fallback_url = f"https://internshala.com/jobs/keywords-{urllib.parse.quote(effective_role)}{page_str}/"
                print(f"[*] Internshala: Trying fallback search URL ({fallback_url})...")
                res = await asyncio.to_thread(
                    c_requests.get,
                    fallback_url,
                    headers=headers,
                    impersonate="chrome120",
                    timeout=20
                )
                if res.status_code != 200:
                    print(f"[!] Internshala: Received HTTP {res.status_code}. Stopping.")
                    break
                    
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".individual_internship, .job-card, [class*='individual_internship'], .container-fluid.individual_internship")
            print(f"[+] Internshala: Found {len(cards)} job card elements on page {page}.")
            
            if not cards:
                break
                
            added_on_page = 0
            for card in cards:
                title_el = card.select_one(".job-title-href, a.view_detail_button, .profile, h3 a, h2 a")
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                if not is_role_match(title, effective_role):
                    continue
                    
                apply_link = title_el.get("href", "")
                if apply_link and not apply_link.startswith("http"):
                    apply_link = "https://internshala.com" + apply_link
                    
                comp_el = card.select_one(".company-name, .link_display_like_text, .company_name")
                company = comp_el.text.strip() if comp_el else "Internshala Employer"
                
                loc_el = card.select_one(".location_link, #location_names, .locations, [class*='location']")
                job_location = loc_el.text.strip() if loc_el else (effective_loc or "Work from home / India")
                
                sal_el = card.select_one(".salary, .stipend, .desktop-text")
                salary = sal_el.text.strip() if sal_el else "Not disclosed"
                
                exp_el = card.select_one(".experience, .exp-item")
                exp = exp_el.text.strip() if exp_el else "0-2 years"
                
                # Date posted extraction
                date_posted = "Recent"
                date_el = card.select_one(".posted_by_container, .status-inactive, .status-success, .posted_on, [class*='status'], [class*='posted']")
                if date_el:
                    date_posted = date_el.text.strip()
                else:
                    date_match = re.search(r'(\d+\s+(?:days?|weeks?|hours?)\s+ago|Just now|Today|Few hours ago)', card.text, re.IGNORECASE)
                    if date_match:
                        date_posted = date_match.group(1).strip()
                        
                details = f"Company: {company} | CTC: {salary} | Experience: {exp} | Location: {job_location} | Posted: {date_posted}"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location or "Bengaluru, Karnataka, India",
                        "Date Posted": normalize_date_posted(date_posted),
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(company, fallback_portal_url="https://internshala.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                        "Source": "Internshala"
                    })
                    added_on_page += 1
                    
            print(f"[+] Internshala: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                break
                
            await asyncio.sleep(1.5)
            
        except Exception as err:
            print(f"[!] Internshala: Error scraping page {page}: {err}")
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
        loc = ""
        
    results = asyncio.run(scrape_internshala_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "internshala_jobs.csv")
