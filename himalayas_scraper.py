import asyncio
import datetime
import os
import sys
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay
from request_client import execute_async_request

def build_himalayas_url(job_role, location=""):
    """
    Generates the exact accurate Himalayas web listing URL for a given role and location.
    """
    role_clean = job_role.lower().strip() if job_role else ""
    role_slug = "-".join(filter(None, "".join(c if c.isalnum() or c == " " else "" for c in role_clean).split()))

    loc_clean = location.lower().strip() if location else ""
    if loc_clean in ["uk", "united kingdom", "gb", "great britain"]:
        location_slug = "united-kingdom"
    elif loc_clean in ["us", "usa", "united states", "united states of america"]:
        location_slug = "united-states"
    else:
        location_slug = "-".join(filter(None, "".join(c if c.isalnum() or c == " " else "" for c in loc_clean).split()))

    if location_slug and role_slug:
        return f"https://himalayas.app/jobs/countries/{location_slug}/{role_slug}?view=filters&src=adv"
    elif role_slug:
        return f"https://himalayas.app/jobs/{role_slug}?view=filters&src=adv"
    elif location_slug:
        return f"https://himalayas.app/jobs/countries/{location_slug}?view=filters&src=adv"
    else:
        return "https://himalayas.app/jobs?view=filters&src=adv"

async def scrape_himalayas_jobs_api(job_role, location="", max_pages=5, filter_params=None, **kwargs):
    """
    Scrapes job listings using Himalayas official public search JSON API.
    Fast, reliable, and completely bypasses Cloudflare bot checks.
    """
    fp = filter_params or {}
    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("country") or location or ""
    
    target_web_url = build_himalayas_url(effective_role, effective_loc)
    print(f"[*] Himalayas Web Link: {target_web_url}")
    print(f"[*] Himalayas: Fetching job listings via API for '{effective_role}' in '{effective_loc or 'Worldwide'}'...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    params = {}
    if effective_role:
        params["q"] = effective_role
    if effective_loc:
        params["country"] = effective_loc
    for k in ["experience_level", "employment_type", "min_salary", "skills", "timezone", "sort"]:
        if fp.get(k):
            params[k] = fp[k]
        
    jobs_data = []
    
    for page_idx in range(1, max_pages + 1):
        params["page"] = page_idx
        api_url = "https://himalayas.app/jobs/api/search"
        
        try:
            resp = await execute_async_request(api_url, method="GET", headers=headers, params=params, timeout=15)
            if not resp or resp.status_code != 200:
                print(f"[!] Himalayas API returned status {resp.status_code if resp else 'None'} on page {page_idx}.")
                break
                
            data = resp.json()
            raw_jobs = data.get("jobs", []) if isinstance(data, dict) else []
            
            if not raw_jobs:
                print(f"[-] Himalayas: No jobs returned on page {page_idx}. Stopping.")
                break
                
            added_on_page = 0
            for item in raw_jobs:
                title = item.get("title", "")
                if job_role and not is_role_match(title, job_role):
                    continue
                    
                loc_list = item.get("locationRestrictions", [])
                job_location = ", ".join(loc_list) if loc_list else "Worldwide / Remote"
                
                # Location filtering check
                if location:
                    loc_lower = location.lower().strip()
                    if loc_lower in ["uk", "united kingdom", "gb", "great britain"]:
                        loc_matches = ["united kingdom", "uk", "great britain", "worldwide", "anywhere"]
                    elif loc_lower in ["us", "usa", "united states"]:
                        loc_matches = ["united states", "us", "usa", "worldwide", "anywhere"]
                    else:
                        loc_matches = [loc_lower, "worldwide", "anywhere"]
                        
                    if loc_list and not any(any(m in l.lower() for m in loc_matches) for l in loc_list):
                        continue
                        
                # Format Date Posted
                pub_date = item.get("pubDate")
                date_str = "N/A"
                if pub_date:
                    try:
                        date_str = datetime.datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = "N/A"
                        
                apply_link = item.get("applicationLink") or item.get("guid") or ""
                if not apply_link:
                    continue
                    
                company_slug = item.get("companySlug", "")
                company_link = f"https://himalayas.app/companies/{company_slug}" if company_slug else "N/A"
                
                emp_type = item.get("employmentType", "")
                seniority = ", ".join(item.get("seniority", [])) if isinstance(item.get("seniority"), list) else ""
                cats = ", ".join(item.get("categories", [])) if isinstance(item.get("categories"), list) else ""
                
                details_parts = []
                if emp_type: details_parts.append(f"Type: {emp_type}")
                if seniority: details_parts.append(f"Seniority: {seniority}")
                if cats: details_parts.append(f"Categories: {cats}")
                details = " | ".join(details_parts) if details_parts else "N/A"
                
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": item.get("companyName", "Himalayas Employer"),
                        "Location": job_location,
                        "Date Posted": date_str,
                        "Apply Link": apply_link,
                        "Company Link": company_link,
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details,
                        "Source": "Himalayas"
                    })
                    added_on_page += 1
                    
            print(f"[+] Himalayas: Extracted {added_on_page} matching jobs from page {page_idx}.")
            await human_delay(0.3, 0.8)
            
        except Exception as err:
            print(f"[!] Himalayas API Error on page {page_idx}: {err}")
            break
            
    return jobs_data

