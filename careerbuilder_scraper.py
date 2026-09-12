import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv
import random

async def scrape_careerbuilder_jobs(job_role, location="", headless=False, filter_params=None, **kwargs):
    """
    Scrapes direct careerbuilder.com job listings and apply links for any role/location.
    Supports dynamic filter parameters and deep scrolling extraction.
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
        for k in ["posted", "emp", "cb_workplace"]:
            if fp.get(k):
                params[k] = fp[k]
                
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
                await page.wait_for_selector(scroll_container_selector, timeout=15000)
            except Exception:
                print("[!] Scroll container not found or zero initial results on CareerBuilder.")
                
            no_new_cards_count = 0
            max_scroll_attempts = 25
            
            for attempt in range(max_scroll_attempts):
                # Parse current DOM HTML incrementally at each scroll step
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.find_all('article', {'data-testid': 'JobCard'})
                
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
                    comp_el = card.find(attrs={"data-testid": "company"})
                    comp_name = comp_el.text.strip() if comp_el else "CareerBuilder Employer"
                    
                    # Location
                    loc_el = card.find(attrs={"data-testid": "jobDetailLocation"})
                    loc_text = loc_el.text.strip() if loc_el else (location or "Remote / Various")
                    
                    # Date Posted
                    date_el = card.find(attrs={"data-testid": "jobFooterRecency"})
                    date_posted = date_el.text.strip() if date_el else "N/A"
                    
                    # Tags (salary, quick apply, etc.) for details
                    tags = [t.text.strip() for t in card.find_all(class_=lambda x: x and 'TagLabel' in x)]
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
                    
                print(f"[*] Scroll step {attempt+1}/{max_scroll_attempts}: Cards on DOM = {len(cards)} | New jobs: {new_extracted_in_step} | Total cumulative: {len(jobs_data)}")
                
                if new_extracted_in_step == 0:
                    no_new_cards_count += 1
                    if no_new_cards_count >= 3:
                        print("[+] Job list stabilized. Stopping scroll pagination.")
                        break
                else:
                    no_new_cards_count = 0
                    
                # Perform JS scroll to bottom of card container
                await page.evaluate("""() => {
                    const el = document.getElementById('card-scroll-container');
                    if (el) {
                        el.scrollTop = el.scrollHeight;
                        el.dispatchEvent(new Event('scroll', { bubbles: true }));
                    } else {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                }""")
                
                await asyncio.sleep(random.uniform(2.5, 3.5))
                
        except Exception as err:
            print(f"[!] CareerBuilder: Exception during scraping process: {err}")
            
        finally:
            await context.close()
            
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
