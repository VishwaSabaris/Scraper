import requests
import json
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 1. Instahyre API check
print("--- 1. Testing Instahyre API ---")
try:
    url = "https://www.instahyre.com/api/v1/job_search?skills=Python&job_type=0"
    r = requests.get(url, headers=headers, timeout=10)
    print("Instahyre API status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Instahyre API keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        if 'objects' in data:
            print("Instahyre objects count:", len(data['objects']))
            if data['objects']:
                obj = data['objects'][0]
                print("Instahyre sample:", obj.get('title'), "|", obj.get('employer', {}).get('company_name'), "|", obj.get('locations'))
except Exception as e:
    print("Instahyre err:", e)

# 2. Dice API / JSON check
print("\n--- 2. Testing Dice search endpoint ---")
try:
    dice_url = "https://application.dice.com/api/jobsearch/paged?q=Python&location=Remote&pageSize=20&page=1"
    r = requests.get(dice_url, headers=headers, timeout=10)
    print("Dice API status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Dice API keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        if 'data' in data:
            print("Dice jobs count:", len(data['data']))
            if data['data']:
                j = data['data'][0]
                print("Sample Dice job:", j.get('title'), "|", j.get('companyName'), "|", j.get('jobLocation', {}).get('displayName'))
except Exception as e:
    print("Dice err:", e)

# 3. Foundit middleware search check
print("\n--- 3. Testing Foundit middleware ---")
try:
    foundit_url = "https://www.foundit.in/middleware/jobsearch?query=Python&locations=Bangalore&limit=20&start=0"
    r = requests.get(foundit_url, headers=headers, timeout=10)
    print("Foundit API status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Foundit API keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        if 'jobSearchResults' in data:
            jobs = data['jobSearchResults'].get('data', [])
            print("Foundit jobs count:", len(jobs))
            if jobs:
                j = jobs[0]
                print("Sample Foundit job:", j.get('title'), "|", j.get('company', {}).get('name'), "|", j.get('locations'))
except Exception as e:
    print("Foundit err:", e)

# 4. Careerjet scraping check
print("\n--- 4. Careerjet HTML check ---")
try:
    url = "https://www.careerjet.co.in/search/jobs?s=Python&l=Bangalore"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('article.job') or soup.select('article') or soup.select('.job')
    print("Careerjet articles count:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('h2 a') or c.select_one('a.title') or c.select_one('h2')
        comp = c.select_one('.company_compact') or c.select_one('.company')
        loc = c.select_one('.location_compact') or c.select_one('.locations')
        print("Sample Careerjet:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '', "|", loc.text.strip() if loc else '')
except Exception as e:
    print("Careerjet err:", e)
