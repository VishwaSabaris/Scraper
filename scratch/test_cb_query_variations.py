from ddgs import DDGS

test_urls = [
    ("https://careerbuilder.com/job-details/sales-development-representative-enterprise-clearwater-fl--51afe872-3724-4890-bbee-2980306219f6", "Sales Development Representative Enterprise Clearwater FL"),
    ("https://careerbuilder.com/job-details/sales-development-representative-vancouver-wa--653e6902-124c-49ad-ac74-43361dc8eef7", "Sales Development Representative Vancouver WA"),
    ("https://careerbuilder.com/job-details/sales-development-representative-sdr-san-francisco-ca--3b946740-c222-49a9-97d6-8c626c02a145", "Sales Development Representative SDR San Francisco CA"),
    ("https://careerbuilder.com/job-details/sales-development-representative-fall-26-spring-27-graduates-chicago-il--3d3fcf02-874f-46fd-b837-4d24b3b261f7", "Sales Development Representative Chicago IL"),
    ("https://careerbuilder.com/job-details/business-development-representative-inside-sales-san-antonio-tx--2f1208e0-6b6b-48bc-9d08-49a30d267654", "Business Development Representative San Antonio TX")
]

with DDGS() as ddgs:
    for url, desc in test_urls:
        slug = url.split('/')[-1]
        print(f"\n==========================================", flush=True)
        print(f"URL: {url}", flush=True)
        
        queries = [
            f'site:careerbuilder.com/job-details "{slug}"',
            f'site:careerbuilder.com {desc}',
            f'"{slug}"',
            f'careerbuilder {desc}'
        ]
        
        found = False
        for q in queries:
            try:
                res = list(ddgs.text(q, max_results=3))
                if res:
                    print(f"Query [{q}] -> Got {len(res)} results:", flush=True)
                    for r in res:
                        print("  Title:", r.get('title'), flush=True)
                        print("  Body :", r.get('body'), flush=True)
                    found = True
                    break
            except Exception as e:
                pass
        if not found:
            print("No results found for any query.", flush=True)
