import sys
from ddgs import DDGS

url = "https://www.careerbuilder.com/job-details/senior-data-engineer-london-england-london-ky--82dfb563-6832-4b57-bda6-2e30aa4a818d"
slug = "senior data engineer london england london ky"
q = f'"{slug}" site:careerbuilder.com'

print(f"Querying: {q}", flush=True)
try:
    with DDGS() as ddgs:
        results = list(ddgs.text(q, max_results=5))
        print(f"Results count: {len(results)}", flush=True)
        for r in results:
            print("Title:", r.get("title"), flush=True)
            print("Href:", r.get("href"), flush=True)
            print("Body:", r.get("body"), flush=True)
except Exception as e:
    print("Error:", e, flush=True)
