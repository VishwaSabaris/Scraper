import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.workatastartup.com/jobs/62175', headers={'User-Agent': 'Mozilla/5.0'})
s = BeautifulSoup(r.text, 'html.parser')
print("Title:", s.title.text if s.title else "No title")
for h in s.find_all(['h1', 'h2', 'h3', 'h4', 'a']):
    if '/companies/' in str(h.get('href')):
        print(f"Company link on job page: {h.text.strip()} -> {h['href']}")
