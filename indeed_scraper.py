import asyncio
import random
import re
import json
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, human_delay, save_to_csv

def is_role_match(job_title, requested_role):
    """Strictly matches requested job role terms against job titles to prevent irrelevant job listings."""
    if not job_title or job_title == "N/A":
        return False
        
    title_lower = job_title.lower()
    req_terms = [t.strip().lower() for t in requested_role.split() if len(t.strip()) > 1]
    
    if any(term in title_lower for term in req_terms):
        return True
        
    if "devops" in requested_role.lower():
        devops_synonyms = ["sre", "site reliability", "cloud engineer", "platform engineer", "infrastructure engineer", "sysadmin"]
        if any(syn in title_lower for syn in devops_synonyms):
            return True
            
    return False

async def check_and_wait_for_challenge(page, timeout_sec=15):
    """Detects Cloudflare/Indeed verification challenges and waits automatically."""
    challenge_detected = False
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout_sec:
        url = page.url.lower()
        title = (await page.title()).lower()
        content = await page.content()
        
        is_challenge = (
            "challenges" in url or 
            "cloudflare" in url or 
            "just a moment" in title or 
            "verify you are human" in content.lower() or
            "cf-challenge" in content.lower() or
            "security check" in title
        )
        
        if is_challenge:
            if not challenge_detected:
                print("[*] Indeed: Automated anti-bot challenge check in progress...")
                challenge_detected = True
            await asyncio.sleep(2)
        else:
            if challenge_detected:
                print("[+] Indeed: Page loaded successfully.")
            break

