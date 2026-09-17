import pandas as pd

df = pd.read_csv("all_scraped_jobs_26_portals.csv")

for idx, r in df.iterrows():
    c = str(r['Company Name']).strip()
    if c in ["", "nan", "NaN", "None", "null", "N/A"]:
        print(f"[{idx}] Source: {r['Source']} | Role: {r['Job Role']} | Link: {r['Apply Link']}")
