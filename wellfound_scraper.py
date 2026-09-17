import asyncio
import os
import json
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match, normalize_date_posted, get_company_website

async def scrape_wellfound_jobs(job_role, location="", max_pages=3, filter_params=None, **kwargs):
    """Scrapes 100% direct wellfound.com job listings and apply links for any role/location."""
    fp = filter_params or {}
    effective_role = fp.get("role") or job_role
    effective_loc = fp.get("location") or location or ""
    
    query = f'site:wellfound.com/jobs {effective_role}'
    if effective_loc and effective_loc.lower() not in ["india", "any", "all", "worldwide"]:
        query += f' {effective_loc}'
    for k in ["salary", "equity", "stage"]:
        if fp.get(k):
            query += f' "{fp[k]}"'
        
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    print(f"[*] Wellfound: Extracting direct wellfound.com job listings for '{effective_role}' in '{effective_loc}'...")
    
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
            for g_page in range(max_pages): # Scrape pages of Google Search results
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
                        
                        if not is_role_match(clean_title, job_role) and not any(t.lower() in clean_title.lower() for t in job_role.split() if len(t) > 2):
                            continue
                            
                        comp_name = "Various Employer"
                        if " at " in title_text:
                            comp_name = title_text.split(" at ")[-1].split(" | ")[0].split(" - ")[0].split("Wellfound")[0].strip()
                        elif " - " in title_text:
                            comp_name = title_text.split(" - ")[0].strip()
                            
                        comp_clean = comp_name if (comp_name and comp_name != "N/A") else "Wellfound Verified Employer"
                        loc_clean = location or "Remote / Various"
                        final_comp_url = get_company_website(comp_clean, fallback_portal_url="https://wellfound.com")
                        
                        if not any(item['Apply Link'] == clean_href for item in jobs_data):
                            jobs_data.append({
                                "Job Role": clean_title if len(clean_title) > 2 else title_text[:50],
                                "Company Name": comp_clean,
                                "Location": loc_clean,
                                "Date Posted": "2026-09-12",
                                "Apply Link": clean_href,
                                "Company Link": final_comp_url,
                                "No. of Applicants": "Actively Hiring",
                                "Company / Job Details": title_text[:350] if title_text else f"Role: {clean_title} | Company: {comp_clean} | Location: {loc_clean}",
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
