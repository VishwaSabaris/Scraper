import pandas as pd

df = pd.read_csv('all_scraped_jobs_26_portals.csv')
cb = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)]

for idx, row in cb.iloc[:20].iterrows():
    print("="*60)
    print(f"Index: {idx}")
    print(f"Current Role   : {row['Job Role']}")
    print(f"Current Comp   : {row['Company Name']}")
    print(f"Apply Link     : {row['Apply Link']}")
    print(f"Current Details: {row['Company / Job Details']}")
