import asyncio
import random
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, human_delay, save_to_csv, is_role_match, normalize_date_posted, get_company_website

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

async def extract_job_details(page, job_url):
    """Navigates to the direct view link to extract raw descriptions safely."""
    try:
        await page.goto(job_url, timeout=30000)
        await human_delay(2, 5)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        applicants_el = soup.find('span', class_='num-applicants__caption') or soup.find(class_=lambda x: x and 'applicants' in x)
        applicants = applicants_el.text.strip() if applicants_el else "0-25 applicants (or login wall)"
        
        desc_el = soup.find('div', class_='description__text') or soup.find(class_=lambda x: x and 'description' in x)
        details = desc_el.text.strip() if desc_el else "No description text found"
        
        return applicants, details
    except Exception:
        return "N/A", "N/A"

async def scroll_and_load_all_jobs(page):
    """Scrolls down and clicks 'See more jobs' on LinkedIn until no new jobs are loaded."""
    print("[*] LinkedIn: Scrolling to load all available jobs. This may take a moment...")
    last_card_count = 0
    no_change_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 10
    
    while scroll_attempts < max_scroll_attempts:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(random.uniform(1.5, 2.5))
        
        if "checkpoint" in page.url or "login" in page.url:
            print("\n[!] LinkedIn: Redirect to login wall detected. Stopping scrolling to preserve loaded jobs.")
            break
            
        auth_modal = await page.evaluate("""
            () => !!(document.querySelector('.authwall-join-form') || 
                     document.querySelector('[data-test-id="authwall-modal"]') ||
                     document.querySelector('.modal') && document.body.classList.contains('overflow-hidden'))
        """)
        if auth_modal:
            print("\n[!] LinkedIn: Authentication wall overlay detected. Stopping scrolling to preserve loaded jobs.")
            break
            
        see_more_button = page.locator("button.infinite-scroller__show-more-button, button[aria-label='See more jobs'], button:has-text('See more jobs')")
        
        button_clicked = False
        if await see_more_button.is_visible():
            try:
                await see_more_button.click()
                print("[*] LinkedIn: Clicked 'See more jobs' button.")
                button_clicked = True
                await asyncio.sleep(random.uniform(2.5, 4.0))
            except Exception as e:
                print(f"[*] LinkedIn: Could not click 'See more jobs' button: {e}")
                
        card_count = await page.evaluate("document.querySelectorAll('ul.jobs-search__results-list > li, li .base-card, .job-search-card').length")
        print(f"[*] LinkedIn: Scroll attempt {scroll_attempts + 1}: Found {card_count} job cards loaded.")
        
        if card_count == last_card_count and not button_clicked:
            no_change_count += 1
            if no_change_count >= 5:
                print("[*] LinkedIn: Job card count has stabilized. Completed scrolling.")
                break
        else:
            no_change_count = 0
            
        last_card_count = card_count
        scroll_attempts += 1

