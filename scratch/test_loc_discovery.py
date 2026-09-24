import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import json
import time
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from ddgs import DDGS
from utils import is_role_match

def test_discovery(role="Lead Generation Executive", location="Chennai"):
    discovered_urls = set()
    
    # Location expansions for Indian cities
    loc_expansions = [location] if location else []
    loc_lower = location.lower()
    if loc_lower in ['chennai', 'madras']:
        loc_expansions.extend(['Tamil Nadu', 'India'])
    elif loc_lower in ['bangalore', 'bengaluru']:
        loc_expansions.extend(['Karnataka', 'India'])
    elif loc_lower in ['mumbai', 'bombay', 'pune']:
        loc_expansions.extend(['Maharashtra', 'India'])
    elif loc_lower in ['delhi', 'noida', 'gurgaon', 'gurugram']:
        loc_expansions.extend(['NCR', 'India'])
    elif loc_lower and loc_lower not in ['india', 'remote', 'worldwide', 'any']:
        loc_expansions.append('India')
        
    # Query list
    ddgs_queries = [
        f'site:wellfound.com/jobs "{role}"',
        f'site:wellfound.com/jobs {role} {location}'.strip(),
    ]
    for loc in loc_expansions:
        ddgs_queries.append(f'site:wellfound.com/jobs "lead generation" {loc}')
        ddgs_queries.append(f'site:wellfound.com/jobs "business development" {loc}')
    ddgs_queries.append(f'site:wellfound.com/jobs "lead generation executive"')
    ddgs_queries.append(f'site:wellfound.com/jobs "lead generation"')
    
    print(f"Generated {len(ddgs_queries)} queries.")
    with DDGS() as d:
        for q in ddgs_queries:
            try:
                res = list(d.text(q, max_results=15))
                for r in res:
                    h = r.get('href', '')
                    if 'wellfound.com/jobs/' in h:
                        clean = h.split('?')[0].split('#')[0]
                        m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', clean)
                        if m:
                            discovered_urls.add(m.group(1))
                time.sleep(0.5)
            except Exception as e:
                pass

    print(f"Discovered {len(discovered_urls)} unique Wellfound URLs.")
    return list(discovered_urls)

if __name__ == "__main__":
    urls = test_discovery()
    for u in urls[:10]:
        print(" ", u)
