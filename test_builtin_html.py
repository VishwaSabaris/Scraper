from curl_cffi import requests
from bs4 import BeautifulSoup
import re

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
res = requests.get('https://builtin.com/jobs/office?search=Sales+Development+Representative&allLocations=true', headers=headers, impersonate='chrome120')
print('Status:', res.status_code)
soup = BeautifulSoup(res.text, 'html.parser')
cards = soup.select("[data-id='job-card'], div[class*='job-card'], div[id^='job-card-'], [class*='JobCard']")
print('Cards found:', len(cards))
if cards:
    c = cards[0]
    print('Card classes:', c.get('class'))
    print('Links:', [a.get('href') for a in c.find_all('a')])
    print('All text:', c.get_text(separator=' | ')[:400])
