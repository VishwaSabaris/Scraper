from ddgs import DDGS
import json

urls = [
    "https://www.careerbuilder.com/job-details/senior-data-engineer-london-england-london-ky--82dfb563-6832-4b57-bda6-2e30aa4a818d",
    "https://www.careerbuilder.com/job-details/sales-development-representative-vancouver-wa--653e6902-124c-49ad-ac74-43361dc8eef7",
    "https://www.careerbuilder.com/job-details/sales-development-representative-enterprise-clearwater-fl--51afe872-3724-4890-bbee-2980306219f6",
    "https://careerbuilder.com/job-details/sales-development-representative-sdr-san-francisco-ca--3b946740-c222-49a9-97d6-8c626c02a145",
    "https://www.careerbuilder.com/job-details/sales-development-representative-fall-26-spring-27-graduates-chicago-il--3d3fcf02-874f-46fd-b837-4d24b3b261f7"
]

with DDGS() as ddgs:
    for u in urls:
        slug = u.split('/')[-1].split('?')[0]
        # extract job id
        job_id = slug.split('--')[-1] if '--' in slug else slug
        slug_clean = slug.split('--')[0].replace('-', ' ')
        print(f"\n==========================================")
        print(f"Testing URL: {u}")
        print(f"Slug: {slug_clean} | ID: {job_id}")
        
        # Test query 1: exact URL or job ID
        queries = [
            f'"{u}"',
            f'"{job_id}" site:careerbuilder.com',
            f'"{slug_clean}" site:careerbuilder.com',
            f'"{slug_clean}"'
        ]
        for q in queries:
            try:
                res = list(ddgs.text(q, max_results=3))
                if res:
                    print(f"\nQuery [{q}] -> Found {len(res)} results:")
                    for r in res:
                        print("  Title:", r.get('title'))
                        print("  Href :", r.get('href'))
                        print("  Body :", r.get('body'))
                    break
            except Exception as e:
                print(f"Query [{q}] error: {e}")