async def scrape_indeed_jobs(job_role, location="", max_pages=3, headless=False, filter_params=None, **kwargs):
    """Scrapes Indeed using stealth Playwright, dynamic filters, and pagination."""
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("l") or location or ""
    
    jobs_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=CHROMIUM_STEALTH_ARGS
        )
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        for page_idx in range(max_pages):
            params = {
                "q": effective_role,
                "start": page_idx * 10
            }
            if effective_loc:
                params["l"] = effective_loc
            for k in ["fromage", "jt", "radius", "sort"]:
                if fp.get(k):
                    params[k] = fp[k]
                    
            target_url = f"https://www.indeed.com/jobs?{urllib.parse.urlencode(params)}"
            print(f"[*] Indeed: Navigating to page {page_idx + 1} ({target_url})...")
            
            try:
                navigated_via_click = False
                if page_idx > 0:
                    next_button = page.locator("a[aria-label='Next Page'], a[data-testid='pagination-page-next'], a[aria-label='Next'], nav[role='navigation'] a:has-text('Next')")
                    if await next_button.count() > 0 and await next_button.first.is_visible():
                        try:
                            print("[*] Indeed: Clicking 'Next Page' button in browser UI...")
                            await next_button.first.click()
                            navigated_via_click = True
                            await human_delay(3, 5)
                        except Exception:
                            pass
                
                if not navigated_via_click:
                    if page_idx > 0:
                        prev_url = f"https://www.indeed.com/jobs?q={formatted_role}&l={formatted_location}&start={(page_idx - 1) * 10}"
                        await page.set_extra_http_headers({"Referer": prev_url})
                    else:
                        await page.set_extra_http_headers({"Referer": "https://www.google.com/"})
                        
                    await page.goto(target_url, timeout=35000, wait_until="domcontentloaded")
                    await human_delay(3, 6)
                
                # Automated challenge wait
                await check_and_wait_for_challenge(page)
                
                try:
                    await page.wait_for_selector(".job_seen_beacon, .resultContent, script#mosaic-data, [data-jk], div.jobsearch-ResultsList", timeout=8000)
                except Exception:
                    pass
                
                await page.evaluate("window.scrollBy(0, 400);")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                parsed_via_json = False
                
                mosaic_scripts = soup.find_all('script', string=re.compile(r'mosaicProviderJobCardsModel|mosaic-provider-jobcards'))
                if not mosaic_scripts:
                    mosaic_scripts = soup.find_all('script', id='mosaic-data')
                    
                for script in mosaic_scripts:
                    if not script.string:
                        continue
                    try:
                        json_match = re.search(r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.+?\});', script.string)
                        if not json_match:
                            json_match = re.search(r'("mosaicProviderJobCardsModel":\s*\{.+?\})\s*;\s*', script.string)
                            
                        if json_match:
                            json_text = json_match.group(1)
                            if json_text.startswith('"mosaicProviderJobCardsModel":'):
                                json_text = "{" + json_text + "}"
                            json_data = json.loads(json_text)
                            
                            results = []
                            if 'metaData' in json_data:
                                results = json_data.get('metaData', {}).get('mosaicProviderJobCardsModel', {}).get('results', [])
                            elif 'mosaicProviderJobCardsModel' in json_data:
                                results = json_data.get('mosaicProviderJobCardsModel', {}).get('results', [])
                                
                            if results:
                                added_count = 0
                                for job in results:
                                    job_key = job.get('jobkey')
                                    if not job_key:
                                        continue
                                        
                                    title = job.get('title', 'N/A')
                                    if not is_role_match(title, job_role):
                                        continue
                                        
                                    company = job.get('company', 'N/A')
                                    job_location = job.get('formattedLocation', 'N/A')
                                    post_date = job.get('formattedRelativeTime', 'N/A')
                                    apply_link = f"https://www.indeed.com/viewjob?jk={job_key}"
                                    
                                    company_slug = job.get('companyResponsiveId')
                                    company_link = f"https://www.indeed.com/cmp/{company_slug}" if company_slug else "N/A"
                                    snippet = job.get('snippet', 'N/A')
                                    
                                    snippet_soup = BeautifulSoup(snippet, 'html.parser')
                                    clean_snippet = snippet_soup.get_text().strip()
                                    
                                    if not any(item['Apply Link'] == apply_link for item in jobs_data):
                                        jobs_data.append({
                                            "Job Role": title,
                                            "Company Name": company,
                                            "Location": job_location,
                                            "Date Posted": post_date,
                                            "Apply Link": apply_link,
                                            "Company Link": company_link,
                                            "No. of Applicants": "N/A",
                                            "Company / Job Details": clean_snippet[:400] + "..." if len(clean_snippet) > 400 else clean_snippet,
                                            "Source": "Indeed"
                                        })
                                        added_count += 1
                                parsed_via_json = True
                                print(f"[+] Indeed: Successfully parsed page {page_idx + 1} using Mosaic JSON ({added_count} matching jobs).")
                                break
                    except Exception:
                        continue
                
                # DOM Fallback
                if not parsed_via_json:
                    cards = soup.find_all('div', class_=lambda x: x and 'job_seen_beacon' in x)
                    if not cards:
                        cards = soup.find_all(class_='resultContent')
                    if not cards:
                        cards = soup.find_all('td', class_='resultContent')
                        
                    added_count = 0
                    for card in cards:
                        try:
                            title_el = card.find('h2', class_='jobTitle') or card.find(class_='jobTitle')
                            title = title_el.text.strip() if title_el else "N/A"
                            if not is_role_match(title, job_role):
                                continue
                                
                            company_el = card.find('span', data_testid='company-name') or card.find(class_='companyName')
                            company = company_el.text.strip() if company_el else "N/A"
                            
                            location_el = card.find('div', data_testid='text-location') or card.find(class_='companyLocation')
                            job_location = location_el.text.strip() if location_el else "N/A"
                            
                            date_el = card.find('span', class_='date') or card.find(class_=lambda x: x and 'date' in x)
                            post_date = date_el.text.strip() if date_el else "N/A"
                            
                            link_el = title_el.find('a') if title_el else None
                            if link_el and link_el.has_attr('href'):
                                href = link_el['href']
                                apply_link = "https://www.indeed.com" + href if href.startswith('/') else href
                            else:
                                apply_link = "N/A"
                                
                            if apply_link != "N/A" and not any(item['Apply Link'] == apply_link for item in jobs_data):
                                jobs_data.append({
                                    "Job Role": title,
                                    "Company Name": company,
                                    "Location": job_location,
                                    "Date Posted": post_date,
                                    "Apply Link": apply_link,
                                    "Company Link": "N/A",
                                    "No. of Applicants": "N/A",
                                    "Company / Job Details": "N/A",
                                    "Source": "Indeed"
                                })
                                added_count += 1
                        except Exception:
                            continue
                    if added_count > 0:
                        print(f"[+] Indeed: Extracted {added_count} matching jobs from DOM on page {page_idx + 1}.")
                        
            except Exception as e:
                print(f"[!] Indeed: Error during page load: {e}")
                break
                
        await browser.close()
        
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
        pages = int(sys.argv[3]) if len(sys.argv) >= 4 else 2
    else:
        role = input("Enter Job Role (e.g., DevOps): ").strip()
        loc = input("Enter Location (e.g., New York): ").strip()
        pages_input = input("Max pages to scrape [default 2]: ").strip()
        pages = int(pages_input) if pages_input.isdigit() else 2
        
    results = asyncio.run(scrape_indeed_jobs(role, loc, max_pages=pages))
    print(f"\n[+] Indeed Scraper finished. Total matching results: {len(results)}")
    save_to_csv(results, "indeed_jobs_only.csv")
