from bs4 import BeautifulSoup
import json
import re

# 1. Parse Apna
print("=== PARSING APNA SAMPLE ===")
with open("./scratch/apna_sample.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
next_data = soup.find("script", id="__NEXT_DATA__")
if next_data:
    data = json.loads(next_data.string)
    # Search for job items
    print("Next data keys:", list(data.keys()))
    props = data.get("props", {})
    pageProps = props.get("pageProps", {})
    
    # Check dehydratedState
    dehydrated = pageProps.get("dehydratedState", {})
    queries = dehydrated.get("queries", [])
    for q in queries:
        st = q.get("state", {}).get("data", {})
        if isinstance(st, dict):
            # Check for results list
            for k, v in st.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    print(f"Found list in Apna state under key '{k}' with {len(v)} items!")
                    sample = v[0]
                    print("Sample Apna Job:", {
                        "title": sample.get("title") or sample.get("job_title"),
                        "company": sample.get("company_name") or sample.get("company", {}).get("name"),
                        "location": sample.get("location") or sample.get("city"),
                        "salary": sample.get("salary") or sample.get("salary_range") or sample.get("min_salary"),
                        "id": sample.get("id") or sample.get("job_id"),
                        "url": sample.get("url") or sample.get("job_url") or sample.get("share_url")
                    })
                    print("Sample keys:", list(sample.keys())[:15])

# Also check HTML card selectors on Apna
cards = soup.select('[data-testid="job-card"]') or soup.select('[class*="JobCard"]') or soup.select('a[href*="/jobs/"]')
print(f"Apna HTML card links found: {len(cards)}")
for c in cards[:3]:
    print("Apna card href:", c.get("href"))

# 2. Parse Shine
print("\n=== PARSING SHINE SAMPLE ===")
with open("./scratch/shine_sample.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
# Check Shine HTML cards
shine_cards = soup.select('.jobCard') or soup.select('[class*="jobCard"]') or soup.select('[itemprop="itemListElement"]') or soup.select('div[data-job-id]')
print(f"Shine HTML cards found: {len(shine_cards)}")
if shine_cards:
    c = shine_cards[0]
    title = c.select_one('h2 a') or c.select_one('a[href*="/jobs/"]') or c.select_one('h2')
    comp = c.select_one('.jobCard_jobCard_cName__') or c.select_one('[class*="cName"]') or c.select_one('.company-name')
    loc = c.select_one('.jobCard_jobCard_lists__') or c.select_one('[class*="loc"]') or c.select_one('[class*="lists"]')
    exp = c.select_one('[class*="exp"]')
    print("Sample Shine:", title.text.strip() if title else 'No title', "|", comp.text.strip() if comp else 'No comp', "|", loc.text.strip() if loc else 'No loc')
    print("Shine card classes:", c.get("class"))
