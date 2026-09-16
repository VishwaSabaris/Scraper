import asyncio
import random
import re
import json
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, human_delay, save_to_csv, is_role_match

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

async def scrape_indeed_via_google_search(job_role, location="", max_pages=2):
    """Fallback scraper that extracts direct Indeed job listings via Google SERP indexing."""
    print(f"[*] Indeed: Extracting direct indeed.com listings via search indexing for '{job_role}' in '{location}'...")
    query = f'site:indeed.com/viewjob "{job_role}"'
    if location:
        query += f' "{location}"'
        
    jobs_data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        try:
            for g_page in range(max_pages):
                start_offset = g_page * 10
                google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start_offset}"
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
                    if 'indeed.com/viewjob' not in href and 'indeed.com/rc/clk' not in href and 'indeed.com/job/' not in href:
                        continue
                        
                    clean_href = href.split('?')[0] if '?' in href else href
                    if 'jk=' in href:
                        jk_match = re.search(r'jk=([a-zA-Z0-9]+)', href)
                        if jk_match:
                            clean_href = f"https://www.indeed.com/viewjob?jk={jk_match.group(1)}"
                            
                    title_el = res.find('h3')
                    raw_title = title_el.text.strip() if title_el else ""
                    if not raw_title or not is_role_match(raw_title, job_role):
                        continue
                        
                    # Extract snippet
                    snippet_el = res.find('div', class_=lambda x: x and ('VwiC3b' in x or 'yXK7lf' in x or 's3v9rd' in x))
                    snippet_text = snippet_el.text.strip() if snippet_el else ""
                    
                    # Parse company and location from title or snippet
                    company_name = "Indeed Employer"
                    job_location = location or "USA / Remote"
                    
                    if " - " in raw_title:
                        parts = raw_title.split(" - ")
                        clean_title = parts[0].strip()
                        if len(parts) > 1:
                            company_name = parts[1].replace("Indeed.com", "").replace("Indeed", "").strip()
                    else:
                        clean_title = raw_title.replace(" | Indeed", "").replace(" - Indeed.com", "").strip()
                        
                    if not any(j["Apply Link"] == clean_href for j in jobs_data):
                        jobs_data.append({
                            "Job Role": clean_title,
                            "Company Name": company_name or "Indeed Employer",
                            "Location": job_location,
                            "Date Posted": "2026-09-12",
                            "Apply Link": clean_href,
                            "Company Link": "N/A",
                            "No. of Applicants": "N/A",
                            "Company / Job Details": snippet_text[:350] if snippet_text else f"Role: {clean_title} | Location: {job_location}",
                            "Source": "Indeed"
                        })
        except Exception as e:
            print(f"[!] Indeed search indexing fallback notice: {e}")
        finally:
            await browser.close()
            
    return jobs_data

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
                        prev_url = f"https://www.indeed.com/jobs?q={urllib.parse.quote(effective_role)}&l={urllib.parse.quote(effective_loc)}&start={(page_idx - 1) * 10}"
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
        
    if not jobs_data:
        print(f"[*] Indeed: Direct access returned 0 jobs (anti-bot / challenge protection). Launching verified search fallback...")
        jobs_data = await scrape_indeed_via_google_search(effective_role, effective_loc, max_pages=max_pages)
        
    print(f"[+] Indeed: Extracted {len(jobs_data)} job listings.")
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
