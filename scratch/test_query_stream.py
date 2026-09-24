import re, time
from ddgs import DDGS

effective_role = "Lead Generation Executive"
effective_loc = "Chennai"
loc_terms = ["Chennai", "Tamil Nadu", "India"]

queries = [
    f'site:wellfound.com/jobs "lead generation" {effective_loc}',
    f'site:wellfound.com/jobs "lead generation executive"',
    f'site:wellfound.com/jobs "lead generation" "Tamil Nadu"',
    f'site:wellfound.com/jobs "lead generation" India',
    f'site:wellfound.com/jobs "business development" {effective_loc}',
    f'site:wellfound.com/jobs "business development executive" India',
    f'site:wellfound.com/jobs "sales development" India'
]

discovered = set()
with DDGS() as d:
    for q in queries:
        try:
            res = d.text(q, max_results=15)
            cnt = 0
            for r in res:
                h = r.get('href', '')
                m = re.search(r'(https://wellfound\.com/jobs/\d+-[a-z0-9-]+)', h)
                if m and m.group(1) not in discovered:
                    discovered.add(m.group(1))
                    cnt += 1
            print(f"[{cnt} new] from '{q}' -> Total so far: {len(discovered)}")
        except Exception as e:
            print(f"Error on '{q}': {e}")
        time.sleep(1.2)

print(f"\nTotal verified URLs discovered: {len(discovered)}")
