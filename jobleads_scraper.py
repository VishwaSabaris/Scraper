import asyncio
import os
import sys
import urllib.parse
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, save_to_csv, is_role_match, human_delay, normalize_date_posted, get_company_website

def get_jobleads_country_code(location):
    """
    Maps user-provided locations to JobLeads localization country codes (ISO 2-letter codes).
    Note: UK uses 'gb' on JobLeads.
    """
    if not location:
        return "us"
    loc_lower = location.lower().strip()
    
    # United Kingdom
    if any(x in loc_lower for x in ["united kingdom", "uk", "great britain", "england", "scotland", "wales", "london", "manchester", "birmingham", "gb"]):
        return "gb"
    
    # India - comprehensive cities and states
    indian_locs = [
        "india", "chennai", "mumbai", "bangalore", "bengaluru", "delhi", "new delhi", "ncr", "noida", 
        "gurgaon", "gurugram", "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "surat", 
        "lucknow", "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "vadodara", 
        "coimbatore", "kochi", "cochin", "chandigarh", "mysore", "mysuru", "trivandrum", 
        "thiruvananthapuram", "cuddalore", "kannur", "kozhikode", "madurai", "tiruchirappalli", 
        "salem", "tiruppur", "tamil nadu", "karnataka", "maharashtra", "telangana", "kerala", 
        "gujarat", "rajasthan", "punjab", "haryana", "uttar pradesh", "west bengal", "andhra pradesh"
    ]
    if any(x in loc_lower for x in indian_locs) or re.search(r'\b(in|india)\b', loc_lower):
        return "in"
        
    # Canada
    if any(x in loc_lower for x in ["canada", "ca", "toronto", "vancouver", "montreal", "ottawa", "calgary"]):
        return "ca"
        
    # Australia
    if any(x in loc_lower for x in ["australia", "au", "sydney", "melbourne", "brisbane", "perth", "adelaide"]):
        return "au"
        
    # New Zealand
    if any(x in loc_lower for x in ["new zealand", "nz", "auckland", "wellington", "christchurch"]):
        return "nz"
        
    # UAE
    if any(x in loc_lower for x in ["united arab emirates", "uae", "dubai", "abu dhabi", "sharjah"]):
        return "ae"
        
    # Germany
    if any(x in loc_lower for x in ["germany", "de", "munich", "berlin", "frankfurt", "hamburg", "cologne"]):
        return "de"
        
    # France
    if any(x in loc_lower for x in ["france", "fr", "paris", "lyon", "marseille"]):
        return "fr"
        
    # Ireland
    if any(x in loc_lower for x in ["ireland", "ie", "dublin", "cork"]):
        return "ie"
        
    return "us"

