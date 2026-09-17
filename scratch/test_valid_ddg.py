from ddgs import DDGS

queries = [
    'site:careerbuilder.com "Sales Development Representative"',
    'site:careerbuilder.com "SDR"',
    'site:careerbuilder.com "Software Engineer"',
    'site:careerbuilder.com "Data Engineer"',
    'careerbuilder "Sales Development Representative"'
]

with DDGS() as ddgs:
    for q in queries:
        try:
            print(f"\n--- Testing Query: {q} ---")
            results = list(ddgs.text(q, max_results=5))
            print(f"Got {len(results)} results:")
            for r in results[:3]:
                print("Title:", r.get('title'))
                print("Href :", r.get('href'))
                print("Body :", r.get('body'))
        except Exception as e:
            print("Error:", e)
