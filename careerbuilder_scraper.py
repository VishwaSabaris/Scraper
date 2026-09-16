import asyncio
import os
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match
import random

async def scrape_careerbuilder_fallback(role, location, max_results=30):
    """Fallback search indexing using DDGS for direct careerbuilder.com job-details postings."""
    try:
        from ddgs import DDGS
    except ImportError:
        return []
        
    jobs_data = []
    seen_links = set()
    
    queries = [
        f'site:careerbuilder.com/job-details "{role}"',
        f'site:careerbuilder.com/job "{role}"',
        f'site:careerbuilder.com/job-details {role}',
    ]
    if location and location.lower() not in ["any", "all", ""]:
        queries.insert(0, f'site:careerbuilder.com/job-details "{role}" "{location}"')
        
    for q in queries:
        if len(jobs_data) >= max_results:
            break
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=20))
                for r in results:
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    
                    if "careerbuilder.com" not in href or not ("/job-details/" in href or "/job/" in href):
                        continue
                        
                    clean_href = href.split("?")[0]
                    if clean_href in seen_links:
                        continue
                        
                    if not is_role_match(title, role):
                        continue
                        
                    company_name = "CareerBuilder Employer"
                    job_location = location or "USA / Remote"
                    clean_title = title
                    
                    # Parse title and company
                    if " - " in clean_title:
                        parts = clean_title.split(" - ")
                        clean_title = parts[0].strip()
                        if len(parts) > 1:
                            company_name = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
                    elif " | " in clean_title:
                        parts = clean_title.split(" | ")
                        clean_title = parts[0].strip()
                        if len(parts) > 1:
                            company_name = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
                            
                    clean_title = re.sub(r'(?i)\b(Job in|Jobs in|Job at|Jobs at|Apply Today at)\b.*$', '', clean_title).strip(' |-,')
                    if not clean_title or len(clean_title) < 3:
                        clean_title = title
                        
                    seen_links.add(clean_href)
                    jobs_data.append({
                        "Job Role": clean_title,
                        "Company Name": company_name or "CareerBuilder Employer",
                        "Location": job_location,
                        "Date Posted": "2026-09-12",
                        "Apply Link": clean_href,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": body[:350] if body else f"Role: {clean_title} | Location: {job_location}",
                        "Source": "CareerBuilder"
                    })
                    if len(jobs_data) >= max_results:
                        break
        except Exception:
            continue
            
    return jobs_data

async def scrape_careerbuilder_jobs(job_role, location="", headless=False, filter_params=None, **kwargs):
    """
    Scrapes direct careerbuilder.com job listings and apply links for any role/location.
    Supports dynamic filter parameters, direct browser rendering, and verified search indexing fallback.
    """
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("where") or location or ""
    
    print(f"[*] CareerBuilder: Extracting direct careerbuilder.com job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    user_dir = os.path.abspath("./careerbuilder_session_run")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    seen_links = set()
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
                channel="chrome",
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Build search URL
        params = {
            "q": effective_role.strip(),
            "where": effective_loc.strip()
        }
        for k, v in fp.items():
            if k not in ["role", "location", "q", "where"]:
                params[k] = v
                
        url = f"https://www.careerbuilder.com/job-listings/search?{urllib.parse.urlencode(params)}"
        
        print(f"[*] CareerBuilder: Navigating to search results page ({url})...")
        try:
            await page.goto(url, timeout=40000, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
            title = await page.title()
            if "Just a moment" in title or "challenge" in page.url.lower():
                print("[*] CareerBuilder: CAPTCHA / Bot detection challenge page detected! Waiting 10 seconds...")
                await asyncio.sleep(10)
            
            # Wait for scroll container to be available
            scroll_container_selector = "div#card-scroll-container"
            try:
                await page.wait_for_selector(scroll_container_selector, timeout=8000)
            except Exception:
                pass
                
            no_new_cards_count = 0
            max_scroll_attempts = 15
            
            for attempt in range(max_scroll_attempts):
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.find_all('article', {'data-testid': 'JobCard'})
                if not cards:
                    cards = soup.find_all('div', class_=lambda x: x and 'JobCard' in str(x))
                
                new_extracted_in_step = 0
                for card in cards:
                    title_el = card.find('a', href=True)
                    if not title_el:
                        continue
                    raw_title = title_el.text.strip()
                    if not raw_title or len(raw_title) < 2:
                        continue
                        
                    href = title_el['href']
                    apply_link = "https:" + href if href.startswith('//') else href
                    if apply_link.startswith('/'):
                        apply_link = "https://www.careerbuilder.com" + apply_link
                        
                    if apply_link in seen_links:
                        continue
                        
                    seen_links.add(apply_link)
                    new_extracted_in_step += 1
                    
                    # Company Name
                    comp_el = card.find(attrs={"data-testid": "company"}) or card.find(class_=lambda x: x and "company" in str(x).lower())
                    comp_name = comp_el.text.strip() if comp_el else "CareerBuilder Employer"
                    
                    # Location
                    loc_el = card.find(attrs={"data-testid": "jobDetailLocation"}) or card.find(class_=lambda x: x and "location" in str(x).lower())
                    loc_text = loc_el.text.strip() if loc_el else (effective_loc or "Remote / Various")
                    
                    # Date Posted
                    date_el = card.find(attrs={"data-testid": "jobFooterRecency"}) or card.find(class_=lambda x: x and "date" in str(x).lower())
                    date_posted = date_el.text.strip() if date_el else "N/A"
                    
                    # Tags
                    tags = [t.text.strip() for t in card.find_all(class_=lambda x: x and 'TagLabel' in str(x))]
                    details_text = f"Title: {raw_title} | Location: {loc_text}"
                    if tags:
                        details_text += " | Tags: " + ", ".join(tags)
                        
                    jobs_data.append({
                        "Job Role": raw_title,
                        "Company Name": comp_name,
                        "Location": loc_text,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details_text[:350],
                        "Source": "CareerBuilder"
                    })
                    
                if new_extracted_in_step == 0:
                    no_new_cards_count += 1
                    if no_new_cards_count >= 3:
                        break
                else:
                    no_new_cards_count = 0
                    
                await page.evaluate("""() => {
                    const el = document.getElementById('card-scroll-container');
                    if (el) {
                        el.scrollTop = el.scrollHeight;
                        el.dispatchEvent(new Event('scroll', { bubbles: true }));
                    } else {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                }""")
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
        except Exception as err:
            print(f"[!] CareerBuilder: Notice during direct navigation: {err}")
        finally:
            await context.close()
            
    # Fallback to search indexing if direct extraction is empty
    if not jobs_data:
        print("[*] CareerBuilder: Direct access yielded 0 listings. Launching search indexing fallback...")
        jobs_data = await scrape_careerbuilder_fallback(effective_role, effective_loc)
        
    print(f"[+] CareerBuilder: Extracted {len(jobs_data)} job listings successfully.")
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = input("Enter Job Role (e.g., DevOps): ").strip()
        loc = input("Enter Location (e.g., New York): ").strip()
        
    results = asyncio.run(scrape_careerbuilder_jobs(role, loc, headless=False))
    print(f"\n[+] CareerBuilder Scraper finished. Total direct results: {len(results)}")
    save_to_csv(results, "careerbuilder_jobs.csv")
