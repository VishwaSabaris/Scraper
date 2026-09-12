import requests
from curl_cffi import requests as c_requests
from bs4 import BeautifulSoup
import json

# 1. Dice check
print("=== DICE CHECK ===")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.dice.com',
        'Referer': 'https://www.dice.com/jobs?q=Python&location=Remote'
    }
    # Test Dice Search API endpoints
    ep1 = "https://job-search-api.dice.com/v1/jobs/search?q=Python&location=Remote&pageSize=20&page=1"
    ep2 = "https://www.dice.com/api/jobsearch/paged?q=Python&location=Remote&pageSize=20&page=1"
    ep3 = "https://job-search-api.dice.com/v2/jobs/search?q=Python&location=Remote&pageSize=20&page=1"
    for ep in [ep1, ep2, ep3]:
        try:
            r = c_requests.get(ep, headers=headers, impersonate='chrome120', timeout=10)
            print(f"Dice {ep[:50]}: status {r.status_code}, len {len(r.text)}")
            if r.status_code == 200:
                d = r.json()
                print("Dice JSON keys:", list(d.keys()))
                if 'data' in d:
                    print("Dice jobs count:", len(d['data']))
                    if d['data']:
                        print("Sample Dice job:", d['data'][0].get('title'), "|", d['data'][0].get('companyName'))
        except Exception as e:
            print(f"Dice {ep[:50]} err: {e}")
except Exception as e:
    print("Dice overall err:", e)

# 2. Careerjet check
print("\n=== CAREERJET CHECK ===")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    s = c_requests.Session()
    # First get homepage
    s.get("https://www.careerjet.co.in/", headers=headers, impersonate="chrome120")
    r = s.get("https://www.careerjet.co.in/search/jobs?s=python&l=bangalore", headers=headers, impersonate="chrome120")
    print("Careerjet session status:", r.status_code, "len:", len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('article.job') or soup.select('article') or soup.select('.job')
    print("Careerjet cards found:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('header h2 a') or c.select_one('h2 a') or c.select_one('h2')
        comp = c.select_one('.company_compact') or c.select_one('.company')
        print("Careerjet sample:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
except Exception as e:
    print("Careerjet err:", e)
