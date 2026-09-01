import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match

DEFAULT_YC_URL = "https://www.workatastartup.com/companies?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-compact&locations=GB&query=DevOps&sortBy=keyword&tab=any&usVisaNotRequired=any"

def build_workatastartup_url(job_role="", location="", industry="", company_size="", min_experience="", custom_url=""):
    """
    Builds a structured Work at a Startup search URL based on user input parameters.
    Uses query=<job_role>&sortBy=keyword for maximum search recall.
    """
    if custom_url and custom_url.strip().startswith("http"):
        return custom_url.strip()
        
    params = [
        ("demographic", "any"),
        ("hasEquity", "any"),
        ("hasSalary", "any"),
        ("industry", industry.strip() if industry and industry.strip() != "All" else "any"),
        ("interviewProcess", "any"),
        ("jobType", "any"),
        ("layout", "list-compact")
    ]
    
    # Location mapping
    loc_lower = location.lower().strip() if location else ""
    if loc_lower:
        if loc_lower in ["uk", "gb", "united kingdom", "great britain", "england"]:
            params.append(("locations", "GB"))
        elif loc_lower in ["india", "in", "ind"]:
            params.append(("locations", "IN"))
        elif loc_lower in ["us", "usa", "united states", "america"]:
            params.append(("locations", "US"))
        elif "remote" in loc_lower:
            params.append(("locations", "Remote"))
        else:
            params.append(("locations", location.strip()))
            
    # Search Query
    if job_role and job_role.strip():
        params.append(("query", job_role.strip()))
        params.append(("sortBy", "keyword"))
    else:
        params.append(("sortBy", "created_desc"))
        
    params.extend([
        ("tab", "any"),
        ("usVisaNotRequired", "any")
    ])
    
    if company_size and company_size.strip() and company_size.strip() != "All":
        params.append(("companySize", company_size.strip()))
        
    if min_experience and min_experience.strip():
        params.append(("minExperience", min_experience.strip()))
        
    query_string = urllib.parse.urlencode(params)
    return f"https://www.workatastartup.com/companies?{query_string}"

