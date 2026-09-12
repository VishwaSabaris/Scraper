import requests
import json
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 1. Foundit
print("=== 1. Foundit ===")
try:
    r = requests.get('https://www.foundit.in/srp/results?query=python&locations=bangalore', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        page_props = data.get('props', {}).get('pageProps', {})
        print("Foundit pageProps keys:", list(page_props.keys())[:10])
        # Find job list
        for k in ['jobSearchResults', 'searchResults', 'jobs', 'initialState', 'data', 'srpData']:
            if k in page_props:
                print(f"Foundit prop '{k}' type:", type(page_props[k]))
    else:
        cards = soup.select('.srpResultCard') or soup.select('[class*="card"]') or soup.select('[class*="jobTuple"]')
        print("Foundit cards count:", len(cards))
except Exception as e:
    print("Foundit error:", e)

# 2. Apna
print("\n=== 2. Apna ===")
try:
    r = requests.get('https://apna.co/jobs?search=true&text=python&location=Bengaluru', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        page_props = data.get('props', {}).get('pageProps', {})
        print("Apna pageProps keys:", list(page_props.keys())[:10])
        if 'jobs' in page_props:
            print("Apna 'jobs' count:", len(page_props['jobs']))
            print("Sample apna job keys:", list(page_props['jobs'][0].keys()) if page_props['jobs'] else [])
        elif 'initialState' in page_props:
            print("Apna initialState keys:", list(page_props['initialState'].keys()))
        elif 'jobList' in page_props:
            print("Apna jobList count:", len(page_props['jobList']))
        else:
            def find_keys(d, target, depth=0):
                if depth > 4: return
                if isinstance(d, dict):
                    for k, v in d.items():
                        if target in k.lower():
                            print(f"Apna matching key: {k} (type: {type(v)})")
                        find_keys(v, target, depth+1)
                elif isinstance(d, list) and d:
                    find_keys(d[0], target, depth+1)
            find_keys(page_props, 'job')
except Exception as e:
    print("Apna error:", e)

# 3. Instahyre
print("\n=== 3. Instahyre ===")
try:
    r = requests.get('https://www.instahyre.com/search-jobs/?search=true&job_type=0&skills=Python', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('.employer-row') or soup.select('.opportunity-container') or soup.select('[id^="job-"]') or soup.select('.job-card')
    print("Instahyre cards count:", len(cards))
    if not cards:
        scripts = [s.string for s in soup.find_all('script') if s.string and ('opportunities' in s.string or 'results' in s.string or 'jobs' in s.string)]
        print("Instahyre scripts with jobs/opportunities:", len(scripts))
        for idx, sc in enumerate(scripts[:2]):
            print(f"Script {idx} snippet:", sc[:150])
except Exception as e:
    print("Instahyre error:", e)

# 4. Internshala
print("\n=== 4. Internshala ===")
try:
    r = requests.get('https://internshala.com/jobs/python-jobs/', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('.individual_internship') or soup.select('.job-card') or soup.select('[class*="individual_internship"]')
    print("Internshala cards count:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('.job-title-href') or c.select_one('a.view_detail_button') or c.select_one('.heading_4_5') or c.select_one('.profile')
        comp = c.select_one('.company-name') or c.select_one('.link_display_like_text') or c.select_one('.company_name')
        loc = c.select_one('.location_link') or c.select_one('#location_names') or c.select_one('.locations')
        sal = c.select_one('.salary') or c.select_one('.stipend')
        print("Sample Internshala:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp', "|", loc.text.strip() if loc else 'No loc')
except Exception as e:
    print("Internshala error:", e)

# 5. Shine
print("\n=== 5. Shine ===")
try:
    r = requests.get('https://www.shine.com/job-search/python-jobs-in-bangalore', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        page_props = data.get('props', {}).get('pageProps', {})
        print("Shine pageProps keys:", list(page_props.keys())[:10])
        for k in ['jobData', 'jobs', 'initialState', 'data', 'searchResult']:
            if k in page_props:
                print(f"Shine prop '{k}':", type(page_props[k]))
    else:
        cards = soup.select('.jobCard') or soup.select('[class*="jobCard"]') or soup.select('[itemtype="https://schema.org/JobPosting"]')
        print("Shine cards count:", len(cards))
except Exception as e:
    print("Shine error:", e)
