import asyncio
import os
import sys
import json
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match, human_delay, normalize_date_posted, get_company_website

async def scrape_glassdoor_jobs(job_role, location="", max_pages=1, headless=False, filter_params=None, **kwargs):
    """
    Scrapes job listings from glassdoor.com using Playwright non-headless persistent browser context.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("sc.keyword") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Glassdoor: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    user_dir = os.path.abspath("./glassdoor_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    async with async_playwright() as p:
        try:
            # Launch persistent browser context (like other scrapers)
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
        
        # 1. Resolve Location ID via AJAX if location is provided
        loc_id = ""
        loc_type = ""
        if effective_loc:
            # Set cookie / initialize by visiting the homepage
            try:
                await page.goto("https://www.glassdoor.com/Job/index.htm", timeout=20000)
                await asyncio.sleep(2)
            except Exception:
                pass
                
            ajax_url = f"https://www.glassdoor.com/findPopularLocationAjax.htm?maxLocationsToReturn=10&term={urllib.parse.quote(effective_loc)}"
            print(f"[*] Glassdoor: Resolving location details via AJAX ({ajax_url})...")
            try:
                await page.goto(ajax_url, timeout=20000)
                body_text = await page.locator("body").inner_text()
                data = json.loads(body_text)
                if isinstance(data, list) and len(data) > 0:
                    loc = data[0]
                    loc_id = loc.get('locationId', '')
                    loc_type = loc.get('locationType', '')
                    print(f"[+] Glassdoor: Resolved '{effective_loc}' to ID: {loc_id}, Type: {loc_type}")
            except Exception as e:
                print(f"[!] Glassdoor: Error resolving location ID: {e}")
                
        # 2. Navigate to search page
        formatted_role = urllib.parse.quote(effective_role)
        search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={formatted_role}"
        if loc_id and loc_type:
            search_url += f"&locT={loc_type}&locId={loc_id}"
        for k, v in fp.items():
            if k not in ["role", "location", "sc.keyword", "locT", "locId"]:
                search_url += f"&{k}={urllib.parse.quote(str(v))}"
            
        print(f"[*] Glassdoor: Navigating to search results ({search_url})...")
        try:
            await page.goto(search_url, timeout=40000)
            await asyncio.sleep(6)
            
            # Dismiss login wall overlay if it appears
            try:
                close_btn = page.locator("button[aria-label='Close'], button.CloseButton, button:has-text('Close'), .modal_closeIcon")
                if await close_btn.count() > 0:
                    await close_btn.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
                
            # Scroll and click "Show more jobs" button to load more jobs
            print("[*] Glassdoor: Loading more listings...")
            for load_idx in range(6):
                # Scroll to bottom to trigger rendering of the button
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2.5)
                
                show_more_btn = page.locator("button:has-text('Show more jobs'), [class*='JobsList_buttonWrapper'] button")
                if await show_more_btn.count() > 0:
                    try:
                        print(f"[*] Glassdoor: Clicking 'Show more jobs' button (attempt {load_idx + 1})...")
                        await show_more_btn.first.click(timeout=5000)
                        await asyncio.sleep(4)
                    except Exception as click_err:
                        print(f"[*] Glassdoor: Could not click button: {click_err}")
                        break
                else:
                    print("[*] Glassdoor: 'Show more jobs' button not visible. Completed loading.")
                    break
                
            # Parse final HTML results
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            cards = soup.find_all('li', class_=lambda x: x and 'JobsList_jobListItem' in x)
            print(f"[+] Glassdoor: Found {len(cards)} job card elements in DOM.")
            
            added_count = 0
            for card in cards:
                title_el = card.find('a', attrs={"data-test": "job-title"})
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                    continue
                    
                href = title_el['href']
                if href.startswith('/'):
                    apply_link = "https://www.glassdoor.com" + href
                else:
                    apply_link = href
                    
                company_el = card.find('span', class_=lambda x: x and 'EmployerProfile_compactEmployerName' in x) or card.find(class_=lambda x: x and 'employerName' in x.lower())
                company = company_el.text.strip() if company_el else "Glassdoor Employer"
                
                loc_el = card.find(class_=lambda x: x and 'location' in x.lower()) or card.find(id=lambda x: x and 'location' in x.lower())
                job_location = loc_el.text.strip() if loc_el else (location or "Remote / Various")
                
                age_el = card.find(attrs={"data-test": "job-age"}) or card.find(class_=lambda x: x and 'listingAge' in x)
                date_posted = age_el.text.strip() if age_el else "N/A"
                
                comp_clean = company if (company and company != "N/A") else "Glassdoor Verified Employer"
                loc_clean = job_location if (job_location and job_location != "N/A") else (location or "United States / Remote")
                details_text = f"Role: {title} | Company: {comp_clean} | Location: {loc_clean} | Source: Glassdoor"
                
                # Check for duplicates
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": comp_clean,
                        "Location": loc_clean,
                        "Date Posted": normalize_date_posted(date_posted),
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(comp_clean, fallback_portal_url="https://www.glassdoor.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": details_text,
                        "Source": "Glassdoor"
                    })
                    added_count += 1
                    
            print(f"[+] Glassdoor: Extracted {added_count} matching job listings.")
            
        except Exception as err:
            print(f"[!] Glassdoor: Exception during scraping process: {err}")
        finally:
            await context.close()
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = input("Enter Job Role (e.g., DevOps): ").strip()
        loc = input("Enter Location (e.g., New York): ").strip()
        
    results = asyncio.run(scrape_glassdoor_jobs(role, loc))
    print(f"\n[+] Glassdoor Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "glassdoor_jobs.csv")
