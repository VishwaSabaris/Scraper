import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.linkedin.com/jobs/view/4465385340', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
s = BeautifulSoup(r.text, 'html.parser')
desc = s.find('div', class_=lambda c: c and 'description' in c)
if desc:
    print(desc.text[:1500].encode('ascii', errors='replace').decode())
