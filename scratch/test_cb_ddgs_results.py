from ddgs import DDGS

q = 'site:careerbuilder.com/job-details "Sales Development Representative"'
print(f"Query: {q}")

with DDGS() as ddgs:
    results = list(ddgs.text(q, max_results=15))
    print(f"Total results: {len(results)}\n")
    for i, r in enumerate(results):
        print(f"[{i+1}] Title: {r.get('title')}")
        print(f"    Href : {r.get('href')}")
        print(f"    Body : {r.get('body')}\n")
