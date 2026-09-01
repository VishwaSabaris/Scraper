import asyncio
import os
import json
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match

async def scrape_wellfound_jobs(job_role, location=""):
    """Scrapes 100% direct wellfound.com job listings and apply links for any role/location."""
    query = f'site:wellfound.com/jobs "{job_role}"'
    if location:
        query += f' "{location}"'
        
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    print(f"[*] Wellfound: Extracting direct wellfound.com job listings for '{job_role}' in '{location}'...")
    
    user_dir = os.path.abspath("./wellfound_direct_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                channel="chrome",
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
        
        try:
            for g_page in range(3): # Scrape 3 pages of Google Search results (up to 30 results)
                start_offset = g_page * 10
                google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start_offset}"
                print(f"[*] Wellfound: Navigating to Google page {g_page + 1} ({google_url})...")
                
                await page.goto(google_url, timeout=25000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                # Accept Google consent if shown (only on first page)
                if g_page == 0:
                    consent_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree'), div:has-text('Accept all')")
                    if await consent_btn.count() > 0:
                        try:
                            await consent_btn.first.click()
                            await asyncio.sleep(2)
                        except Exception:
                            pass
                            
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                links = soup.find_all('a', href=True)
                
                for a in links:
                    href = a['href']
                    
                    # Unquote to resolve any URL-encoded characters (like %2F)
                    decoded_href = urllib.parse.unquote(href)
                    
                    # Extract target URL from Google redirect parameter if present
                    actual_url = decoded_href
                    if '/url?' in decoded_href:
                        parsed_url = urllib.parse.urlparse(decoded_href)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        target = query_params.get('q') or query_params.get('url')
                        if target:
                            actual_url = target[0]
                            
                    clean_href = actual_url.split('#')[0]
                    
                    # Identify if this is a search result link (contains h3 or is from wellfound.com)
                    h3_elem = a.find('h3')
                    is_search_result = False
                    if h3_elem:
                        is_search_result = True
                    elif 'wellfound.com/jobs/' in clean_href or 'wellfound.com/job/' in clean_href:
                        is_search_result = True
                        
                    # Skip generic Google links (e.g. settings, navigation)
                    if any(x in clean_href.lower() for x in ['google.com/', '/search?']):
                        is_search_result = False
                        
                    if is_search_result:
                        # Extract title from nested h3 if available to avoid breadcrumb garbage
                        if h3_elem:
                            title_text = h3_elem.text.strip()
                        else:
                            title_text = a.text.strip()
                            
                        if not title_text or title_text.lower() in ['read more', 'apply', 'wellfound']:
                            parent = a.find_parent(['div', 'h3'])
                            if parent:
                                h3_parent = parent.find('h3')
                                title_text = h3_parent.text.strip() if h3_parent else parent.text.strip()
                                
                        if "Read more" in title_text or len(title_text) < 3:
                            continue
                            
                        clean_title = title_text.split(" at ")[0].split(" | ")[0].split(" - ")[0].split("Wellfound")[0].strip()
                        
                        if not is_role_match(clean_title, job_role) and not is_role_match(title_text, job_role):
                            continue
                            
                        comp_name = "Various Employer"
                        if " at " in title_text:
                            comp_name = title_text.split(" at ")[-1].split(" | ")[0].split(" - ")[0].split("Wellfound")[0].strip()
                        elif " - " in title_text:
                            comp_name = title_text.split(" - ")[0].strip()
                            
                        company_link = clean_href.split('/jobs')[0] if '/jobs' in clean_href else clean_href
                        
                        if not any(item['Apply Link'] == clean_href for item in jobs_data):
                            jobs_data.append({
                                "Job Role": clean_title if len(clean_title) > 2 else title_text[:50],
                                "Company Name": comp_name,
                                "Location": location or "Remote / Various",
                                "Date Posted": "N/A",
                                "Apply Link": clean_href,
                                "Company Link": company_link,
                                "No. of Applicants": "N/A",
                                "Company / Job Details": title_text[:350],
                                "Source": "Wellfound"
                            })
        except Exception as err:
            print(f"[!] Direct Wellfound extraction note: {err}")
            
        await context.close()
        
    print(f"[+] Wellfound: Extracted {len(jobs_data)} direct wellfound.com job listings.")
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = input("Enter Job Role (e.g., DevOps Engineer): ").strip()
        loc = input("Enter Location (e.g., Chennai): ").strip()
        
    results = asyncio.run(scrape_wellfound_jobs(role, loc))
    print(f"\n[+] Wellfound Scraper finished. Total direct results: {len(results)}")
    save_to_csv(results, "wellfound_jobs_only.csv")
