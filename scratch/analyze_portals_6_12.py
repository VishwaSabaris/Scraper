import requests
import json
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 6. Adzuna
print("=== 6. Adzuna ===")
try:
    s = requests.Session()
    s.headers.update(headers)
    # First get homepage or search
    r = s.get('https://www.adzuna.in/search?q=python&w=bangalore', timeout=10)
    print("Adzuna status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('article[data-aid]') or soup.select('.a-job-search-result') or soup.select('article')
    print("Adzuna cards count:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('h2 a') or c.select_one('a.text-base') or c.select_one('h2')
        comp = c.select_one('.ui-company') or c.select_one('[data-qa="company-name"]') or c.select_one('.text-neutral-500')
        loc = c.select_one('.ui-location') or c.select_one('.location')
        sal = c.select_one('.ui-salary') or c.select_one('.salary')
        print("Sample Adzuna:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp', "|", loc.text.strip() if loc else 'No loc')
except Exception as e:
    print("Adzuna error:", e)

# 7. BuiltIn
print("\n=== 7. BuiltIn ===")
try:
    r = requests.get('https://builtin.com/jobs?search=python', headers=headers, timeout=10)
    print("BuiltIn status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Check Next data or JSON-LD or job cards
    cards = soup.select('[data-id="job-card"]') or soup.select('.job-item') or soup.select('.job-card') or soup.select('[id^="job-card-"]')
    print("BuiltIn cards count:", len(cards))
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        page_props = data.get('props', {}).get('pageProps', {})
        print("BuiltIn pageProps keys:", list(page_props.keys())[:10])
        # Find jobs in pageProps
        def search_dict(d, query, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    if query in k.lower():
                        print(f"BuiltIn found key at {path}.{k}: type {type(v)} (len {len(v) if hasattr(v, '__len__') else 'N/A'})")
                    search_dict(v, query, f"{path}.{k}")
            elif isinstance(d, list) and d and len(d) > 0 and isinstance(d[0], dict):
                search_dict(d[0], query, f"{path}[0]")
        search_dict(page_props, "job")
except Exception as e:
    print("BuiltIn error:", e)

# 8. Careerjet
print("\n=== 8. Careerjet ===")
try:
    r = requests.get('https://www.careerjet.co.in/search/jobs?s=python&l=bangalore', headers=headers, timeout=10)
    print("Careerjet status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('article.job') or soup.select('.job-list article') or soup.select('.job')
    print("Careerjet cards count:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('header h2 a') or c.select_one('h2 a') or c.select_one('a.title')
        comp = c.select_one('.company_compact') or c.select_one('p.company') or c.select_one('.company')
        loc = c.select_one('ul.location_compact') or c.select_one('.location') or c.select_one('ul.location')
        desc = c.select_one('.desc')
        print("Sample Careerjet:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp', "|", loc.text.strip() if loc else 'No loc')
except Exception as e:
    print("Careerjet error:", e)

# 9. Dice
print("\n=== 9. Dice ===")
try:
    r = requests.get('https://www.dice.com/jobs?q=python&location=Remote', headers=headers, timeout=10)
    print("Dice status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('dhi-search-card') or soup.select('.card-title-link') or soup.select('[data-cy="card-title-link"]') or soup.select('.search-card')
    print("Dice cards count:", len(cards))
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        print("Dice has __NEXT_DATA__")
    else:
        # Check script tags
        scripts = soup.find_all('script')
        for sc in scripts:
            if sc.string and 'jobSearchResult' in sc.string:
                print("Found jobSearchResult in script tag!")
except Exception as e:
    print("Dice error:", e)

# 10. SimplyHired
print("\n=== 10. SimplyHired ===")
try:
    r = requests.get('https://www.simplyhired.co.in/search?q=python&l=bangalore', headers=headers, timeout=10)
    print("SimplyHired status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('[data-testid="searchSerpJob"]') or soup.select('.SerpJob-jobCard') or soup.select('li[data-testid="searchSerpJob"]') or soup.select('article')
    print("SimplyHired cards count:", len(cards))
except Exception as e:
    print("SimplyHired error:", e)

# 11. TimesJobs
print("\n=== 11. TimesJobs ===")
try:
    r = requests.get('https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords=python&txtLocation=bangalore', headers=headers, verify=False, timeout=10)
    print("TimesJobs status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('li.clearfix.job-bx') or soup.select('.job-bx') or soup.select('ul.job-list li') or soup.select('div.job-bx')
    print("TimesJobs cards count:", len(cards))
    if not cards:
        print("TimesJobs title tag:", soup.title.text if soup.title else 'No title')
        print("TimesJobs snippet:", soup.text[:300].strip())
except Exception as e:
    print("TimesJobs error:", e)

# 12. Freshersworld
print("\n=== 12. Freshersworld ===")
try:
    r = requests.get('https://www.freshersworld.com/jobs/jobsearch/python-jobs-in-bangalore', headers=headers, timeout=10)
    print("Freshersworld status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('.job-container') or soup.select('.jobs-today') or soup.select('.col-md-12.job-container') or soup.select('[class*="job-container"]') or soup.select('.job-contents')
    print("Freshersworld cards count:", len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('.job-title') or c.select_one('.latest-jobs-title') or c.select_one('h3') or c.select_one('a')
        comp = c.select_one('.company-name') or c.select_one('.latest-jobs-company')
        loc = c.select_one('.job-location') or c.select_one('.job-desc .bold')
        print("Sample Freshersworld:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp')
except Exception as e:
    print("Freshersworld error:", e)
