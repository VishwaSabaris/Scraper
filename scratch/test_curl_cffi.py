from curl_cffi import requests
from bs4 import BeautifulSoup

# 1. SimplyHired with curl_cffi
print("=== 1. SimplyHired with curl_cffi ===")
try:
    r = requests.get('https://www.simplyhired.co.in/search?q=Python&l=Bengaluru', impersonate='chrome120', timeout=10)
    print('SimplyHired status:', r.status_code, 'len:', len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('[data-testid="searchSerpJob"]') or soup.select('li[data-testid="searchSerpJob"]')
    print('SimplyHired cards count:', len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('[data-testid="searchSerpJobTitle"]') or c.select_one('h2 a') or c.select_one('h2')
        comp = c.select_one('[data-testid="searchSerpJobCompany"]') or c.select_one('[data-testid="companyName"]') or c.select_one('.css-1t925in')
        loc = c.select_one('[data-testid="searchSerpJobLocation"]') or c.select_one('.css-1g8i5q')
        sal = c.select_one('[data-testid="searchSerpJobSalary"]')
        link = c.select_one('a[href*="/job/"]') or c.select_one('a')
        print("Sample SimplyHired:", {
            "title": title.text.strip() if title else '',
            "company": comp.text.strip() if comp else '',
            "loc": loc.text.strip() if loc else '',
            "salary": sal.text.strip() if sal else '',
            "link": ("https://www.simplyhired.co.in" + link.get('href')) if link and link.get('href', '').startswith('/') else (link.get('href') if link else '')
        })
except Exception as e:
    print('SimplyHired err:', e)

# 2. Foundit with curl_cffi
print("\n=== 2. Foundit with curl_cffi ===")
try:
    r = requests.get('https://www.foundit.in/srp/results?query=Python&locations=Bangalore', impersonate='chrome120', timeout=10)
    print('Foundit status:', r.status_code, 'len:', len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('.srpResultCard') or soup.select('[class*="card"]')
    print('Foundit cards count:', len(cards))
    # Check script tags
    scripts = soup.find_all('script')
    for sc in scripts:
        if sc.string and ('jobSearchResults' in sc.string or '__NEXT_DATA__' in sc.string):
            print("Foundit script match found!")
except Exception as e:
    print('Foundit err:', e)

# 3. Careerjet with curl_cffi
print("\n=== 3. Careerjet with curl_cffi ===")
try:
    r = requests.get('https://www.careerjet.co.in/search/jobs?s=Python&l=Bangalore', impersonate='chrome120', timeout=10)
    print('Careerjet status:', r.status_code, 'len:', len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.select('article.job') or soup.select('.job-list article') or soup.select('article')
    print('Careerjet cards count:', len(cards))
    if cards:
        c = cards[0]
        title = c.select_one('header h2 a') or c.select_one('h2 a') or c.select_one('h2')
        comp = c.select_one('.company_compact') or c.select_one('.company') or c.select_one('p.company')
        loc = c.select_one('.location_compact') or c.select_one('.locations') or c.select_one('ul.location')
        sal = c.select_one('.salary') or c.select_one('ul.salary')
        desc = c.select_one('.desc')
        link = title.get('href') if title and title.name == 'a' else ''
        print("Sample Careerjet:", {
            "title": title.text.strip() if title else '',
            "company": comp.text.strip() if comp else '',
            "loc": loc.text.strip() if loc else '',
            "salary": sal.text.strip() if sal else '',
            "link": ("https://www.careerjet.co.in" + link) if link.startswith('/') else link,
            "desc": desc.text.strip()[:80] if desc else ''
        })
except Exception as e:
    print('Careerjet err:', e)
