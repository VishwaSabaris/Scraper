import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.linkedin.com/jobs/view/4465385340', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
s = BeautifulSoup(r.text, 'html.parser')
for x in s.find_all(class_=lambda c: c and ('job-insight' in c or 'bullet' in c or 'workplace' in c or 'description' in c)):
    t = x.text.strip()
    if 'remote' in t.lower() or 'on-site' in t.lower() or 'hybrid' in t.lower():
        print("MATCH:", t[:100])
