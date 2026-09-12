from bs4 import BeautifulSoup

print("=== PARSING TIMESJOBS SAMPLE ===")
with open("./scratch/timesjobs_sample.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
cards = soup.select('li.clearfix.job-bx') or soup.select('.job-bx') or soup.select('ul.job-list li') or soup.select('.clearfix.job-bx') or soup.select('article')
print(f"TimesJobs cards found: {len(cards)}")
if cards:
    c = cards[0]
    title = c.select_one('h2 a') or c.select_one('h2')
    comp = c.select_one('.heading-trun') or c.select_one('h3.joblist-comp-name') or c.select_one('h3')
    loc = c.select_one('.srp-loc') or c.select_one('.top-jd-dtl li span') or c.select_one('ul.top-jd-dtl li')
    exp = c.select_one('.top-jd-dtl li')
    desc = c.select_one('.job-description') or c.select_one('.list-job-dtls')
    print("TimesJobs Sample:", {
        "title": title.text.strip() if title else '',
        "link": title.get('href') if title and title.name == 'a' else (title.find('a').get('href') if title and title.find('a') else ''),
        "company": comp.text.strip() if comp else '',
        "loc": loc.text.strip() if loc else '',
        "exp": exp.text.strip() if exp else '',
        "desc": desc.text.strip()[:100] if desc else ''
    })

print("\n=== PARSING CAREERJET SAMPLE ===")
with open("./scratch/careerjet_sample.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
cards = soup.select('article.job') or soup.select('.job-list article') or soup.select('article') or soup.select('.jobs article')
print(f"Careerjet cards found: {len(cards)}")
if cards:
    c = cards[0]
    title = c.select_one('header h2 a') or c.select_one('h2 a') or c.select_one('h2')
    comp = c.select_one('.company_compact') or c.select_one('p.company') or c.select_one('.company')
    loc = c.select_one('ul.location_compact') or c.select_one('ul.location') or c.select_one('.location')
    desc = c.select_one('.desc') or c.select_one('.job-description')
    print("Careerjet Sample:", {
        "title": title.text.strip() if title else '',
        "link": title.get('href') if title and title.name == 'a' else '',
        "company": comp.text.strip() if comp else '',
        "loc": loc.text.strip() if loc else '',
        "desc": desc.text.strip()[:100] if desc else ''
    })
else:
    print("Careerjet HTML length:", len(html))
    print("Careerjet text snippet:", soup.text[:300].strip())
