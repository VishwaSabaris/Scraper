import pandas as pd

df = pd.read_csv('all_scraped_jobs_26_portals.csv')
cb = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)]

print(f"Total CareerBuilder rows: {len(cb)}")
for i, r in cb.iterrows():
    print(f"[{i}] Role: {r.get('Job Role')} | Comp: {r.get('Company Name')} | Details: {str(r.get('Company / Job Details'))[:50]}... | URL: {r.get('Apply Link')}")
