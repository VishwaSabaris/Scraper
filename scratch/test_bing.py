import urllib.parse, re, time
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

queries = [
    'site:wellfound.com/jobs "lead generation" Chennai',
    'site:wellfound.com/jobs "lead generation" "Tamil Nadu"',
    'site:wellfound.com/jobs "lead generation" India',
    'site:wellfound.com/jobs "business development" Chennai',
    'site:wellfound.com/jobs "business development" "Tamil Nadu"',
    'site:wellfound.com/jobs "lead generation executive"',
    'site:wellfound.com/jobs "business development executive" India',
    'site:wellfound.com/jobs "sales development" India'
]
found = set()
for q in queries:
    for offset in [0, 10]:
        url = f'https://www.bing.com/search?q={urllib.parse.quote(q)}&first={offset+1}'
        try:
            r = cffi_requests.get(url, impersonate='chrome120', timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', a['href'])
                    if m:
                        found.add(m.group(1))
        except Exception:
            pass
        time.sleep(0.3)
print(f"Total Bing found: {len(found)}")
for u in sorted(found):
    print(" ", u)
