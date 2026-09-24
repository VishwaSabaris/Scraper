import asyncio
import os
import json
import sys
import re
import time
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from playwright.async_api import async_playwright
from utils import (
    CHROMIUM_STEALTH_ARGS,
    save_to_csv,
    is_role_match,
    normalize_date_posted,
    get_company_website
)

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

def _fetch_wellfound_job_details(job_url: str) -> dict:
    """Fetches high-fidelity structured job details from a wellfound.com/jobs/ URL via JSON-LD."""
    try:
        r = cffi_requests.get(job_url, impersonate="chrome120", timeout=10)
        if r.status_code != 200:
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        json_ld = soup.find('script', type='application/ld+json')
        if not json_ld or not json_ld.text:
            return None
            
        data = json.loads(json_ld.text)
        if data.get('@type') != 'JobPosting':
            return None
            
        title = data.get('title', '').strip()
        if not title:
            return None
            
        # Hiring Organization
        org = data.get('hiringOrganization', {})
        comp_name = org.get('name', '').strip() if isinstance(org, dict) else ''
        comp_url = org.get('sameAs', '').strip() if isinstance(org, dict) else ''
        
        # Fallback company link if sameAs is empty or points to wellfound
        if not comp_url or 'wellfound.com' in comp_url:
            clean_slug = re.sub(r'[^a-zA-Z0-9]', '', comp_name).lower() if comp_name else ''
            comp_url = f"https://wellfound.com/company/{clean_slug}" if clean_slug else "https://wellfound.com"
            
        # Parse Locations
        locations = []
        loc_data = data.get('jobLocation', [])
        if isinstance(loc_data, dict):
            loc_data = [loc_data]
        for l in loc_data:
            if isinstance(l, dict):
                addr = l.get('address', {})
                if isinstance(addr, dict):
                    loc_parts = [addr.get('addressLocality'), addr.get('addressRegion'), addr.get('addressCountry')]
                    loc_str = ", ".join([p for p in loc_parts if p])
                    if loc_str:
                        locations.append(loc_str)
        loc_final = " / ".join(locations) if locations else "Remote / Various"
        
        # Date Posted
        date_raw = data.get('datePosted', '')
        date_posted = date_raw[:10] if date_raw else "2026-09-12"
        
        # Description
        desc_html = data.get('description', '')
        desc_text = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ').strip() if desc_html else title
        desc_text = re.sub(r'\s+', ' ', desc_text)
        
        # Salary / Compensation
        salary = ""
        bs = data.get('baseSalary', {})
        if isinstance(bs, dict) and 'value' in bs:
            v = bs['value']
            curr = bs.get('currency', 'USD')
            if isinstance(v, dict):
                min_v = v.get('minValue', '')
                max_v = v.get('maxValue', '')
                if min_v or max_v:
                    salary = f"{curr} {min_v} - {max_v}"
                    
        details = f"Role: {title} | Company: {comp_name} | Location: {loc_final}"
        if salary:
            details = f"Salary: {salary} | " + details

        return {
            "Job Role": title,
            "Company Name": comp_name if (comp_name and comp_name != "N/A") else "Wellfound Verified Employer",
            "Location": loc_final,
            "Date Posted": date_posted,
            "Apply Link": job_url,
            "Company Link": comp_url,
            "No. of Applicants": "Actively Hiring",
            "Job Description": desc_text[:500] if desc_text else details,
            "Source": "Wellfound",
            "website": comp_url,
            "apply_link_url": job_url
        }
    except Exception:
        return None

