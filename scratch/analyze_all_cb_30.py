import pandas as pd
import re

df = pd.read_csv('all_scraped_jobs_26_portals.csv')
cb = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)].copy()

print(f"Total CB rows: {len(cb)}")
for i, (idx, row) in enumerate(cb.iterrows()):
    role = row['Job Role']
    comp = row['Company Name']
    url = row['Apply Link']
    det = str(row['Company / Job Details'])
    
    # Extract slug
    slug = url.split('/')[-1].split('?')[0]
    slug_parts = slug.split('--')[0] if '--' in slug else slug
    
    print(f"[{i+1}] Index {idx}")
    print(f"    Role: {role}")
    print(f"    Comp: {comp}")
    print(f"    Slug: {slug_parts}")
    print(f"    URL : {url}")
    print(f"    Det : {det[:120]}")
