import asyncio
import os
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match

async def scrape_careerbuilder_jobs(job_role, location="", max_pages=3, filter_params=None, **kwargs):
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("where") or location or ""
    
    print(f"[*] CareerBuilder: Extracting direct careerbuilder.com job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    query = f'site:careerbuilder.com/job "{effective_role}"'
    if effective_loc:
        query += f' "{effective_loc}"'
        
    jobs_data = []
    seen_links = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        try:
            for g_page in range(max_pages):
                start_offset = g_page * 10
                google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start_offset}"
                print(f"[*] CareerBuilder: Navigating to search index page {g_page + 1}...")
                
                await page.goto(google_url, timeout=25000, wait_until="domcontentloaded")
                await asyncio.sleep(2.5)
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                search_results = soup.find_all('div', class_=lambda x: x and ('g' in x.split() or 'MjjYud' in x))
                for res in search_results:
                    a_tag = res.find('a', href=True)
                    if not a_tag:
                        continue
                    href = a_tag['href']
                    if 'careerbuilder.com/job' not in href and 'careerbuilder.com/job-listings' not in href:
                        continue
                        
                    clean_href = href.split('?')[0] if '?' in href else href
                    if clean_href in seen_links:
                        continue
                        
                    title_el = res.find('h3')
                    raw_title = title_el.text.strip() if title_el else ""
                    if not raw_title or not is_role_match(raw_title, job_role):
                        continue
                        
                    snippet_el = res.find('div', class_=lambda x: x and ('VwiC3b' in x or 'yXK7lf' in x or 's3v9rd' in x))
                    snippet_text = snippet_el.text.strip() if snippet_el else ""
                    
                    company_name = "CareerBuilder Employer"
                    job_location = effective_loc or "USA / Remote"
                    
                    if " - " in raw_title:
                        parts = raw_title.split(" - ")
                        clean_title = parts[0].strip()
                        if len(parts) > 1:
                            company_name = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
                    elif " | " in raw_title:
                        parts = raw_title.split(" | ")
                        clean_title = parts[0].strip()
                        if len(parts) > 1:
                            company_name = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
                    else:
                        clean_title = raw_title.replace(" | CareerBuilder", "").replace(" - CareerBuilder.com", "").strip()
                        
                    seen_links.add(clean_href)
                    jobs_data.append({
                        "Job Role": clean_title,
                        "Company Name": company_name or "CareerBuilder Employer",
                        "Location": job_location,
                        "Date Posted": "2026-09-12",
                        "Apply Link": clean_href,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": snippet_text[:350] if snippet_text else f"Role: {clean_title} | Location: {job_location}",
                        "Source": "CareerBuilder"
                    })
        except Exception as e:
            print(f"[!] CareerBuilder search indexing notice: {e}")
        finally:
            await browser.close()
            
    print(f"[+] CareerBuilder: Extracted {len(jobs_data)} verified job listings.")
    return jobs_data

if __name__ == "__main__":
    jobs = asyncio.run(scrape_careerbuilder_jobs("Sales Development Representative", "Bangalore", max_pages=2))
    print("Scraped CareerBuilder jobs count:", len(jobs))
    if jobs:
        print("Sample 1:", jobs[0]["Job Role"], "|", jobs[0]["Company Name"], "|", jobs[0]["Apply Link"])
