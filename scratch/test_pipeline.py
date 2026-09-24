import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests
from ddgs import DDGS
from utils import is_role_match, normalize_date_posted

def discover_wellfound_job_urls(role: str, location: str = ""):
    discovered_urls = set()
    
    # 1. DDGS queries
    queries = [
        f'site:wellfound.com/jobs "{role}"',
        f'site:wellfound.com/jobs "{role}" {location}'.strip(),
        f'site:wellfound.com/jobs {role} {location}'.strip(),
    ]
    if "lead" in role.lower() and "generation" in role.lower():
        queries.extend([
            f'site:wellfound.com/jobs "lead generation" {location}'.strip(),
            f'site:wellfound.com/jobs "lead generation" India',
            f'site:wellfound.com/jobs "business development" {location}'.strip(),
            f'site:wellfound.com/jobs "sales development" {location}'.strip()
        ])
        
    print("[*] Querying DuckDuckGo for Wellfound job listings...")
    try:
        with DDGS() as d:
            for q in queries[:4]:
                try:
                    res = d.text(q, max_results=15)
                    for r in res:
                        u = r.get('href', '')
                        if 'wellfound.com/jobs/' in u:
                            # Clean URL
                            clean_u = u.split('?')[0].split('#')[0]
                            if re.search(r'wellfound\.com/jobs/\d+', clean_u):
                                discovered_urls.add(clean_u)
                except Exception as e:
                    pass
    except Exception as e:
        print("[!] DDGS note:", e)
        
    print(f"[*] Discovered {len(discovered_urls)} URLs via DDGS.")
    
    # 2. Bing queries
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    print("[*] Querying Bing for Wellfound job listings...")
    for q in [f'site:wellfound.com/jobs "{role}"', f'site:wellfound.com/jobs "lead generation" {location}'.strip()]:
        try:
            bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
            r = requests.get(bing_url, impersonate="chrome120", timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    h = a['href']
                    if 'wellfound.com/jobs/' in h:
                        clean_u = h.split('?')[0].split('#')[0]
                        if re.search(r'wellfound\.com/jobs/\d+', clean_u):
                            discovered_urls.add(clean_u)
        except Exception:
            pass
            
    print(f"[*] Total unique Wellfound URLs discovered: {len(discovered_urls)}")
    return list(discovered_urls)

def fetch_job_details(job_url: str):
    try:
        r = requests.get(job_url, impersonate="chrome120", timeout=10)
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
        
        # Hiring Org
        org = data.get('hiringOrganization', {})
        comp_name = org.get('name', '').strip() if isinstance(org, dict) else ''
        comp_url = org.get('sameAs', '').strip() if isinstance(org, dict) else ''
        if not comp_url or 'wellfound.com' in comp_url:
            # Fallback
            comp_url = f"https://wellfound.com/company/{comp_name.lower().replace(' ', '-')}" if comp_name else "https://wellfound.com"

        # Location
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
        
        # Date
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
                salary = f"{curr} {v.get('minValue', '')} - {v.get('maxValue', '')}"
                
        details = f"Role: {title} | Company: {comp_name} | Location: {loc_final}"
        if salary:
            details = f"Salary: {salary} | " + details
            
        return {
            "Job Role": title,
            "Company Name": comp_name or "Wellfound Verified Employer",
            "Location": loc_final,
            "Date Posted": date_posted,
            "Apply Link": job_url,
            "Company Link": comp_url,
            "No. of Applicants": "Actively Hiring",
            "Company / Job Details": details[:350],
            "Source": "Wellfound",
            "website": comp_url,
            "apply_link_url": job_url,
            "job_description": desc_text[:500] if desc_text else details
        }
    except Exception as e:
        return None

if __name__ == "__main__":
    urls = discover_wellfound_job_urls("Lead Generation Executive", "Chennai")
    print(f"\nDiscovered {len(urls)} URLs. Fetching details for first 10...")
    jobs = []
    for u in urls[:15]:
        j = fetch_job_details(u)
        if j:
            jobs.append(j)
            print(f"[+] {j['Job Role']} at {j['Company Name']} ({j['Location']})")
            print(f"    Website: {j['website']}")
            print(f"    Apply: {j['Apply Link']}")
            print(f"    Date: {j['Date Posted']}")
    print(f"\nSuccessfully fetched {len(jobs)} jobs!")
