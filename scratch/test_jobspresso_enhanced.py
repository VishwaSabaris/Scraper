from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import is_role_match

role = 'Lead Generation Executive'
terms = [role] + [t for t in role.split() if len(t) > 3]
all_jobs = []
for term in terms:
    url = f'https://jobspresso.co/feed/?post_type=job_listing&s={urllib.parse.quote(term)}&paged=1'
    r = requests.get(url, impersonate='chrome120')
    s = BeautifulSoup(r.text, 'html.parser')
    items = s.find_all('item')
    print(f'Term "{term}" -> {len(items)} items')
    for it in items:
        t = it.find('title').text.strip()
        if is_role_match(t, role) or any(w.lower() in t.lower() for w in role.split() if len(w) > 3):
            all_jobs.append(t)
            
print('Total matched:', len(all_jobs))
for j in all_jobs[:5]:
    print(' *', j)
