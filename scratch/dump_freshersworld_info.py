import pandas as pd
import re

df = pd.read_csv("all_scraped_jobs_26_portals.csv")
fw = df[df['Source'].str.contains('freshersworld', case=False, na=False) | df['Apply Link'].str.contains('freshersworld.com', case=False, na=False)]

print(f"Total Freshersworld rows in all_scraped_jobs: {len(fw)}")
for idx, r in fw.iterrows():
    print("="*60)
    print(f"Index: {idx}")
    print(f"  Role   : {r['Job Role']}")
    print(f"  Link   : {r['Apply Link']}")
    print(f"  Details: {str(r.get('Company / Job Details'))[:120]}")
