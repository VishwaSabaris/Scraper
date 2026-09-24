import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.linkedin.com/jobs/view/4465385340', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
s = BeautifulSoup(r.text, 'html.parser')
for li in s.find_all(['li', 'div', 'span'], class_=lambda c: c and ('criteria' in c or 'job-insight' in c or 'tophead' in c or 'sub-header' in c)):
    print("CRITERIA/INSIGHT:", li.name, li.get('class'), "->", li.text.strip().replace('\n', ' '))
