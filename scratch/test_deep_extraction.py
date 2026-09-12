import requests
import json
import re
from bs4 import BeautifulSoup

# Test Apna Next Data structure
print("--- APNA ---")
try:
    r = requests.get('https://apna.co/jobs?search=true&text=Python+Developer&location=Bengaluru', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    nd = soup.find('script', id='__NEXT_DATA__')
    if nd:
        d = json.loads(nd.string)
        props = d.get('props', {}).get('pageProps', {})
        print("Apna pageProps keys:", list(props.keys()))
        # Check if there is a dehydratedState or queryClient
        dehydrated = props.get('dehydratedState', {})
        if dehydrated:
            queries = dehydrated.get('queries', [])
            print(f"Apna dehydratedState queries: {len(queries)}")
            for q in queries:
                qkey = q.get('queryKey', [])
                print("QueryKey:", qkey)
                state_data = q.get('state', {}).get('data', {})
                if isinstance(state_data, dict):
                    print("State data keys:", list(state_data.keys()))
                    if 'results' in state_data:
                        print("Results count in apna:", len(state_data['results']))
                        if state_data['results']:
                            print("Sample Apna result:", state_data['results'][0].get('title'), "|", state_data['results'][0].get('company_name'))
except Exception as e:
    print("Apna err:", e)

# Test Shine Next Data structure
print("\n--- SHINE ---")
try:
    r = requests.get('https://www.shine.com/job-search/python-jobs-in-bangalore', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    nd = soup.find('script', id='__NEXT_DATA__')
    if nd:
        d = json.loads(nd.string)
        pageProps = d.get('props', {}).get('pageProps', {})
        pageData = pageProps.get('pageData', {})
        print("Shine pageData keys:", list(pageData.keys()) if isinstance(pageData, dict) else type(pageData))
        if isinstance(pageData, dict) and 'jobData' in pageData:
            jobData = pageData['jobData']
            print("Shine jobData count:", len(jobData))
            if jobData:
                print("Sample shine job:", jobData[0].get('job_title'), "|", jobData[0].get('company_name'), "|", jobData[0].get('loc_details'))
except Exception as e:
    print("Shine err:", e)

# Test BuiltIn structure
print("\n--- BUILTIN ---")
try:
    r = requests.get('https://builtin.com/jobs?search=python', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('[data-id="job-card"]')
    print(f"BuiltIn cards count: {len(cards)}")
    if cards:
        c = cards[0]
        title = c.select_one('h2 a') or c.select_one('a[data-id="job-title"]') or c.select_one('h2')
        comp = c.select_one('[data-id="company-title"]') or c.select_one('span.company-title')
        loc = c.select_one('[data-id="location"]') or c.select_one('span.location')
        print("Sample BuiltIn:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp', "|", loc.text.strip() if loc else 'No loc')
except Exception as e:
    print("BuiltIn err:", e)