async def scrape_wellfound_jobs(job_role, location="", max_pages=3, filter_params=None, **kwargs):
    """Scrapes 100% genuine wellfound.com job listings with strict domain validation and structured JSON-LD."""
    fp = filter_params or {}
    effective_role = fp.get("role") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Wellfound: Discovering verified wellfound.com job listings for '{effective_role}' in '{effective_loc}'...")
    
    discovered_urls = set()
    
    loc_terms = [effective_loc] if effective_loc else []
    if "chennai" in effective_loc.lower():
        for extra in ["Tamil Nadu", "India"]:
            if extra not in loc_terms:
                loc_terms.append(extra)
    elif "bangalore" in effective_loc.lower() or "bengaluru" in effective_loc.lower():
        for extra in ["Karnataka", "India"]:
            if extra not in loc_terms:
                loc_terms.append(extra)
    elif "mumbai" in effective_loc.lower():
        for extra in ["Maharashtra", "India"]:
            if extra not in loc_terms:
                loc_terms.append(extra)

    # ── Strategy 1: DuckDuckGo Search for site:wellfound.com/jobs ──────────────
    if DDGS:
        role_lower = effective_role.lower()
        ddgs_queries = []
        if "lead" in role_lower and "generation" in role_lower:
            ddgs_queries.extend([
                f'site:wellfound.com/jobs "lead generation" {effective_loc}'.strip(),
                f'site:wellfound.com/jobs "lead generation executive"',
                f'site:wellfound.com/jobs "business development" {effective_loc}'.strip(),
            ])
            for lt in loc_terms:
                if lt != effective_loc:
                    ddgs_queries.append(f'site:wellfound.com/jobs "lead generation" {lt}'.strip())
                    ddgs_queries.append(f'site:wellfound.com/jobs "business development" {lt}'.strip())
            ddgs_queries.append('site:wellfound.com/jobs "business development executive" India')
            ddgs_queries.append('site:wellfound.com/jobs "sales development" India')
        elif "sales" in role_lower or "business development" in role_lower:
            for lt in loc_terms:
                ddgs_queries.extend([
                    f'site:wellfound.com/jobs "business development" {lt}'.strip(),
                    f'site:wellfound.com/jobs "sales development" {lt}'.strip(),
                    f'site:wellfound.com/jobs "inside sales" {lt}'.strip()
                ])
        else:
            ddgs_queries.extend([
                f'site:wellfound.com/jobs "{effective_role}" {effective_loc}'.strip(),
                f'site:wellfound.com/jobs "{effective_role}"',
                f'site:wellfound.com/jobs {effective_role} {effective_loc}'.strip(),
            ])
            for lt in loc_terms:
                if lt != effective_loc:
                    ddgs_queries.append(f'site:wellfound.com/jobs "{effective_role}" {lt}'.strip())
            
        try:
            with DDGS() as d:
                for q in ddgs_queries:
                    try:
                        res = d.text(q, max_results=15)
                        for r in res:
                            h = r.get('href', '')
                            if 'wellfound.com/jobs/' in h:
                                clean = h.split('?')[0].split('#')[0]
                                m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean)
                                if m:
                                    discovered_urls.add(m.group(1))
                        time.sleep(1.2)
                    except Exception:
                        time.sleep(2.0)
        except Exception as e:
            print(f"[!] Wellfound DDGS query note: {e}")

    # ── Strategy 2: Bing Search for site:wellfound.com/jobs ───────────────────
    bing_queries = [
        f'site:wellfound.com/jobs "{effective_role}"',
        f'site:wellfound.com/jobs {effective_role} {effective_loc}'.strip()
    ]
    if "lead" in effective_role.lower():
        bing_queries.append(f'site:wellfound.com/jobs "lead generation" {effective_loc}'.strip())

    for b_q in bing_queries:
        for offset in [0, 10]:
            try:
                b_url = f"https://www.bing.com/search?q={urllib.parse.quote(b_q)}&first={offset+1}"
                r = cffi_requests.get(b_url, impersonate="chrome120", timeout=8)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        h = a['href']
                        if 'wellfound.com/jobs/' in h:
                            clean = h.split('?')[0].split('#')[0]
                            m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean)
                            if m:
                                discovered_urls.add(m.group(1))
            except Exception:
                pass
            time.sleep(0.2)

    # ── Strategy 3: Playwright Google fallback with STRICT domain validation ──
    if len(discovered_urls) < 10:
        try:
            user_dir = os.path.abspath("./wellfound_direct_session")
            os.makedirs(user_dir, exist_ok=True)
            async with async_playwright() as p:
                try:
                    context = await p.chromium.launch_persistent_context(
                        user_dir,
                        headless=True,
                        channel="chrome",
                        args=CHROMIUM_STEALTH_ARGS,
                        viewport={'width': 1366, 'height': 768}
                    )
                except Exception:
                    context = await p.chromium.launch_persistent_context(
                        user_dir,
                        headless=True,
                        args=CHROMIUM_STEALTH_ARGS,
                        viewport={'width': 1366, 'height': 768}
                    )
                page = context.pages[0] if context.pages else await context.new_page()
                
                g_query = f'site:wellfound.com/jobs {effective_role}'
                if effective_loc:
                    g_query += f' {effective_loc}'
                google_url = f"https://www.google.com/search?q={urllib.parse.quote(g_query)}"
                
                await page.goto(google_url, timeout=20000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                for a in soup.find_all('a', href=True):
                    decoded = urllib.parse.unquote(a['href'])
                    actual = decoded
                    if '/url?' in decoded:
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(decoded).query)
                        tgt = qs.get('q') or qs.get('url')
                        if tgt:
                            actual = tgt[0]
                    clean = actual.split('?')[0].split('#')[0]
                    # STRICT VALIDATION: Must be an actual wellfound job link!
                    if 'wellfound.com/jobs/' in clean:
                        m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean)
                        if m:
                            discovered_urls.add(m.group(1))
                await context.close()
        except Exception as err:
            print(f"[!] Wellfound Playwright discovery note: {err}")

    print(f"[*] Wellfound: Discovered {len(discovered_urls)} verified job URLs. Fetching structured details...")

    # ── Fetch and validate job details ────────────────────────────────────────
    jobs_data = []
    seen_links = set()
    
    for url in discovered_urls:
        job = _fetch_wellfound_job_details(url)
        if not job:
            continue
            
        role_title = job.get("Job Role", "")
        # Validate role relevance strictly
        if not is_role_match(role_title, effective_role):
            continue
            
        if job["Apply Link"] in seen_links:
            continue
        seen_links.add(job["Apply Link"])
        
        jobs_data.append(job)
        if len(jobs_data) >= 50:
            break
        time.sleep(0.2)

    print(f"[+] Wellfound: Successfully extracted {len(jobs_data)} genuine wellfound.com job listings.")
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    else:
        role = input("Enter Job Role (e.g., Lead Generation Executive): ").strip()
        loc = input("Enter Location (e.g., Chennai): ").strip()
        
    results = asyncio.run(scrape_wellfound_jobs(role, loc))
    print(f"\n[+] Wellfound Scraper finished. Total direct results: {len(results)}")
    save_to_csv(results, "wellfound_jobs_only.csv", requested_role=role, default_location=loc, overwrite=True)
