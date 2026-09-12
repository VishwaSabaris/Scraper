import asyncio
import os
import sys
import urllib.parse
import json
import urllib.request
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay

def get_target_domain(location):
    """
    Determines the appropriate ZipRecruiter domain based on location.
    ZipRecruiter uses ziprecruiter.com for US, UK, Canada, and global searches,
    and ziprecruiter.in for India.
    """
    if not location:
        return "ziprecruiter.com"

    loc_lower = location.lower().strip()
    india_keywords = ["india", "bengaluru", "bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata", "gurgaon", "noida"]
    if any(k in loc_lower for k in india_keywords) or loc_lower == "in":
        return "ziprecruiter.in"
        
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
    for k in ["days", "refine_by_salary", "radius"]:
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
                    url = f"https://www.{domain}/jobs-search/{page_idx}?search={formatted_role}"
                    if formatted_location:
                        url += f"&location={formatted_location}"
                        
                print(f"[*] ZipRecruiter: Navigating to page {page_idx} ({url})...")
                
                await page.goto(url, timeout=50000)
                await asyncio.sleep(5)
                
                # Scroll slightly to ensure dynamic elements load
                await page.evaluate("window.scrollBy(0, 400);")
                await asyncio.sleep(2)
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Card identification priority:
                # 1. <article> elements (modern ZipRecruiter search cards)
                # 2. .job_result_two_pane_v2 divs
                # 3. .job-listing li elements
                # 4. .job_result divs
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
                            
                        if not is_role_match(title, job_role):
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
                        
                        # 5. Apply Link (Job Key extraction or href)
                        art_id = card.get('id', '')
                        job_key = art_id.replace('job-card-', '') if 'job-card-' in art_id else art_id
                        
                        apply_link = "N/A"
                        a_tags = card.find_all("a", href=True)
                        for a in a_tags:
                            href = a.get("href", "")
                            if "lk=" in href or "/job/" in href:
                                apply_link = f"https://www.{domain}{href}" if href.startswith("/") else href
                                break
                                
                        if apply_link == "N/A" and job_key:
                            apply_link = f"https://www.{domain}/jobs-search?search={formatted_role}&location={formatted_location}&lk={job_key}"
                        elif apply_link == "N/A" and a_tags:
                            href = a_tags[0].get("href", "")
                            apply_link = f"https://www.{domain}{href}" if href.startswith("/") else href
                            
                        if apply_link == "N/A":
                            continue
                            
                        # 6. Date Posted
                        date_posted = "N/A"
                        card_text = card.text.strip().lower()
                        for p_el in card.find_all(['p', 'span', 'time']):
                            p_text = p_el.text.strip().lower()
                            if 'posted' in p_text or 'ago' in p_text or 'today' in p_text or 'yesterday' in p_text:
                                date_posted = p_el.text.strip()
                                break
                                
                        details_parts = []
                        if company != "ZipRecruiter Employer":
                            details_parts.append(f"Company: {company}")
                        if job_location:
                            details_parts.append(f"Location: {job_location}")
                        if salary_str != "N/A":
                            details_parts.append(f"Salary: {salary_str}")
                        details = " | ".join(details_parts) if details_parts else "N/A"
                        
                    elif structure_type == "two_pane":
                        h2_el = card.find('h2')
                        if not h2_el:
                            continue
                        title = h2_el.text.strip()
                        
                        if not is_role_match(title, job_role):
                            continue
                            
                        company_el = card.find(attrs={"data-testid": "job-card-company"})
                        company = company_el.text.strip() if company_el else "ZipRecruiter Employer"
                        company_url = "N/A"
                        
                        location_el = card.find(attrs={"data-testid": "job-card-location"})
                        job_location = location_el.text.strip() if location_el else (location or "Remote / Various")
                        
                        salary_str = "N/A"
                        for p_el in card.find_all(['p', 'span']):
                            p_text = p_el.text.strip()
                            if '$' in p_text and ('/yr' in p_text or '/hr' in p_text or 'Est.' in p_text):
                                salary_str = p_text
                                break
                                
                        article_el = card.find('article')
                        card_id = article_el.get('id', '') if article_el else card.get('id', '')
                        job_key = card_id.replace('job-card-', '') if 'job-card-' in card_id else card_id
                        
                        if job_key:
                            apply_link = f"https://www.{domain}/jobs-search?search={formatted_role}&location={formatted_location}&lk={job_key}"
                        else:
                            link_el = card.find('a', href=True)
                            href = link_el['href'] if link_el else ""
                            apply_link = f"https://www.{domain}" + href if href.startswith('/') else href
                            
                        date_posted = "N/A"
                        for p_el in card.find_all(['p', 'span']):
                            p_text = p_el.text.strip().lower()
                            if 'posted' in p_text or 'ago' in p_text or 'today' in p_text:
                                date_posted = p_el.text.strip()
                                break
                                
                        details = f"Company: {company} | Location: {job_location} | Salary: {salary_str}"
                        
                    elif structure_type == "job-listing":
                        title_el = card.find('a', class_='jobList-title') or card.find('a', class_='job-link')
                        if not title_el:
                            continue
                            
                        title = title_el.text.strip()
                        if not is_role_match(title, job_role):
                            continue
                            
                        href = title_el.get('href', '')
                        if not href:
                            continue
                            
                        apply_link = f"https://www.{domain}" + href if href.startswith('/') else href
                        
                        comp_li = card.find(lambda tag: tag.name == 'li' and tag.find('i', class_=lambda c: c and 'fa-building' in c))
                        company = comp_li.text.strip() if comp_li else "ZipRecruiter Employer"
                        company_url = "N/A"
                        
                        loc_li = card.find(lambda tag: tag.name == 'li' and tag.find('i', class_=lambda c: c and 'fa-map-marker-alt' in c))
                        job_location = loc_li.text.strip() if loc_li else (location or "Remote / Various")
                        
                        date_el = card.find(class_=lambda x: x and 'jobList-date' in x)
                        date_posted = date_el.text.strip() if date_el else "N/A"
                        
                        desc_el = card.find(class_=lambda x: x and 'jobList-description' in x)
                        details = desc_el.text.strip() if desc_el else "N/A"
                        
                    else:
                        h2_el = card.find('h2')
                        if not h2_el:
                            continue
                            
                        title = h2_el.text.strip()
                        if not is_role_match(title, job_role):
                            continue
                            
                        link_el = h2_el.find_parent('a') or card.find('a', href=True)
                        if not link_el:
                            continue
                            
                        href = link_el['href']
                        apply_link = f"https://www.{domain}" + href if href.startswith('/') else href
                        
                        company_el = card.find(attrs={"data-testid": "job-card-company"})
                        company = company_el.text.strip() if company_el else "ZipRecruiter Employer"
                        company_url = "N/A"
                        
                        location_el = card.find(attrs={"data-testid": "job-card-location"})
                        job_location = location_el.text.strip() if location_el else (location or "Remote / Various")
                        
                        date_posted = "N/A"
                        desc_el = card.find('p', class_=lambda x: x and 'text-secondary' in x and 'line-clamp-3' in x)
                        details = desc_el.text.strip() if desc_el else "N/A"
                        
                    # Check for duplicates and add
                    if not any(j["Apply Link"] == apply_link for j in jobs_data):
                        jobs_data.append({
                            "Job Role": title,
                            "Company Name": company,
                            "Location": job_location,
                            "Date Posted": date_posted,
                            "Apply Link": apply_link,
                            "Company Link": company_url,
                            "No. of Applicants": "N/A",
                            "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                            "Source": f"ZipRecruiter ({domain})"
                        })
                        added_count += 1
                        
                print(f"[+] ZipRecruiter: Extracted {added_count} matching job listings from page {page_idx}.")
                
                await human_delay(2, 4)
                
        finally:
            await context.close()
            
    return jobs_data

if __name__ == "__main__":
    max_p = 1
    if len(sys.argv) >= 4:
        role = sys.argv[1]
        loc = sys.argv[2]
        max_p = int(sys.argv[3])
    elif len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = input("Enter Job Role (e.g., DevOps): ").strip()
        loc = input("Enter Location (e.g., Bengaluru, Karnataka, India): ").strip()
        pages_input = input("Enter Max Pages to Scrape [default 1]: ").strip()
        max_p = int(pages_input) if pages_input.isdigit() else 1
        
    results = asyncio.run(scrape_ziprecruiter_jobs(role, loc, max_pages=max_p))
    print(f"\n[+] ZipRecruiter Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "ziprecruiter_jobs.csv")
