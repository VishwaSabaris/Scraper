import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay, normalize_date_posted, get_company_website

async def scrape_naukri_jobs(job_role, location="", max_pages=1, headless=False, filter_params=None, **kwargs):
    """
    Scrapes job listings from naukri.com using Playwright chromium persistent context.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("keywords") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Naukri: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    user_dir = os.path.abspath("./naukri_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    # Format URL elements
    formatted_role_path = effective_role.lower().strip().replace(" ", "-")
    formatted_role_path = "".join(c for c in formatted_role_path if c.isalnum() or c == "-")
    
    formatted_location_path = ""
    if effective_loc:
        formatted_location_path = effective_loc.lower().strip().replace(" ", "-")
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
                extra_params = {
                    "k": effective_role,
                    "pageNo": page_idx
                }
                if effective_loc:
                    extra_params["l"] = effective_loc
                for k, v in fp.items():
                    if k not in ["role", "location", "k", "l", "pageNo"]:
                        extra_params[k] = v
                        
                query_str = urllib.parse.urlencode(extra_params)
                if formatted_location_path and formatted_location_path not in ["india", "remote", "any", "all", "worldwide"]:
                    url = f"https://www.naukri.com/{formatted_role_path}-jobs-in-{formatted_location_path}?{query_str}"
                else:
                    url = f"https://www.naukri.com/{formatted_role_path}-jobs?{query_str}"
                    
                print(f"[*] Naukri: Navigating to page {page_idx} ({url})...")
                
                try:
                    await page.goto(url, timeout=40000)
                    # Human-like delay to ensure scripts execute and elements hydrate
                    await asyncio.sleep(5)
                    
                    # Scroll down slowly to trigger lazy loading of elements
                    await page.evaluate("window.scrollBy(0, 500);")
                    await asyncio.sleep(1)
                    await page.evaluate("window.scrollBy(0, 500);")
                    await asyncio.sleep(1)
                    
                    # Parse the page
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    cards = soup.select(".srp-jobtuple-wrapper, .cust-job-tuple, article.jobTuple, .jobTuple, [data-job-id]")
                    print(f"[+] Naukri: Found {len(cards)} job card elements on page {page_idx}.")
                    
                    if len(cards) == 0:
                        print("[-] Naukri: No job card elements found on this page. Stopping.")
                        break
                        
                    added_on_page = 0
                    for card in cards:
                        title_el = card.select_one("a.title, .title a, a[href*='job-listings'], h2 a, a")
                        if not title_el:
                            continue
                            
                        title = title_el.text.strip()
                        # Verify role matches
                        if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
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
                        
                        if not any(j["Apply Link"] == apply_link for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": company or "Naukri Verified Employer",
                                "Location": job_location or "Bengaluru, Karnataka, India",
                                "Date Posted": normalize_date_posted(date_posted),
                                "Apply Link": apply_link,
                                "Company Link": get_company_website(company, fallback_portal_url="https://www.naukri.com"),
                                "No. of Applicants": "Actively Hiring",
                                "Company / Job Details": details[:400] + "..." if (details and details != "N/A" and len(details) > 400) else (details if (details and details != "N/A") else f"Role: {title} | Company: {company} | Location: {job_location}"),
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
