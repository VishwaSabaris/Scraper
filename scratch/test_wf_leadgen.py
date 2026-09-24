import urllib.request
from bs4 import BeautifulSoup
import json
import datetime
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def extract_wellfound_page(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
    except Exception as e:
        return []
        
    soup = BeautifulSoup(html, 'html.parser')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if not next_data:
        return []
        
    data = json.loads(next_data.string)
    apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
    
    startups = {}
    for k, v in apollo.items():
        if (k.startswith('StartupResult:') or k.startswith('Startup:')) and isinstance(v, dict):
            startups[k] = v
            if v.get('id'):
                startups[str(v.get('id'))] = v

    results = []
    for k, v in apollo.items():
        if ('JobListing' in k) and isinstance(v, dict):
            title = v.get('title')
            slug = v.get('slug')
            job_id = v.get('id')
            if not title or not job_id:
                continue
                
            comp_name = "N/A"
            comp_slug = ""
            startup_ref = v.get('startup', {}).get('__ref') if isinstance(v.get('startup'), dict) else None
            if startup_ref and startup_ref in apollo:
                st = apollo[startup_ref]
                comp_name = st.get('name') or comp_name
                comp_slug = st.get('slug') or ""
            else:
                for s_key, s_val in startups.items():
                    if isinstance(s_val, dict):
                        h_list = s_val.get('highlightedJobListings', [])
                        if any(item.get('__ref') == k for item in h_list if isinstance(item, dict)):
                            comp_name = s_val.get('name') or comp_name
                            comp_slug = s_val.get('slug') or ""
                            break

            locs = v.get('locationNames', [])
            loc_str = ", ".join(locs) if locs else "Remote / Various"
            
            live_start = v.get('liveStartAt')
            date_posted = "N/A"
            if live_start:
                try:
                    date_posted = datetime.datetime.fromtimestamp(live_start).strftime('%Y-%m-%d')
                except Exception:
                    pass
            
            apply_link = f"https://wellfound.com/jobs/{job_id}-{slug}"
            company_link = f"https://wellfound.com/company/{comp_slug}" if comp_slug else "https://wellfound.com"
            desc = v.get('description', '')
            comp = v.get('compensation', '')
            details = desc[:300] if desc else f"Role: {title} | Company: {comp_name} | Location: {loc_str}"
            if comp:
                details = f"Compensation: {comp} | " + details

            results.append({
                "Job Role": title,
                "Company Name": comp_name,
                "Location": loc_str,
                "Date Posted": date_posted,
                "Apply Link": apply_link,
                "Company Link": company_link,
                "No. of Applicants": "Actively Hiring",
                "Company / Job Details": details[:350],
                "Source": "Wellfound",
                "website": company_link,
                "apply_link_url": apply_link,
                "job_description": desc[:350] if desc else title
            })
    return results

urls = [
    'https://wellfound.com/role/l/sales/chennai',
    'https://wellfound.com/role/l/sales-development-representative/india',
    'https://wellfound.com/role/l/business-development/india',
    'https://wellfound.com/role/l/sales/india'
]

all_jobs = []
seen_ids = set()

for u in urls:
    jobs = extract_wellfound_page(u)
    print(f"{u} -> {len(jobs)} jobs")
    for j in jobs:
        if j['Apply Link'] not in seen_ids:
            seen_ids.add(j['Apply Link'])
            all_jobs.append(j)

print(f"\nTotal unique jobs scraped: {len(all_jobs)}")

# Check matching for Lead Generation Executive / Sales / BD
keywords = ['lead', 'generation', 'sales', 'business development', 'sdr', 'bde', 'representative', 'executive', 'account']
matching = []
for j in all_jobs:
    t = j['Job Role'].lower()
    if any(k in t for k in keywords):
        matching.append(j)

print(f"Matching sales/lead/bde jobs: {len(matching)}")
for m in matching[:15]:
    print(f"[{m['Job Role']}] | [{m['Company Name']}] | [{m['Location']}] | {m['Apply Link']}")
