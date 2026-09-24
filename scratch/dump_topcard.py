import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.linkedin.com/jobs/view/4465385340', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
s = BeautifulSoup(r.text, 'html.parser')
topcard = s.find('section', class_=lambda c: c and 'topcard' in c) or s.find('div', class_=lambda c: c and 'top-card' in c)
if topcard:
    print(topcard.prettify()[:1500])
else:
    print("No topcard found. Dumping body headers:")
    for h in s.find_all(['h1', 'h2', 'h3', 'h4']):
        print(h.name, h.get('class'), "->", h.text.strip())
