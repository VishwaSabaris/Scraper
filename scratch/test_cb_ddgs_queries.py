from ddgs import DDGS

queries = [
    'site:careerbuilder.com/job-details Sales Development Representative',
    'site:careerbuilder.com/job "Sales Development Representative"',
    'site:careerbuilder.com/jobs- "Sales Development Representative"',
    'site:careerbuilder.com "Sales Development Representative" jobs'
]

with DDGS() as ddgs:
    for q in queries:
        print("="*60)
        print("Query:", q)
        try:
            res = list(ddgs.text(q, max_results=5))
            print(f"Count: {len(res)}")
            for r in res:
                print("  ", r['title'][:50], "->", r['href'])
        except Exception as e:
            print("Error:", e)
