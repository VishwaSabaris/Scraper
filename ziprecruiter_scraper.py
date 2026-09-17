import asyncio
import os
import sys
import urllib.parse
import json
import urllib.request
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay, normalize_date_posted, get_company_website

def get_target_domain(location):
    """
    Determines the appropriate ZipRecruiter domain based on location.
    ZipRecruiter uses ziprecruiter.com for global/US searches and ziprecruiter.co.uk for UK.
    """
    if not location:
        return "ziprecruiter.com"

    loc_lower = location.lower().strip()
    uk_keywords = ["uk", "united kingdom", "london", "england", "scotland", "wales"]
    if any(k in loc_lower for k in uk_keywords):
        return "ziprecruiter.co.uk"
        
    return "ziprecruiter.com"

async def scrape_ziprecruiter_jobs(job_role, location="", max_pages=1, headless=False, filter_params=None, **kwargs):
    """
    Scrapes job listings from ZipRecruiter using Playwright persistent context.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("search") or job_role
    effective_loc = fp.get("location") or location or ""
    
    domain = get_target_domain(effective_loc)
    
    print(f"[*] ZipRecruiter: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}' (Target Domain: {domain})...")
    
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    params = {
        "search": effective_role.strip()
    }
    if effective_loc:
        params["location"] = effective_loc.strip()
    for k in ["days", "radius", "refine_by_employment", "refine_by_location_type", "refine_by_experience_level", "refine_by_salary", "location_explicitly_set"]:
        if fp.get(k):
            params[k] = fp[k]
            
    base_url = f"https://www.{domain}/jobs-search?{urllib.parse.urlencode(params)}"
        
    async with async_playwright() as p:
        try:
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
            for page_idx in range(1, max_pages + 1):
                if page_idx == 1:
                    url = base_url
                else:
                    params_page = dict(params)
                    params_page["page"] = page_idx
                    url = f"https://www.{domain}/jobs-search?{urllib.parse.urlencode(params_page)}"
                        
                print(f"[*] ZipRecruiter: Navigating to page {page_idx} ({url})...")
                
                await page.goto(url, timeout=50000)
                await asyncio.sleep(5)
                
                # Scroll slightly to ensure dynamic elements load
                await page.evaluate("window.scrollBy(0, 400);")
                await asyncio.sleep(2)
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                articles = soup.find_all("article")
                cards_two_pane = soup.find_all('div', class_=lambda x: x and 'job_result_two_pane_v2' in x)
                cards_in = soup.find_all('li', class_='job-listing')
                
                if len(articles) > 0:
                    cards = articles
                    structure_type = "article"
                elif cards_two_pane:
                    cards = cards_two_pane
                    structure_type = "two_pane"
                elif cards_in:
                    cards = cards_in
                    structure_type = "job-listing"
                else:
                    cards = soup.find_all('div', class_=lambda x: x and 'job_result' in x)
                    structure_type = "legacy"
                    
                print(f"[+] ZipRecruiter: Found {len(cards)} job card elements on page {page_idx} (structure: {structure_type}).")
                
                if not cards:
                    print("[*] No job cards found on this page. Stopping pagination.")
                    break
                    
                added_count = 0
                for card in cards:
                    if structure_type == "article":
                        # 1. Title
                        h2_el = card.find(["h2", "h3", "h1"])
                        if not h2_el:
                            continue
                        title = h2_el.text.strip()
                        if not title or title == "N/A":
                            continue
                            
                        if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                            continue
                            
                        # 2. Company Name & Link
                        comp_el = card.find(attrs={"data-testid": "job-card-company"}) or card.find(class_=lambda c: c and "company" in c)
                        company = comp_el.text.strip() if comp_el else "ZipRecruiter Employer"
                        comp_href = comp_el.get("href", "") if comp_el else ""
                        company_url = f"https://www.{domain}{comp_href}" if comp_href.startswith("/") else (comp_href or "N/A")
                        
                        # 3. Location
                        location_el = card.find(attrs={"data-testid": "job-card-location"}) or card.find(class_=lambda c: c and "location" in c)
                        job_location = location_el.text.strip() if location_el else (location or "Remote / Various")
                        
                        # 4. Salary
                        salary_el = card.find(attrs={"data-testid": lambda t: t and "salary" in t}) or card.find(class_=lambda c: c and ("salary" in c or "pay" in c))
                        salary_str = salary_el.text.strip() if salary_el else "N/A"
                        
                        # 5. Apply Link
                        link_el = card.find("a", href=True)
                        if not link_el:
                            continue
                        apply_href = link_el['href']
                        apply_link = f"https://www.{domain}{apply_href}" if apply_href.startswith("/") else apply_href
                        
                        # 6. Date Posted
                        time_el = card.find("time") or card.find(attrs={"data-testid": lambda t: t and "time" in t or "date" in t})
                        date_posted = time_el.text.strip() if time_el else "Recent"
                        date_posted = normalize_date_posted(date_posted)
                        
                        # 7. Job snippet / details
                        snippet_el = card.find(attrs={"data-testid": "job-card-snippet"}) or card.find("p")
                        comp_clean = company if (company and company != "N/A") else "ZipRecruiter Verified Employer"
                        loc_clean = job_location if (job_location and job_location != "N/A") else (location or "United States / Remote")
                        details_text = f"Company: {comp_clean} | Location: {loc_clean} | Salary: {salary_str} | {snippet_text}" if snippet_text else f"Role: {title} | Company: {comp_clean} | Location: {loc_clean} | Source: ZipRecruiter"
                        final_comp_url = company_url if (company_url and company_url != "N/A" and company_url.startswith("http")) else get_company_website(comp_clean, fallback_portal_url=f"https://www.{domain}")
                        
                        if not any(j["Apply Link"] == apply_link for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": comp_clean,
                                "Location": loc_clean,
                                "Date Posted": date_posted,
                                "Apply Link": apply_link,
                                "Company Link": final_comp_url,
                                "No. of Applicants": "Actively Hiring",
                                "Company / Job Details": details_text[:400] + "..." if len(details_text) > 400 else details_text,
                                "Source": "ZipRecruiter"
                            })
                            added_count += 1
                            
                print(f"[+] ZipRecruiter: Extracted {added_count} matching jobs from page {page_idx}.")
                if added_count == 0:
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
        loc = "Boston, MA"
        
    results = asyncio.run(scrape_ziprecruiter_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "ziprecruiter_jobs.csv")
