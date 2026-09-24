import urllib.request
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

for test_url in [
    'https://wellfound.com/location/india',
    'https://wellfound.com/role/l/sales-development-representative/india',
    'https://wellfound.com/jobs'
]:
    print(f"\n--- Checking {test_url} ---")
    try:
        req = urllib.request.Request(test_url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            print("No __NEXT_DATA__")
            continue
        data = json.loads(next_data.string)
        apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
        job_keys = [k for k in apollo if k.startswith('JobListing:')]
        print(f"JobListing count: {len(job_keys)}")
        for k in job_keys[:5]:
            j = apollo[k]
            startup_ref = j.get('startup', {}).get('__ref', '')
            startup = apollo.get(startup_ref, {})
            print(f"  Role: {j.get('title')} | Comp: {startup.get('name')} | Locs: {j.get('locationNames')} | ID: {j.get('id')} | Slug: {j.get('slug')}")
    except Exception as e:
        print(f"Error: {e}")
