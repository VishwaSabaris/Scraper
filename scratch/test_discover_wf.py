import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import json
import time
import urllib.parse
from bs4 import BeautifulSoup
from curl_cffi import requests
from ddgs import DDGS

def get_all_wellfound_urls(role="Lead Generation Executive", location="Chennai"):
    urls = set()
    
    # Clean terms
    role_terms = [t for t in role.split() if len(t) > 2]
    
    # 1. Bing search queries
    bing_queries = [
        f'site:wellfound.com/jobs "{role}"',
        f'site:wellfound.com/jobs "lead generation" {location}',
        f'site:wellfound.com/jobs "lead generation" India',
        f'site:wellfound.com/jobs "lead generation"',
        f'site:wellfound.com/jobs "lead generation executive"',
        f'site:wellfound.com/jobs "business development" {location}',
        f'site:wellfound.com/jobs "business development executive" India',
        f'site:wellfound.com/jobs "sales development representative" India',
        f'site:wellfound.com/jobs "demand generation" India',
        f'site:wellfound.com/jobs "inside sales" India'
    ]
    
    print(f"[*] Querying Bing for {len(bing_queries)} target searches...")
    for q in bing_queries:
        for offset in [0, 10]:
            try:
                b_url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}&first={offset+1}"
                r = requests.get(b_url, impersonate="chrome120", timeout=8)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        h = a['href']
                        if 'wellfound.com/jobs/' in h:
                            clean_u = h.split('?')[0].split('#')[0]
                            m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean_u)
                            if m:
                                urls.add(m.group(1))
            except Exception:
                pass
        time.sleep(0.3)
        
    print(f"[*] Discovered {len(urls)} URLs from Bing.")
    
    # 2. DDGS queries
    ddgs_queries = [
        f'site:wellfound.com/jobs "lead generation" India',
        f'site:wellfound.com/jobs "lead generation" {location}',
        f'site:wellfound.com/jobs "{role}"',
        f'site:wellfound.com/jobs "business development" {location}',
        f'site:wellfound.com/jobs "sales development" India'
    ]
    print(f"[*] Querying DDGS for {len(ddgs_queries)} target searches...")
    try:
        with DDGS() as d:
            for q in ddgs_queries:
                try:
                    res = d.text(q, max_results=20)
                    for r in res:
                        h = r.get('href', '')
                        if 'wellfound.com/jobs/' in h:
                            clean_u = h.split('?')[0].split('#')[0]
                            m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean_u)
                            if m:
                                urls.add(m.group(1))
                    time.sleep(0.8)
                except Exception as e:
                    pass
    except Exception as e:
        pass
        
    print(f"[*] Total unique Wellfound URLs discovered: {len(urls)}")
    return list(urls)

if __name__ == "__main__":
    urls = get_all_wellfound_urls("Lead Generation Executive", "Chennai")
    print(f"Discovered {len(urls)} job URLs:")
    for u in sorted(urls):
        print(" ", u)
