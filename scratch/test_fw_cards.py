from curl_cffi import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.freshersworld.com/jobs/jobsearch/python-jobs-in-bangalore?offset=0&limit=20', impersonate='chrome120')
soup = BeautifulSoup(r.text, 'html.parser')
cards = soup.select('.job-container, .jobs-today, .col-md-12.job-container, .job-contents')
for idx, c in enumerate(cards[:5]):
    title_el = c.select_one('.job-title, .latest-jobs-title, h3 a, h2 a, a.bold') or c.select_one('a')
    comp_el = c.select_one('.company-name, .latest-jobs-company')
    print(f"Card {idx}: Title={title_el.text.strip() if title_el else None} | Comp={comp_el.text.strip() if comp_el else None}")
    for a in c.find_all('a'):
        if a.get('href') and '/jobs/' in a.get('href'):
            print(f"   Link: text={a.text.strip()} href={a.get('href')}")
