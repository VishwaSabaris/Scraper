import pandas as pd

df = pd.read_csv("all_scraped_jobs_26_portals.csv")

for idx, r in df.iterrows():
    null_cols = [col for col in df.columns if pd.isna(r[col]) or str(r[col]).strip() in ["", "nan", "NaN", "None", "null"]]
    if null_cols:
        print(f"[{idx}] Source: {r['Source']} | Nulls in {null_cols} | Role: {r['Job Role']} | Comp: {r.get('Company Name')} | Link: {r.get('Apply Link')}")