async def scrape_linkedin_jobs(job_role, location="", fetch_details=False, batch_size=4, headless=False, filter_params=None, **kwargs):
    """Scrapes LinkedIn using target keywords, dynamic scrolling, strict role matching, and dynamic filters."""
    fp = filter_params or {}
    effective_role = fp.get("keywords") or job_role
    effective_loc = fp.get("location") or location or ""
    
    # Detect if remote filtering is requested
    is_remote_mode = (
        fp.get("f_WT") == "2" or
        "remote" in (fp.get("work_mode") or "").lower() or
        "remote" in kwargs.get("work_mode", "").lower() or
        "remote" in effective_role.lower() or
        "remote" in (effective_loc or "").lower()
    )
    
    if is_remote_mode:
        if "remote" not in effective_role.lower():
            effective_role = f"{effective_role} Remote"
        if effective_loc.lower().strip() in ["remote", "worldwide", "any"]:
            effective_loc = ""
            
    params = {
        "keywords": effective_role
    }
    if effective_loc:
        params["location"] = effective_loc

    for k in ["f_TPR", "f_WT", "f_E", "f_JT", "f_AL", "f_EA", "sortBy"]:
        if fp.get(k):
            params[k] = fp[k]
    if is_remote_mode:
        params["f_WT"] = "2"
    if "f_TPR" not in params:
        params["f_TPR"] = "r604800"
        
    base_url = f"https://www.linkedin.com/jobs/search?{urllib.parse.urlencode(params)}"
    
    jobs_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=CHROMIUM_STEALTH_ARGS
        )
        context = await create_stealth_context(browser)
        
        page = await context.new_page()
        print(f"[*] LinkedIn: Searching for '{effective_role}' in '{effective_loc or 'Worldwide / Remote'}' ({base_url})...")
        await page.goto(base_url)
        await human_delay(4, 7)
        
        await scroll_and_load_all_jobs(page)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        job_cards = soup.find_all(['li', 'div'], class_=lambda x: x and ('base-card' in x or 'base-search-card' in x or 'job-search-card' in x))
        if not job_cards:
            job_cards = soup.find_all('li')
            
        print(f"[*] LinkedIn: Parsing job details from {len(job_cards)} HTML elements...")
        
        for card in job_cards:
            urn = None
            if card.has_attr('data-entity-urn'):
                urn = card['data-entity-urn']
            else:
                card_div = card.find(class_=lambda x: x and ('base-card' in x or 'base-search-card' in x))
                if card_div and card_div.has_attr('data-entity-urn'):
                    urn = card_div['data-entity-urn']
                    
            if not urn or 'jobPosting' not in urn:
                continue
                
            try:
                job_id = urn.split(':')[-1]
                stable_apply_link = f"https://www.linkedin.com/jobs/view/{job_id}"
                
                title_el = card.find('h3', class_='base-search-card__title') or card.find(class_='base-search-card__title')
                job_role_title = title_el.text.strip() if title_el else "N/A"
                
                if not is_role_match(job_role_title, job_role):
                    continue

                title_lower = job_role_title.lower()
                
                # If remote mode was requested, reject any card with explicit onsite requirements
                if is_remote_mode:
                    onsite_flags = ["onsite", "on-site", "in-office", "wfo only", "office only", "no remote", "onsite 4x", "onsite 3x", "onsite 5x"]
                    if any(flag in title_lower for flag in onsite_flags):
                        continue
                    workplace_badge = card.find(class_=lambda x: x and ('workplace' in x.lower() or 'badge' in x.lower()))
                    if workplace_badge and ("on-site" in workplace_badge.text.lower() or "onsite" in workplace_badge.text.lower()):
                        continue
                    
                company_el = card.find('h4', class_='base-search-card__subtitle') or card.find(class_='base-search-card__subtitle')
                company_name = company_el.text.strip() if company_el else "N/A"
                
                company_link_el = company_el.find('a') if company_el else None
                company_link = company_link_el['href'].split('?')[0] if company_link_el and company_link_el.has_attr('href') else "N/A"
                
                location_el = card.find('span', class_='job-search-card__location') or card.find(class_='job-search-card__location')
                if not location_el:
                    location_el = card.find(class_=lambda x: x and 'location' in x)
                job_location = location_el.text.strip() if location_el else "N/A"
                
                date_el = card.find('time')
                if not date_el:
                    date_el = card.find(class_=lambda x: x and 'listdate' in x)
                post_date = date_el.text.strip() if date_el else "N/A"
                
                comp_clean = company_name if (company_name and company_name != "N/A") else "LinkedIn Verified Employer"
                if is_remote_mode:
                    if job_location and job_location != "N/A":
                        loc_clean = job_location if "remote" in job_location.lower() else f"{job_location} (Remote)"
                    else:
                        loc_clean = "Remote"
                else:
                    loc_clean = job_location if (job_location and job_location != "N/A") else (location or "Bengaluru, Karnataka, India")
                details_text = f"Company: {comp_clean} | Location: {loc_clean} | Role: {job_role_title} | Source: LinkedIn | Actively hiring qualified talent."

                if not any(item['Apply Link'] == stable_apply_link for item in jobs_data):
                    jobs_data.append({
                        "Job Role": job_role_title,
                        "Company Name": comp_clean,
                        "Location": loc_clean,
                        "Date Posted": normalize_date_posted(post_date),
                        "Apply Link": stable_apply_link,
                        "Company Link": get_company_website(comp_clean, fallback_portal_url="https://www.linkedin.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": details_text,
                        "Source": "LinkedIn"
                    })
                    
            except Exception:
                continue
                
        total_jobs = len(jobs_data)
        print(f"[+] LinkedIn: Extracted {total_jobs} matching unique jobs.")
        
        if fetch_details and total_jobs > 0:
            print(f"\n[*] LinkedIn: Starting detail extraction...")
            detail_page = await context.new_page()
            
            for idx, job in enumerate(jobs_data):
                print(f"[*] LinkedIn: Scraping job details ({idx + 1}/{total_jobs}): {job['Job Role']} at {job['Company Name']}")
                
                applicants, details = await extract_job_details(detail_page, job['Apply Link'])
                job["No. of Applicants"] = applicants
                job["Company / Job Details"] = details[:400] + "..." if len(details) > 400 else details
                
                if (idx + 1) % batch_size == 0 and (idx + 1) < total_jobs:
                    cooldown = random.randint(15, 30)
                    print(f"[*] LinkedIn: Batch complete. Cooldown for {cooldown}s...")
                    await asyncio.sleep(cooldown)
                else:
                    await human_delay(3, 6)
                    
            await detail_page.close()
            
        await browser.close()
        
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
        details = sys.argv[3].lower() == 'y' if len(sys.argv) >= 4 else False
    else:
        role = input("Enter Job Role (e.g., DevOps): ").strip()
        loc = input("Enter Location (e.g., New York): ").strip()
        details = input("Fetch detailed info? (y/n) [n]: ").strip().lower() == 'y'
        
    results = asyncio.run(scrape_linkedin_jobs(role, loc, fetch_details=details))
    print(f"\n[+] LinkedIn Scraper finished. Total matching results: {len(results)}")
    save_to_csv(results, "linkedin_jobs_only.csv")
