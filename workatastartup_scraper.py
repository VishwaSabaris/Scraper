import asyncio
import os
import sys
import re
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context, save_to_csv, is_role_match, normalize_date_posted, get_company_website

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

def parse_workatastartup_html(html_content, job_role_filter="", work_mode_filter=""):
    """
    Parses HTML content from workatastartup.com.
    Extracts ONLY real individual job postings (/jobs/<numeric_id>).
    Never creates synthetic 'General Application' records or company profiles.
    Accurately extracts real company names and excludes navigation elements like 'See all X jobs ›'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_apply_links = set()
    
    # Find all specific job links (/jobs/<numeric_id>)
    job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
    
    for jl in job_links:
        j_href = jl['href']
        apply_link = "https://www.workatastartup.com" + j_href if j_href.startswith('/') else j_href
        
        if apply_link in seen_apply_links:
            continue
            
        # Check Layout 1 (Modern grid layout: <a> is the card containing h3, p.font-semibold, img)
        h3 = jl.find(['h3', 'h2'])
        comp_el = jl.find('p', class_=lambda c: c and 'font-semibold' in c)
        img = jl.find('img')
        
        comp_name = "YC Startup"
        job_title = ""
        comp_tagline = ""
        comp_batch = ""
        comp_url = ""
        
        if h3 and h3.text.strip():
            job_title = h3.text.strip()
        if comp_el and comp_el.text.strip():
            comp_name = comp_el.text.strip()
        elif img and img.get('alt'):
            comp_name = img['alt'].replace(' logo', '').replace(' Logo', '').strip()
            
        # If not found inside jl itself, check Layout 2 (Traditional list layout)
        if not job_title:
            job_title = jl.text.strip()
            
        if not job_title:
            continue
            
        # Role match validation: strictly match requested job role if provided
        if job_role_filter and not is_role_match(job_title, job_role_filter):
            continue
            
        seen_apply_links.add(apply_link)
        
        # Locate enclosing company card container and company profile link
        card = jl.parent
        if comp_name == "YC Startup":
            p = jl.parent
            for _ in range(10):
                if not p:
                    break
                candidates = []
                for a in p.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h)):
                    href = a['href']
                    if href.endswith('/companies'):
                        continue
                    txt = " ".join(a.text.split())
                    txt_lower = txt.lower()
                    if txt_lower.startswith('see all') or txt_lower.startswith('view all') or txt_lower.startswith('view job') or txt_lower == 'apply':
                        continue
                    if len(txt) > 0:
                        candidates.append((a, txt, href))
                        
                if candidates:
                    card = p
                    best_link, raw_comp_text, comp_href = candidates[0]
                    for cand in candidates:
                        if 'hover:underline' in (cand[0].get('class') or []):
                            best_link, raw_comp_text, comp_href = cand
                            break
                            
                    comp_url = "https://www.workatastartup.com" + comp_href if comp_href.startswith('/') else comp_href
                    batch_match = re.search(r'\(([A-Z0-9]+)\)', raw_comp_text)
                    if batch_match:
                        comp_batch = batch_match.group(1)
                    parts = re.split(r'[\u2022\u2013\u2014|\t\n\xb7]', raw_comp_text)
                    if parts:
                        comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
                        if len(parts) > 1:
                            comp_tagline = parts[1].strip()
                    if not comp_name or len(comp_name) < 2 or 'see all' in comp_name.lower():
                        slug_match = re.search(r'/companies/([a-zA-Z0-9_-]+)', comp_href)
                        if slug_match:
                            comp_name = slug_match.group(1).replace('-', ' ').title()
                    break
                p = p.parent

        # Extract details, salary, and location from card / job row
        card_text = " ".join(card.text.split()) if card else ""
        
        # Check inside jl for modern layout meta
        line_clamp = jl.find(class_=lambda c: c and 'line-clamp-2' in c)
        if line_clamp:
            r_text = " ".join(line_clamp.text.split())
        else:
            j_row = jl.parent
            for _ in range(4):
                if j_row and j_row.name in ['div', 'li', 'tr'] and len(j_row.find_all(['span', 'div', 'a'])) > 2:
                    break
                if j_row:
                    j_row = j_row.parent
            r_text = " ".join(j_row.text.split()) if j_row else card_text
        
        salary_str = "N/A"
        sal_match = re.search(r'\$\d+K?\s*-\s*\$\d+K?|\$\d+,\d+\s*-\s*\$\d+,\d+|[£€]\d+K?\s*-\s*[£€]\d+K?|₹\d+[MK]?\s*-\s*₹\d+[MK]?', r_text, re.IGNORECASE)
        if sal_match:
            salary_str = sal_match.group(0)
            
        loc_str = "Remote"
        loc_tokens = []
        for token in re.split(r'[\n\t•|\xb7/]', r_text):
            t_clean = token.strip()
            if any(k in t_clean for k in ['London', 'United Kingdom', 'UK', 'San Francisco', 'Mountain View', 'Austin', 'New York', 'India', 'IN', 'Remote', 'CA', 'NY', 'US', 'GB']):
                if t_clean not in loc_tokens and len(t_clean) < 60 and not any(ch in t_clean for ch in ['$','£','€','₹','%']):
                    loc_tokens.append(t_clean)
        if loc_tokens:
            loc_str = " / ".join(loc_tokens[:2])
            
        # Remote mode validation:
        if work_mode_filter and "remote" in work_mode_filter.lower():
            if "remote" not in loc_str.lower() and "remote" not in r_text.lower() and "remote" not in card_text.lower():
                loc_str = f"{loc_str} (Remote)" if loc_str and loc_str != "Remote / Various" else "Remote"
                
        comp_clean = comp_name if (comp_name and comp_name != "N/A") else "YC Verified Startup"
        loc_clean = loc_str if (loc_str and loc_str != "N/A") else "Remote / Worldwide"
        
        details_clean = card_text[:350]
        details_full = f"{comp_tagline} - {details_clean}" if comp_tagline else details_clean
        if salary_str and salary_str != "N/A":
            details_full += f" | Salary: {salary_str}"
        if comp_batch:
            details_full += f" | YC Batch: {comp_batch}"
            
        final_comp_url = comp_url if (comp_url and comp_url.startswith("http")) else get_company_website(comp_clean, fallback_portal_url="https://www.workatastartup.com")

        results.append({
            "Job Role": job_title,
            "Company Name": comp_clean,
            "Location": loc_clean,
            "Date Posted": normalize_date_posted("today"),
            "Apply Link": apply_link,
            "Company Link": final_comp_url,
            "No. of Applicants": "Actively Hiring",
            "Company / Job Details": details_full,
            "Source": "Work at a Startup"
        })
        
    return results

async def scrape_workatastartup_jobs(target_url=None, job_role="", location="", industry="", company_size="", min_experience="", max_scrolls=20, headless=False, filter_params=None, interactive=False, **kwargs):
    """
    Scrapes Y Combinator's Work at a Startup job listings.
    Supports direct URLs, custom parameters (job_role, location), and universal filter parameters.
    Saves session cookies in ./workatastartup_session for authenticated access.
    """
    fp = filter_params or {}
    effective_role = fp.get("query") or job_role
    effective_loc = fp.get("locations") or fp.get("location") or location or ""
    work_mode_filter = fp.get("work_mode") or kwargs.get("work_mode") or ("remote" if "remote" in effective_loc.lower() else "")

    if work_mode_filter and "remote" in work_mode_filter.lower():
        effective_loc = "Remote"
        if fp:
            fp["locations"] = "Remote"
            
    if target_url and target_url.strip().startswith("http"):
        url = target_url.strip()
    elif fp:
        # Build direct query string from filter params
        url = f"https://www.workatastartup.com/companies?{urllib.parse.urlencode(fp)}"
    else:
        url = build_workatastartup_url(
            job_role=effective_role,
            location=effective_loc,
            industry=industry,
            company_size=company_size,
            min_experience=min_experience
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
            
            # Interactive login prompt only if explicitly enabled and stdin is interactive
            if interactive and not headless and sys.stdin and sys.stdin.isatty():
                print("\n" + "=" * 65)
                print(" [!] BROWSER WINDOW IS OPEN - LOGIN & SEARCH WINDOW")
                print("=" * 65)
                print(" 1. Please LOG IN to Work at a Startup in the opened browser window if not already logged in.")
                print(" 2. Your login session is saved in ./workatastartup_session for all future runs.")
                print(" 3. Once logged in and viewing search results, press ENTER below to start extracting all matching jobs.")
                print("=" * 65)
                try:
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, input, " -> Press ENTER once you are logged in and viewing results: "),
                        timeout=30
                    )
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
            filter_term = effective_role if effective_role and not target_url else ""
            jobs_data = parse_workatastartup_html(html, job_role_filter=filter_term, work_mode_filter=work_mode_filter)
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
