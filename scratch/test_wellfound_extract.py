import urllib.request
from bs4 import BeautifulSoup
import json
import datetime

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def test_extract(url):
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers=headers)
    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if not next_data:
        print("No __NEXT_DATA__")
        return []
    
    data = json.loads(next_data.string)
    apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
    
    jobs = []
    # Build startup lookup map
    startups = {}
    for k, v in apollo.items():
        if k.startswith('StartupResult:') or k.startswith('Startup:'):
            startups[k] = v
            # Also map by ID or other keys
            for ref_k in [k, v.get('id')]:
                if ref_k:
                    startups[str(ref_k)] = v

    for k, v in apollo.items():
        if 'JobListing' in k and isinstance(v, dict):
            title = v.get('title')
            slug = v.get('slug')
            job_id = v.get('id')
            if not title or not job_id:
                continue
            
            # Find associated startup
            comp_name = "N/A"
            comp_slug = ""
            comp_url = ""
            
            # Check startup ref
            startup_ref = v.get('startup', {}).get('__ref') if isinstance(v.get('startup'), dict) else None
            if startup_ref and startup_ref in apollo:
                st = apollo[startup_ref]
                comp_name = st.get('name') or comp_name
                comp_slug = st.get('slug') or ""
            else:
                # Find startup that has this job in highlightedJobListings or jobListings
                for s_key, s_val in startups.items():
                    if isinstance(s_val, dict):
                        h_list = s_val.get('highlightedJobListings', [])
                        if any(item.get('__ref') == k for item in h_list if isinstance(item, dict)):
                            comp_name = s_val.get('name') or comp_name
                            comp_slug = s_val.get('slug') or ""
                            break

            locs = v.get('locationNames', [])
            loc_str = ", ".join(locs) if locs else "Remote / Various"
            
            # Date
            live_start = v.get('liveStartAt')
            date_posted = "N/A"
            if live_start:
                try:
                    date_posted = datetime.datetime.fromtimestamp(live_start).strftime('%Y-%m-%d')
                except Exception:
                    pass
            
            # Links
            apply_link = f"https://wellfound.com/jobs/{job_id}-{slug}"
            if comp_slug:
                company_link = f"https://wellfound.com/company/{comp_slug}"
            else:
                company_link = "https://wellfound.com"
                
            desc = v.get('description', '')
            comp = v.get('compensation', '')
            details = desc[:300] if desc else f"Role: {title} | Company: {comp_name} | Location: {loc_str}"
            if comp:
                details = f"Compensation: {comp} | " + details

            jobs.append({
                "Job Role": title,
                "Company Name": comp_name,
                "Location": loc_str,
                "Date Posted": date_posted,
                "Apply Link": apply_link,
                "Company Link": company_link,
                "No. of Applicants": "Actively Hiring",
                "Company / Job Details": details[:350],
                "Source": "Wellfound"
            })
            
    print(f"Extracted {len(jobs)} jobs.")
    return jobs

if __name__ == "__main__":
    jobs_chennai = test_extract('https://wellfound.com/role/l/sales/chennai')
    jobs_india = test_extract('https://wellfound.com/role/l/sales/india')

    print('\n--- Chennai URL Jobs (Indian/Remote locations) ---')
    for j in jobs_chennai:
        loc = j['Location'].lower()
        if any(x in loc for x in ['chennai', 'india', 'tamil', 'bangalore', 'bengaluru', 'remote', 'hyderabad', 'delhi', 'mumbai']):
            print(f"{j['Job Role']} | {j['Company Name']} | {j['Location']}")

    print('\n--- India URL Jobs ---')
    for j in jobs_india:
        print(f"{j['Job Role']} | {j['Company Name']} | {j['Location']}")

