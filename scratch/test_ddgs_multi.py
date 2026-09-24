import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import json
import time
from ddgs import DDGS
from curl_cffi import requests
from bs4 import BeautifulSoup

queries = [
    'site:wellfound.com/jobs "lead generation"',
    'site:wellfound.com/jobs "lead generation" India',
    'site:wellfound.com/jobs "lead generation" Chennai',
    'site:wellfound.com/jobs "lead generation executive"',
    'site:wellfound.com/jobs "business development" Chennai',
    'site:wellfound.com/jobs "business development executive" India',
    'site:wellfound.com/jobs "sales development" India',
    'site:wellfound.com/jobs "demand generation"',
    'site:wellfound.com/jobs "inside sales" India',
    'site:wellfound.com/jobs "sales representative" India'
]

discovered = set()
with DDGS() as d:
    for q in queries:
        try:
            print(f"Querying: {q}...")
            res = list(d.text(q, max_results=15))
            for r in res:
                h = r.get('href', '')
                if 'wellfound.com/jobs/' in h:
                    clean = h.split('?')[0].split('#')[0]
                    if re.search(r'wellfound\.com/jobs/\d+', clean):
                        discovered.add(clean)
            print(f"  Total discovered so far: {len(discovered)}")
            time.sleep(1.2)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(2)

print(f"\nDiscovered {len(discovered)} unique Wellfound job URLs!")
for u in sorted(discovered):
    print(" ", u)
