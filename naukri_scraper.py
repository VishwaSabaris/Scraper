import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay

async def scrape_naukri_jobs(job_role, location="", max_pages=1, headless=False):
    """
    Scrapes job listings from naukri.com using Playwright chromium persistent context.
    Returns a list of structured job dictionaries.
    """
    print(f"[*] Naukri: Fetching job listings for '{job_role}' in '{location or 'Any'}'...")
    
    user_dir = os.path.abspath("./naukri_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    # Format URL elements
    formatted_role_path = job_role.lower().strip().replace(" ", "-")
    # Keep only alphanumeric and hyphens for the path
    formatted_role_path = "".join(c for c in formatted_role_path if c.isalnum() or c == "-")
    
    formatted_location_path = ""
    if location:
        formatted_location_path = location.lower().strip().replace(" ", "-")
        formatted_location_path = "".join(c for c in formatted_location_path if c.isalnum() or c == "-")

    async with async_playwright() as p:
        try:
            # Launch persistent browser context to mimic realistic sessions
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
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
        
        try:
            # First initialize cookies by visiting the homepage
            try:
                await page.goto("https://www.naukri.com/", timeout=25000)
                await asyncio.sleep(2)
            except Exception:
                pass
                
            for page_idx in range(1, max_pages + 1):
                # Construct search URL for this page
                if location:
                    url = f"https://www.naukri.com/{formatted_role_path}-jobs-in-{formatted_location_path}?k={urllib.parse.quote(job_role)}&l={urllib.parse.quote(location)}&pageNo={page_idx}"
                else:
                    url = f"https://www.naukri.com/{formatted_role_path}-jobs?k={urllib.parse.quote(job_role)}&pageNo={page_idx}"
                    
                print(f"[*] Naukri: Navigating to page {page_idx} ({url})...")
                
                try:
                    await page.goto(url, timeout=40000)
                    # Human-like delay to ensure scripts execute and elements hydrate
                    await asyncio.sleep(6)
                    
                    # Scroll down slowly to trigger lazy loading of elements
                    await page.evaluate("window.scrollBy(0, 400);")
                    await asyncio.sleep(1)
                    await page.evaluate("window.scrollBy(0, 400);")
                    await asyncio.sleep(1)
                    
                    # Parse the page
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    cards = soup.find_all(class_=lambda x: x and 'cust-job-tuple' in str(x))
                    print(f"[+] Naukri: Found {len(cards)} job card elements on page {page_idx}.")
                    
                    if len(cards) == 0:
                        print("[-] Naukri: No job card elements found on this page. Stopping.")
                        break
                        
                    added_on_page = 0
                    for card in cards:
                        title_el = card.find("a", class_=lambda x: x and "title" in str(x)) or card.find("a")
                        if not title_el:
                            continue
                            
                        title = title_el.text.strip()
                        # Verify role matches
                        if not is_role_match(title, job_role):
                            continue
                            
                        apply_link = title_el.get("href", "")
                        if not apply_link.startswith("http"):
                            apply_link = "https://www.naukri.com" + apply_link
                            
                        # Extract company name
                        company_el = card.find(class_=lambda x: x and "comp-name" in str(x))
                        company = company_el.text.strip() if company_el else "Naukri Employer"
                        
                        # Extract location
                        loc_el = card.find(class_=lambda x: x and "locWdth" in str(x))
                        job_location = loc_el.text.strip() if loc_el else (location or "Remote / Various")
                        
                        # Extract date posted
                        date_el = card.find(class_=lambda x: x and "job-post-day" in str(x))
                        date_posted = date_el.text.strip() if date_el else "N/A"
                        
                        # Extract description / details
                        desc_el = card.find(class_=lambda x: x and "job-desc" in str(x))
                        details = desc_el.text.strip() if desc_el else "N/A"
                        
                        # Check for duplicates in current run
                        if not any(j["Apply Link"] == apply_link for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": company,
                                "Location": job_location,
                                "Date Posted": date_posted,
                                "Apply Link": apply_link,
                                "Company Link": "N/A",
                                "No. of Applicants": "N/A",
                                "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                                "Source": "Naukri"
                            })
                            added_on_page += 1
                            
                    print(f"[+] Naukri: Extracted {added_on_page} matching jobs from page {page_idx}.")
                    
                    if added_on_page == 0:
                        # If zero matching jobs extracted, break early
                        break
                        
                except Exception as page_err:
                    print(f"[!] Naukri: Error scraping page {page_idx}: {page_err}")
                    break
                    
        except Exception as run_err:
            print(f"[!] Naukri: Scraper execution failed: {run_err}")
        finally:
            await context.close()
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = input("Enter Job Role: ").strip()
        loc = input("Enter Location: ").strip()
        
    results = asyncio.run(scrape_naukri_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "naukri_jobs.csv")
