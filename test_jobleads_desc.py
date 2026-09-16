from curl_cffi import requests
from bs4 import BeautifulSoup
import json

url = "https://www.jobleads.com/job/sales-development-representative-bengaluru-67d9fa89e8293557e103980c"
# Or sample URL from our scraped jobs
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
res = requests.get("https://www.jobleads.com/in/jobs/l/Bangalore/q/Sales%20Development%20Representative", headers=headers, impersonate="chrome120")
soup = BeautifulSoup(res.text, "html.parser")
cards = soup.select("[data-testid='search-job-card'], .animated-list-item")
print("JobLeads cards found:", len(cards))
if cards:
    c = cards[0]
    print("Card text:", c.get_text(separator=" | ")[:400])
    link = c.find("a", href=True)
    if link:
        detail_url = "https://www.jobleads.com" + link['href'] if link['href'].startswith('/') else link['href']
        print("Detail URL:", detail_url)
        res_d = requests.get(detail_url, headers=headers, impersonate="chrome120")
        soup_d = BeautifulSoup(res_d.text, "html.parser")
        for s in soup_d.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(s.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    print("Found JobPosting JSON-LD in JobLeads! Description length:", len(data.get('description', '')))
            except Exception:
                pass
        desc_el = soup_d.select_one("[data-testid='job-description'], .job-description, .job-details-text")
        if desc_el:
            print("Found desc_el in JobLeads! Text length:", len(desc_el.get_text().strip()))
