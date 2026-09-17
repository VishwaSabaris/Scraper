import pandas as pd

df = pd.read_csv("all_scraped_jobs_26_portals.csv")
bi = df[df['Source'].str.contains('builtin', case=False, na=False) | df['Apply Link'].str.contains('builtin.com', case=False, na=False)]

print(f"Total BuiltIn rows: {len(bi)}")
for idx, r in bi.iterrows():
    print(f"[{idx}] Role: {r['Job Role']} | Link: {r['Apply Link']} | Current Details: {str(r.get('Company / Job Details'))[:100]}")
