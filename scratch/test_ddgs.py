import re, time
from ddgs import DDGS

queries = [
    'site:wellfound.com/jobs "Lead Generation" India',
    'site:wellfound.com/jobs "Lead Generation Executive"',
    'site:wellfound.com/jobs "Lead Generation" Chennai',
    'site:wellfound.com/jobs "Business Development" "Tamil Nadu"',
    'site:wellfound.com/jobs "Business Development Executive" India',
    'site:wellfound.com/jobs "Sales Development Representative" India',
    'site:wellfound.com/jobs "Lead Generation"',
    'site:wellfound.com/jobs "Inside Sales" India'
]

discovered = set()
with DDGS() as d:
    for q in queries:
        try:
            res = d.text(q, max_results=20)
            for r in res:
                h = r.get("href", "")
                m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', h)
                if m:
                    discovered.add(m.group(1))
            print(f"Query: {q} -> Found total: {len(discovered)}")
        except Exception as e:
            print(f"Error on {q}: {e}")
        time.sleep(1)

print(f"\nTotal discovered: {len(discovered)}")
