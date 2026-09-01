import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match, human_delay

async def scrape_jooble_jobs(job_role, location="", max_pages=2, headless=False):
    """
    Scrapes job listings from in.jooble.org using Playwright persistent browser context.
    Returns a list of structured job dictionaries.
    """
    role_slug = re.sub(r'[^a-zA-Z0-9]+', '-', job_role.strip().lower()).strip('-')
    loc_slug = re.sub(r'[^a-zA-Z0-9]+', '-', location.strip().lower()).strip('-') if location else ""
    
    print(f"[*] Jooble: Fetching job listings for '{job_role}' in '{location or 'India'}'...")
    
    user_dir = os.path.abspath("./jooble_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        suggested_pages = None
        
        for page_idx in range(1, max_pages + 1):
            if suggested_pages and page_idx > suggested_pages:
                print(f"[*] Page {page_idx} is beyond available suggested pages ({suggested_pages}). Stopping.")
                break
                
            if loc_slug:
                base_url = f"https://in.jooble.org/jobs-{role_slug}/{loc_slug}"
            else:
                base_url = f"https://in.jooble.org/jobs-{role_slug}"
                
            url = f"{base_url}?p={page_idx}" if page_idx > 1 else base_url
            print(f"[*] Jooble: Navigating to page {page_idx} ({url})...")
            
            retries = 3
            success = False
            
            for attempt in range(retries):
                try:
                    await page.goto(url, timeout=40000, wait_until="domcontentloaded")
                    await human_delay(3, 5)
                    
                    # Check for Cloudflare Turnstile verification challenge
                    title = await page.title()
                    if "Just a moment" in title or "challenge" in page.url.lower():
                        print(f"[*] Jooble: Cloudflare challenge detected on page {page_idx} (attempt {attempt+1}/{retries}), waiting...")
                        await asyncio.sleep(8)
                        title = await page.title()
                        
                    # Scroll to ensure job listings load completely
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                    await asyncio.sleep(2)
                    
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Parse total vacancies on page 1
                    if page_idx == 1:
                        try:
                            for tag in soup.find_all(string=True):
                                text = tag.strip()
                                if "vacanc" in text.lower() or "vacancy" in text.lower():
                                    numbers = re.findall(r'\b\d+(?:,\d+)*\b', text)
                                    if numbers:
                                        raw_num = numbers[0].replace(',', '')
                                        total_vacancies = int(raw_num)
                                        suggested_pages = (total_vacancies + 19) // 20
                                        print(f"[+] Jooble: Found {total_vacancies} vacancies ({suggested_pages} pages available on website).")
                                        break
                        except Exception:
                            pass
                            
                    success = True
                    break
                except Exception as err:
                    print(f"[!] Jooble page {page_idx} attempt {attempt+1}/{retries} failed: {err}")
                    await asyncio.sleep(6)
            
            if not success:
                print(f"[-] Skipping page {page_idx} after {retries} failed attempts.")
                continue
                
            try:
                
                job_links = soup.find_all('a', href=True)
                desc_links = [a for a in job_links if '/desc/' in a['href'] or '/away/' in a['href']]
                
                for a in desc_links:
                    href = a['href']
                    if href.startswith('/'):
                        apply_link = 'https://in.jooble.org' + href
                    else:
                        apply_link = href
                        
                    job_title = a.text.strip()
                    if not job_title or len(job_title) < 2:
                        continue
                        
                    if not is_role_match(job_title, job_role):
                        continue
                        
                    parent = a.find_parent(['article', 'div'])
                    comp_name = "Jooble Employer"
                    loc_text = location or "India"
                    details_text = job_title
                    
                    if parent:
                        parent_str = parent.text.strip().replace('\n', ' ')
                        details_text = parent_str[:350]
                        
                        # Extract potential company name & location snippet
                        text_parts = [p.strip() for p in parent_str.split('  ') if p.strip()]
                        if len(text_parts) > 1:
                            comp_name = text_parts[1][:50]
                            
                    if not any(item['Apply Link'] == apply_link for item in jobs_data):
                        jobs_data.append({
                            "Job Role": job_title,
                            "Company Name": comp_name,
                            "Location": loc_text,
                            "Date Posted": "N/A",
                            "Apply Link": apply_link,
                            "Company Link": "N/A",
                            "No. of Applicants": "N/A",
                            "Company / Job Details": details_text,
                            "Source": "Jooble"
                        })
                        
            except Exception as err:
                print(f"[!] Jooble page {page_idx} error: {err}")
                break
                
        await context.close()
        
    print(f"[+] Jooble: Extracted {len(jobs_data)} job listings.")
    return jobs_data

if __name__ == "__main__":
    pages = 2
    if len(sys.argv) >= 4:
        role = sys.argv[1]
        loc = sys.argv[2]
        pages = int(sys.argv[3])
    elif len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = input("Enter Job Role (e.g., Python Developer): ").strip()
        loc = input("Enter Location (e.g., Chennai): ").strip()
        pages_input = input("Max pages to scrape [default 2]: ").strip()
        pages = int(pages_input) if pages_input.isdigit() else 2
        
    results = asyncio.run(scrape_jooble_jobs(role, loc, max_pages=pages))
    print(f"\n[+] Jooble Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "jooble_jobs.csv")