def parse_workatastartup_html(html_content, job_role_filter=""):
    """
    Parses HTML content from workatastartup.com.
    Extracts all startups matching search results, including those with specific open job links 
    and those with general applications (like Arva AI, Upsolve AI, etc.).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_keys = set()
    
    # Find all company profile links (/companies/<slug>)
    company_links = soup.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h))
    
    for clink in company_links:
        company_href = clink['href']
        if company_href.endswith('/companies'):
            continue
            
        comp_url = "https://www.workatastartup.com" + company_href if company_href.startswith('/') else company_href
        raw_comp_text = clink.text.strip()
        if not raw_comp_text or len(raw_comp_text) < 2:
            continue
            
        # Find card container
        card = clink.parent
        for _ in range(8):
            if not card:
                break
            if len(card.find_all(['a', 'button', 'div', 'span'])) > 4:
                break
            card = card.parent
            
        if not card:
            continue
            
        # YC Batch cohort, e.g. (S24), (W24), (W22)
        comp_batch = "N/A"
        batch_match = re.search(r'\(([A-Z0-9]+)\)', raw_comp_text)
        if batch_match:
            comp_batch = batch_match.group(1)
            
        # Company Name and Tagline
        comp_name = "YC Startup"
        comp_tagline = ""
        parts = re.split(r'[\u2022\u2013\u2014|\t\n]', raw_comp_text)
        if parts:
            comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
            if len(parts) > 1:
                comp_tagline = parts[1].strip()
                
        card_text = card.text.strip()
        
        # Location extraction from card text
        loc_str = "Remote / Various"
        loc_match = re.search(r'📍\s*([^📍\n•\t]+)', card_text)
        if loc_match:
            loc_str = loc_match.group(1).strip()
        else:
            loc_tokens = []
            for token in re.split(r'[\n\t•|]', card_text):
                t_clean = token.strip()
                if any(k in t_clean for k in ['London', 'United Kingdom', 'UK', 'San Francisco', 'Mountain View', 'Los Angeles', 'New York', 'India', 'IN', 'Remote', 'CA', 'NY', 'US', 'GB']):
                    if t_clean not in loc_tokens and len(t_clean) < 60:
                        loc_tokens.append(t_clean)
            if loc_tokens:
                loc_str = " / ".join(loc_tokens[:2])
                
        # Check for specific open job role links (/jobs/<numeric_id>)
        job_links = card.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
        
        if job_links:
            for jl in job_links:
                job_title = jl.text.strip()
                j_href = jl['href']
                apply_link = "https://www.workatastartup.com" + j_href if j_href.startswith('/') else j_href
                
                key = (comp_name, job_title, apply_link)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                
                # Job specific row details
                j_row = jl.parent
                for _ in range(4):
                    if j_row and j_row.name in ['div', 'li', 'tr']:
                        if len(j_row.find_all(['span', 'div', 'a'])) > 2:
                            break
                    if j_row:
                        j_row = j_row.parent
                r_text = j_row.text if j_row else card_text
                
                salary_str = "N/A"
                sal_match = re.search(r'\$\d+K?\s*-\s*\$\d+K?|\$\d+,\d+\s*-\s*\$\d+,\d+|[£€]\d+K?\s*-\s*[£€]\d+K?|₹\d+[MK]?\s*-\s*₹\d+[MK]?', r_text, re.IGNORECASE)
                if sal_match:
                    salary_str = sal_match.group(0)
                    
                job_type = "Fulltime"
                if "Fulltime" in r_text or "Full-time" in r_text:
                    job_type = "Fulltime"
                elif "Intern" in r_text or "Internship" in r_text:
                    job_type = "Internship"
                elif "Contract" in r_text:
                    job_type = "Contract"
                    
                details_clean = " ".join(card_text.split())[:350]
                
                results.append({
                    "Job Role": job_title,
                    "Company Name": comp_name,
                    "YC Batch": comp_batch,
                    "Location": loc_str,
                    "Job Type": job_type,
                    "Salary / Equity": salary_str,
                    "Apply Link": apply_link,
                    "Company Link": comp_url,
                    "Company / Job Details": f"{comp_tagline} - {details_clean}" if comp_tagline else details_clean,
                    "Source": "Work at a Startup"
                })
        else:
            # Company has no specific open job links (e.g. Arva AI, Upsolve AI)
            # Add general application entry so 100% of matching startups are saved!
            key = (comp_name, job_role_filter, comp_url)
            if key not in seen_keys:
                seen_keys.add(key)
                
                role_label = f"{job_role_filter} (General Application)" if job_role_filter else "General Application"
                details_clean = " ".join(card_text.split())[:350]
                
                # Check for direct Apply button link inside card if available
                apply_btn = card.find('a', href=lambda h: h and ('apply' in h or '/companies/' in h))
                apply_link = comp_url
                if apply_btn and apply_btn.get('href'):
                    b_href = apply_btn['href']
                    apply_link = "https://www.workatastartup.com" + b_href if b_href.startswith('/') else b_href
                    
                results.append({
                    "Job Role": role_label,
                    "Company Name": comp_name,
                    "YC Batch": comp_batch,
                    "Location": loc_str,
                    "Job Type": "General Apply",
                    "Salary / Equity": "N/A",
                    "Apply Link": apply_link,
                    "Company Link": comp_url,
                    "Company / Job Details": f"{comp_tagline} - {details_clean}" if comp_tagline else details_clean,
                    "Source": "Work at a Startup"
                })
                
    return results

async def scrape_workatastartup_jobs(target_url=None, job_role="", location="", industry="", company_size="", min_experience="", max_scrolls=20, headless=False):
    """
    Scrapes Y Combinator's Work at a Startup job listings.
    Supports direct URLs or custom parameters (job_role, location).
    Saves session cookies in ./workatastartup_session for authenticated access.
    """
    url = build_workatastartup_url(
        job_role=job_role,
        location=location,
        industry=industry,
        company_size=company_size,
        min_experience=min_experience,
        custom_url=target_url
    )
        
    print(f"[*] Work at a Startup (YC): Navigating to target URL...\n    {url}")
    
    session_dir = os.path.abspath("./workatastartup_session")
    os.makedirs(session_dir, exist_ok=True)
    
    jobs_data = []
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                session_dir,
                headless=headless,
                channel="chrome",
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                session_dir,
                headless=headless,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(4)
            
            # ALWAYS pause up to 3 minutes when running in non-headless interactive mode
            if not headless:
                print("\n" + "=" * 65)
                print(" [!] BROWSER WINDOW IS OPEN - 3-MINUTE LOGIN & SEARCH WINDOW")
                print("=" * 65)
                print(" 1. Please LOG IN to Work at a Startup in the opened browser window if not already logged in.")
                print(" 2. Your login session is saved in ./workatastartup_session for all future runs.")
                print(" 3. Once logged in and viewing search results, press ENTER below to start extracting all matching jobs.")
                print("=" * 65)
                print("[*] Waiting up to 3 minutes for login...")
                
                try:
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, input, " -> Press ENTER once you are logged in and viewing results: "),
                        timeout=180
                    )
                    print("[*] User pressed ENTER. Starting extraction now...")
                except asyncio.TimeoutError:
                    print("\n[*] 3-minute login window finished. Starting extraction now...")
                except Exception:
                    pass
                    
            # Progressively scroll to trigger lazy loading ("Loading matches...") for all 36+ startups
            print("[*] Work at a Startup (YC): Progressively scrolling page to load ALL matching startups...")
            previous_height = 0
            for scroll in range(max_scrolls):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                # Scroll back slightly to trigger IntersectionObserver lazy load
                await page.evaluate("window.scrollBy(0, -600)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                current_height = await page.evaluate("document.body.scrollHeight")
                if current_height == previous_height:
                    print(f"[*] Fully loaded all matching startups at scroll step {scroll + 1}.")
                    break
                previous_height = current_height
                
            html = await page.content()
            filter_term = job_role if job_role and not target_url else ""
            jobs_data = parse_workatastartup_html(html, filter_term)
            print(f"[+] Work at a Startup (YC): Extracted {len(jobs_data)} job postings successfully.")
            
        except Exception as err:
            print(f"[!] Work at a Startup extraction note/error: {err}")
            
        await context.close()
        
    return jobs_data

def main():
    print("=" * 60)
    print("     Y Combinator: Work at a Startup Scraper")
    print("=" * 60)
    
    target_url = ""
    role = ""
    loc = ""
    
    if len(sys.argv) > 1:
        arg1 = sys.argv[1].strip()
        if arg1.startswith("http"):
            target_url = arg1
        else:
            role = arg1
            if len(sys.argv) > 2:
                loc = sys.argv[2].strip()
    else:
        role = input("Enter Job Role (e.g., Data Analyst, DevOps): ").strip()
        loc = input("Enter Location (e.g., UK / IN / US / Remote): ").strip()
        
    results = asyncio.run(
        scrape_workatastartup_jobs(
            target_url=target_url,
            job_role=role,
            location=loc,
            headless=False
        )
    )
    
    print(f"\n[+] Work at a Startup Scraper completed. Total listings extracted: {len(results)}")
    if results:
        save_to_csv(results, "workatastartup_jobs.csv")

if __name__ == "__main__":
    main()
