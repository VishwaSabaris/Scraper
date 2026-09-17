import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT, save_to_csv, is_role_match, normalize_date_posted, get_company_website

async def scrape_careerjet_jobs(job_role, location="", max_pages=1, headless=True, filter_params=None, **kwargs):
    """
    Scrapes job listings from careerjet.co.in using Playwright persistent context.
    Supports dynamic filter parameters (nw, cp, ct, etc.) and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("s") or job_role
    effective_loc = fp.get("l") or location or ""
    
    print(f"[*] Careerjet: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    user_dir = os.path.abspath("./careerjet_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
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
        await page.add_init_script(STEALTH_JS_INIT)
        
        try:
            # First visit homepage to establish session and solve Turnstile challenge
            try:
                await page.goto("https://www.careerjet.co.in/", timeout=25000)
                await asyncio.sleep(7)
            except Exception:
                pass
                
            for page_idx in range(1, max_pages + 1):
                params = {
                    "s": effective_role,
                    "p": page_idx
                }
                if effective_loc:
                    params["l"] = effective_loc
                for k in ["nw", "cp", "ct", "radius", "sort", "f"]:
                    if fp.get(k):
                        params[k] = fp[k]
                        
                url = f"https://www.careerjet.co.in/jobs?{urllib.parse.urlencode(params)}"
                print(f"[*] Careerjet: Navigating to page {page_idx} ({url})...")
                
                try:
                    await page.goto(url, timeout=35000)
                    await asyncio.sleep(4)
                    
                    # Scroll down to load elements
                    await page.evaluate("window.scrollBy(0, 400);")
                    await asyncio.sleep(1)
                    
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    cards = soup.select("article.job, .job-list article, article, .job")
                    print(f"[+] Careerjet: Found {len(cards)} card elements on page {page_idx}.")
                    
                    if not cards:
                        break
                            
                    added_on_page = 0
                    for card in cards:
                        title_el = card.select_one("header h2 a, h2 a, a.title, h2")
                        if not title_el:
                            continue
                            
                        title = title_el.text.strip()
                        if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                            continue
                            
                        apply_link = title_el.get("href", "") if title_el.name == "a" else (title_el.find("a").get("href") if title_el.find("a") else "")
                        if apply_link and not apply_link.startswith("http"):
                            apply_link = "https://www.careerjet.co.in" + apply_link
                            
                        comp_el = card.select_one(".company_compact, .company, p.company, a[href*='/company/']")
                        company = comp_el.text.strip() if comp_el else "Careerjet Employer"
                        
                        comp_url = "N/A"
                        if comp_el and comp_el.name == "a" and comp_el.get("href"):
                            comp_href = comp_el.get("href")
                            comp_url = f"https://www.careerjet.co.in{comp_href}" if comp_href.startswith("/") else comp_href
                        
                        loc_el = card.select_one(".location_compact, .locations, ul.location")
                        job_location = loc_el.text.strip() if loc_el else (location or "India")
                        
                        sal_el = card.select_one(".salary, ul.salary")
                        salary = sal_el.text.strip() if sal_el else "Not disclosed"
                        
                        desc_el = card.select_one(".desc, .job-description, p")
                        desc = desc_el.text.strip() if desc_el else ""
                        
                        date_el = card.select_one(".badge_date, .date, time, span.badge")
                        date_posted = date_el.text.strip() if date_el else "Recent"
                        date_posted = normalize_date_posted(date_posted)
                        
                        comp_clean = company if (company and company != "Careerjet Employer" and company != "N/A") else "Careerjet Verified Employer"
                        loc_clean = job_location if (job_location and job_location != "N/A") else (location or "Bengaluru, Karnataka, India")
                        details = f"Company: {comp_clean} | Location: {loc_clean} | Salary: {salary} | {desc}" if desc else f"Role: {title} | Company: {comp_clean} | Location: {loc_clean} | Source: Careerjet"
                        final_comp_url = comp_url if (comp_url and comp_url != "N/A" and comp_url.startswith("http")) else get_company_website(comp_clean, fallback_portal_url="https://www.careerjet.co.in")

                        if not any(j["Apply Link"] == apply_link for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": comp_clean,
                                "Location": loc_clean,
                                "Date Posted": date_posted,
                                "Apply Link": apply_link,
                                "Company Link": final_comp_url,
                                "No. of Applicants": "Actively Hiring",
                                "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                                "Source": "Careerjet"
                            })
                            added_on_page += 1
                            
                    print(f"[+] Careerjet: Extracted {added_on_page} matching jobs from page {page_idx}.")
                    if added_on_page == 0:
                        break
                        
                    await asyncio.sleep(2)
                    
                except Exception as err:
                    print(f"[!] Careerjet: Error on page {page_idx}: {err}")
                    break
                    
        finally:
            await context.close()
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = "Sales Development Representative"
        loc = "Bangalore"
        
    results = asyncio.run(scrape_careerjet_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "careerjet_jobs.csv")