async def scrape_jobleads_jobs(job_role, location="", max_pages=1, headless=False, filter_params=None, **kwargs):
    """
    Scrapes job listings from jobleads.com using Playwright chromium persistent context.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = dict(filter_params or {})
    for k, v in kwargs.items():
        if v is not None and k not in fp:
            fp[k] = v

    effective_role = fp.get("q") or job_role
    effective_loc = fp.get("location") or location or ""
    
    country_code = get_jobleads_country_code(effective_loc)
    encoded_role = urllib.parse.quote(effective_role.strip())
    
    if effective_loc and effective_loc.strip():
        loc_clean = effective_loc.strip()
        # Format location with country for JobLeads URL structure (e.g. 'Chennai, India' for /in/jobs/l/)
        if country_code == "in" and not any(k in loc_clean.lower() for k in ["india", "in"]):
            loc_formatted = f"{loc_clean}, India"
        elif country_code == "gb" and not any(k in loc_clean.lower() for k in ["uk", "united kingdom", "gb"]):
            loc_formatted = f"{loc_clean}, United Kingdom"
        elif country_code == "us" and not any(k in loc_clean.lower() for k in ["usa", "united states", "us"]):
            loc_formatted = f"{loc_clean}, United States"
        else:
            loc_formatted = loc_clean

        encoded_loc = urllib.parse.quote(loc_formatted)
        base_url = f"https://www.jobleads.com/{country_code}/jobs/l/{encoded_loc}/q/{encoded_role}"
    else:
        base_url = f"https://www.jobleads.com/{country_code}/jobs/q/{encoded_role}"

    extra_q = {}
    
    # Map work_mode to filter_by_remote if not already set
    work_mode = fp.get("work_mode") or kwargs.get("work_mode")
    if "filter_by_remote" not in fp and work_mode:
        wm = str(work_mode).lower().strip()
        if "remote" in wm or "wfh" in wm:
            extra_q["filter_by_remote"] = "remote"
        elif "hybrid" in wm:
            extra_q["filter_by_remote"] = "hybrid"
        elif any(k in wm for k in ["office", "wfo", "onsite", "in_person", "in-person"]):
            extra_q["filter_by_remote"] = "in_person"

    for k, v in fp.items():
        if k not in ["role", "location", "q", "work_mode"]:
            extra_q[k] = v

    # Optional City Coordinates for precision
    city_coords = {
        "chennai": {"location_latitude": "13.0836939", "location_longitude": "80.270186", "location_coordinates_radius": "23723.45776770741"},
        "bangalore": {"location_latitude": "12.9715987", "location_longitude": "77.5945627", "location_coordinates_radius": "25000"},
        "bengaluru": {"location_latitude": "12.9715987", "location_longitude": "77.5945627", "location_coordinates_radius": "25000"},
        "mumbai": {"location_latitude": "19.0760", "location_longitude": "72.8777", "location_coordinates_radius": "25000"},
        "delhi": {"location_latitude": "28.6139", "location_longitude": "77.2090", "location_coordinates_radius": "25000"},
        "hyderabad": {"location_latitude": "17.3850", "location_longitude": "78.4867", "location_coordinates_radius": "25000"},
        "pune": {"location_latitude": "18.5204", "location_longitude": "73.8567", "location_coordinates_radius": "25000"},
        "kolkata": {"location_latitude": "22.5726", "location_longitude": "88.3639", "location_coordinates_radius": "25000"},
    }
    if effective_loc:
        for cname, coords in city_coords.items():
            if cname in effective_loc.lower():
                for ck, cv in coords.items():
                    if ck not in extra_q:
                        extra_q[ck] = cv
                break

    if extra_q:
        url = f"{base_url}?{urllib.parse.urlencode(extra_q)}"
    else:
        url = base_url

    print(f"[*] JobLeads: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}' (Country: {country_code.upper()})...")
    print(f"[*] JobLeads URL: {url}")
    
    user_dir = os.path.abspath("./jobleads_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
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
            print(f"[*] JobLeads: Navigating to search page...")
            await page.goto(url, timeout=50000)
            await asyncio.sleep(6)
            
            # Scroll loop to load all available jobs dynamically (Infinite Scroll)
            print("[*] JobLeads: Scrolling to load more listings...", flush=True)
            prev_card_count = 0
            max_scrolls = max(2, min(max_pages * 3, 15))
            scroll_count = 0
            
            while scroll_count < max_scrolls:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
                
                current_html = await page.content()
                current_soup = BeautifulSoup(current_html, 'html.parser')
                cards = current_soup.find_all(class_='animated-list-item')
                if len(cards) == 0:
                    cards = current_soup.find_all(attrs={"data-testid": "search-job-card"})
                    
                curr_card_count = len(cards)
                print(f"  - Scroll {scroll_count + 1}: Found {curr_card_count} job cards.", flush=True)
                
                if curr_card_count <= prev_card_count:
                    break
                    
                prev_card_count = curr_card_count
                scroll_count += 1
                
            # Parse final HTML results
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            cards = soup.find_all(class_='animated-list-item')
            if len(cards) == 0:
                cards = soup.find_all(attrs={"data-testid": "search-job-card"})
                
            print(f"[+] JobLeads: Found {len(cards)} job card elements on the search page.")
            
            added_count = 0
            for card in cards:
                # Extract title and apply link
                link_el = card.find(attrs={"data-testid": "search-job-card-link"})
                if not link_el:
                    link_el = card.find("a", href=True)
                    
                if not link_el:
                    continue
                    
                title = link_el.text.strip()
                if not title or title == "N/A":
                    h2_el = card.find("h2")
                    title = h2_el.text.strip() if h2_el else "N/A"
                    
                if not title or title == "N/A":
                    continue
                    
                # Verify role matches
                if not is_role_match(title, job_role):
                    continue
                    
                apply_link = link_el.get("href", "")
                if apply_link.startswith("/"):
                    apply_link = "https://www.jobleads.com" + apply_link
                    
                # Extract company and location
                comp_loc_el = card.find(attrs={"data-testid": "search-job-card-company"})
                company = "JobLeads Employer"
                job_location = location or "Various"
                
                if comp_loc_el:
                    comp_loc_text = comp_loc_el.text.strip()
                    parts = [p.strip() for p in re.split(r' \ufffd | \u2022 | \u00b7 | - | \| |\u2013', comp_loc_text)]
                    parts = [p for p in parts if p]
                    
                    if len(parts) > 0:
                        company = parts[0]
                    if len(parts) > 1:
                        job_location = parts[1]
                        
                # Extract Date Posted
                date_el = card.find(attrs={"data-testid": "job-card-date"})
                date_posted = date_el.text.strip() if date_el else "N/A"
                
                # Extract Details (combine work setting and salary chips)
                work_setting_el = card.find(attrs={"data-testid": "job-card-chip-work-setting"})
                salary_el = card.find(attrs={"data-testid": "job-card-chip-salary"})
                
                details_parts = []
                if work_setting_el:
                    details_parts.append(f"Work Setting: {work_setting_el.text.strip()}")
                if salary_el:
                    details_parts.append(f"Salary: {salary_el.text.strip()}")
                    
                comp_clean = company if (company and company != "JobLeads Employer" and company != "N/A") else "JobLeads Verified Employer"
                loc_clean = job_location if (job_location and job_location != "Various" and job_location != "N/A") else (location or "United States / Remote")
                details = " | ".join(details_parts) if details_parts else f"Company: {comp_clean} | Location: {loc_clean} | Role: {title} | Source: JobLeads"
                
                # Deduplicate and add
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": comp_clean,
                        "Location": loc_clean,
                        "Date Posted": normalize_date_posted(date_posted),
                        "Apply Link": apply_link,
                        "Company Link": get_company_website(comp_clean, fallback_portal_url="https://www.jobleads.com"),
                        "No. of Applicants": "Actively Hiring",
                        "Company / Job Details": details,
                        "Source": "JobLeads"
                    })
                    added_count += 1
                    
            print(f"[+] JobLeads: Extracted {added_count} matching job listings.")
            
        except Exception as run_err:
            print(f"[!] JobLeads: Scraper execution failed: {run_err}")
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
        
    results = asyncio.run(scrape_jobleads_jobs(role, loc, max_pages=1))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "jobleads_jobs.csv")
