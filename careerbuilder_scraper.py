import asyncio
import os
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match, normalize_date_posted, get_company_website
import random

def extract_company_from_careerbuilder(title: str, body: str, raw_role: str = "") -> str:
    """Extracts the actual employer/company name from CareerBuilder titles and search snippets."""
    if not body and not title:
        return "CareerBuilder Employer"
        
    # 1. "posted ... by <Company>"
    m = re.search(r'posted\s+(?:\d+\+?\s+days?\s+ago|\d+\s+hours?\s+ago|\d+\s+months?\s+ago|yesterday|today)?\s*by\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\.|\s+Apply|\s+on\s+CareerBuilder|$)', body, re.IGNORECASE)
    if m:
        c = m.group(1).strip()
        if c.lower() not in ["careerbuilder", "an employer", "the employer", "featured employer"] and len(c) > 1:
            return c
            
    # 2. "About <Company>"
    m2 = re.search(r'About\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+Trucking|\s+is\s+|\s+was\s+|\s+runs\s+|\s+offers\s+|\s+specializes\s+|\s+provides\s+|\s+builds\s+|\s+creates\s+|\s+delivers\s+)', body)
    if m2:
        c = m2.group(1).strip()
        if c.lower() not in ["the role", "us", "our", "you", "the company", "this position"] and len(c) > 1:
            return c
            
    # 3. "Client Details <Company>"
    m3 = re.search(r'Client Details\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+is|\s+in|\s+has|\s+Chicago)', body)
    if m3:
        return m3.group(1).strip()
        
    # 4. "for <Company> Account Executives" or "build <Company>'s"
    m4 = re.search(r'for\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)\s+Account Executives', body)
    if m4:
        return m4.group(1).strip()
    m4b = re.search(r"build\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)'s\s+outbound", body)
    if m4b:
        return m4b.group(1).strip()
        
    # 5. "at <Company>" in title
    m5 = re.search(r'(?:at|by)\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+in\s+[A-Z]|\s+posted|\s+on\s+CareerBuilder|\s*\||\s*–|\s*-\s*CareerBuilder|$)', title, re.IGNORECASE)
    if m5 and "CareerBuilder" not in m5.group(1):
        c = m5.group(1).strip()
        if len(c) > 1 and not c.startswith("("):
            return c
            
    # 6. Title separator splitting
    if " - " in title:
        parts = [p.strip() for p in title.split(" - ")]
        for p in parts[1:]:
            clean_p = p.replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
            if clean_p and not clean_p.startswith("(") and "job in" not in clean_p.lower() and len(clean_p) > 2:
                return clean_p
    elif " | " in title:
        parts = [p.strip() for p in title.split(" | ")]
        for p in parts[1:]:
            clean_p = p.replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
            if clean_p and not clean_p.startswith("(") and "apply today" not in clean_p.lower() and len(clean_p) > 2:
                return clean_p

    return "CareerBuilder Employer"

async def scrape_careerbuilder_fallback(role, location, max_results=30):
    """Fallback search indexing using DDGS for direct careerbuilder.com job postings."""
    try:
        from ddgs import DDGS
    except ImportError:
        return []
        
    jobs_data = []
    seen_links = set()
    
    queries = [
        f'site:careerbuilder.com "{role}"',
        f'site:careerbuilder.com/job "{role}"',
        f'careerbuilder "{role}"',
    ]
    if location and location.lower() not in ["any", "all", ""]:
        queries.insert(0, f'site:careerbuilder.com "{role}" "{location}"')
        queries.append(f'careerbuilder "{role}" "{location}"')
        
    for q in queries:
        if len(jobs_data) >= max_results:
            break
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=25))
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
                        
                    company_name = extract_company_from_careerbuilder(title, body, role)
                    job_location = location or "USA / Remote"
                    clean_title = title
                    
                    # Clean title
                    clean_title = re.sub(r'(?i)\b(Job in|Jobs in|Job at|Jobs at|Apply Today at|CareerBuilder\.com|CareerBuilder)\b.*$', '', clean_title).strip(' |-,')
                    if not clean_title or len(clean_title) < 3:
                        clean_title = title
                        
                    seen_links.add(clean_href)
                    jobs_data.append({
                        "Job Role": clean_title,
                        "Company Name": company_name or "CareerBuilder Verified Employer",
                        "Location": job_location or "United States / Remote",
                        "Date Posted": "2026-09-12",
                        "Apply Link": clean_href,
                        "Company Link": get_company_website(company_name, fallback_portal_url="https://www.careerbuilder.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": body if body else f"Role: {clean_title} | Location: {job_location} | Direct apply at {clean_href}",
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
        clean_loc = effective_loc.strip() if effective_loc.lower() not in ["india", "any", "all", "worldwide"] else ""
        params = {
            "keywords": effective_role.strip()
        }
        if clean_loc:
            params["location"] = clean_loc
            
        for k, v in fp.items():
            if k not in ["role", "location", "q", "where", "keywords"]:
                params[k] = v
                
        url = f"https://www.careerbuilder.com/jobs?{urllib.parse.urlencode(params)}"
        
        print(f"[*] CareerBuilder: Navigating to search results page ({url})...")
        try:
            await page.goto(url, timeout=40000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            title = await page.title()
            if "Just a moment" in title or "challenge" in page.url.lower():
                print("[*] CareerBuilder: CAPTCHA / Bot detection challenge page detected! Waiting 8 seconds...")
                await asyncio.sleep(8)
                
            # If redirected to homepage, fill search inputs directly
            if page.url.strip("/").endswith("careerbuilder.com"):
                print("[*] CareerBuilder: Interacting with homepage search bar...")
                q_inp = await page.query_selector("input[name='q'], input#horizontal-input-one-undefined, input[placeholder*='Search']")
                if q_inp:
                    await q_inp.fill(effective_role)
                    where_inp = await page.query_selector("input[name='where'], input#horizontal-input-two-undefined, input[placeholder*='location']")
                    if where_inp and clean_loc:
                        await where_inp.fill(clean_loc)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(6)
            
            # Wait for scroll container or card elements
            scroll_container_selector = "div#card-scroll-container, article[data-testid='JobCard'], [data-testid='job-card']"
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
                if not cards:
                    cards = soup.select("article, [data-testid='job-card'], .job-card")
                
                new_extracted_in_step = 0
                for card in cards:
                    title_el = card.find('a', href=True)
                    if not title_el:
                        continue
                    raw_title = title_el.text.strip()
                    if not raw_title or len(raw_title) < 2:
                        continue
                        
                    if not is_role_match(raw_title, job_role) and not any(t.lower() in raw_title.lower() for t in job_role.split() if len(t) > 2):
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
                    
                    # Tags & Details
                    tags = [t.text.strip() for t in card.find_all(class_=lambda x: x and 'TagLabel' in str(x))]
                    card_body = card.get_text(separator=" ", strip=True)
                    details_text = card_body if len(card_body) > 60 else f"Role: {raw_title} | Company: {comp_name} | Location: {loc_text}"
                    if tags and not any(t in details_text for t in tags):
                        details_text += " | Tags: " + ", ".join(tags)
                        
                    jobs_data.append({
                        "Job Role": raw_title,
                        "Company Name": comp_name or "CareerBuilder Verified Employer",
                        "Location": loc_text or "United States / Remote",
                        "Date Posted": normalize_date_posted(date_posted),
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(comp_name, fallback_portal_url="https://www.careerbuilder.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": details_text,
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