async def scrape_himalayas_jobs_playwright(job_role, location="", max_pages=5, headless=False):
    """
    Playwright fallback scraper for Himalayas HTML pages.
    """
    user_dir = os.path.abspath("./himalayas_session")
    os.makedirs(user_dir, exist_ok=True)
    
    base_url = build_himalayas_url(job_role, location)
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
        
        try:
            for page_idx in range(1, max_pages + 1):
                url = f"{base_url}&page={page_idx}" if "?" in base_url else f"{base_url}?page={page_idx}"
                print(f"[*] Himalayas Playwright Fallback: Navigating to page {page_idx} ({url})...")
                
                try:
                    await page.goto(url, timeout=35000)
                    
                    # Check for Cloudflare challenge and wait
                    for _ in range(10):
                        title = await page.title()
                        if "Just a moment" in title:
                            await asyncio.sleep(1)
                        else:
                            break
                            
                    await asyncio.sleep(3)
                    
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    articles = soup.find_all("article")
                    if not articles:
                        print(f"[-] Himalayas: No job articles found on page {page_idx}. Stopping.")
                        break
                        
                    added_on_page = 0
                    for article in articles:
                        title_elem = article.find("a", class_=lambda c: c and 'text-xl' in c and 'font-medium' in c)
                        if not title_elem:
                            for link in article.find_all("a"):
                                href = link.get("href", "")
                                if "/jobs/" in href and not any(x in href for x in ["/countries/", "/roles/", "/types/", "/api/"]):
                                    title_elem = link
                                    break
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        job_href = title_elem.get("href", "")
                        job_url = f"https://himalayas.app{job_href}" if job_href.startswith("/") else job_href
                        
                        if job_role and not is_role_match(title, job_role):
                            continue
                            
                        company_elem = article.find("a", href=lambda h: h and h.startswith("/companies/") and not any(x in h for x in ["/jobs/", "/salaries/", "/benefits/", "/tech-stack/"]))
                        if company_elem:
                            company = company_elem.get_text(strip=True)
                            comp_href = company_elem.get("href", "")
                            company_url = f"https://himalayas.app{comp_href}" if comp_href.startswith("/") else comp_href
                        else:
                            company = "Himalayas Employer"
                            company_url = "N/A"
                            
                        flag_img = article.find("img", attrs={"data-testid": "circle-country-flag"})
                        if flag_img:
                            job_location = flag_img.parent.get_text(strip=True)
                        else:
                            job_location = "Remote"
                            
                        time_elem = article.find("time")
                        date_posted = time_elem.get_text(strip=True) if time_elem else "N/A"
                        
                        tags = []
                        for tag_link in article.find_all("a", href=lambda h: h and "/jobs/" in h and any(x in h for x in ["/countries/", "/roles/", "/types/"])):
                            tags.append(tag_link.get_text(strip=True))
                        details = f"Tags: {', '.join(tags)}" if tags else "N/A"
                        
                        if not any(j["Apply Link"] == job_url for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": company,
                                "Location": job_location,
                                "Date Posted": date_posted,
                                "Apply Link": job_url,
                                "Company Link": company_url,
                                "No. of Applicants": "N/A",
                                "Company / Job Details": details,
                                "Source": "Himalayas"
                            })
                            added_on_page += 1
                            
                    print(f"[+] Himalayas Playwright Fallback: Extracted {added_on_page} matching jobs from page {page_idx}.")
                    await human_delay(1.5, 3.0)
                    
                except Exception as err:
                    print(f"[!] Himalayas Playwright Error on page {page_idx}: {err}")
                    break
                    
        finally:
            await context.close()
            
    return jobs_data

async def scrape_himalayas_jobs(job_role, location="", max_pages=5, headless=False, filter_params=None, **kwargs):
    """
    Main scraper for Himalayas jobs.
    Uses public API primary, falls back to Playwright if needed.
    """
    results = await scrape_himalayas_jobs_api(job_role, location, max_pages=max_pages, filter_params=filter_params, **kwargs)
    if results:
        print(f"[+] Himalayas Scraper completed. Total results: {len(results)}")
        return results
        
    print("[!] Himalayas API returned 0 results or failed. Retrying via Playwright fallback...")
    results = await scrape_himalayas_jobs_playwright(job_role, location, max_pages=max_pages, headless=headless)
    print(f"[+] Himalayas Scraper completed. Total results: {len(results)}")
    return results

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = input("Enter Job Role: ").strip()
        loc = input("Enter Location: ").strip()
        
    results = asyncio.run(scrape_himalayas_jobs(role, loc))
    print(f"\n[+] Himalayas Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "himalayas_jobs.csv")
