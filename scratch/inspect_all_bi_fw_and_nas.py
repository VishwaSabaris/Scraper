import pandas as pd

df = pd.read_csv("all_scraped_jobs_26_portals.csv")
print(f"Total rows in all_scraped_jobs_26_portals.csv: {len(df)}")
print("Columns:", list(df.columns))

print("\n--- BUILTIN ROWS ---")
bi = df[df['Source'].str.contains('builtin', case=False, na=False) | df['Apply Link'].str.contains('builtin.com', case=False, na=False)]
print(f"Total BuiltIn rows: {len(bi)}")
for idx, r in bi.iterrows():
    print(f"[{idx}] Role: {r['Job Role']} | Comp: {r['Company Name']} | Loc: {r['Location']} | Date: {r['Date Posted']} | Web: {r.get('Company Link')} | URL: {r['Apply Link']}")

print("\n--- FRESHERSWORLD ROWS ---")
fw = df[df['Source'].str.contains('freshersworld', case=False, na=False) | df['Apply Link'].str.contains('freshersworld.com', case=False, na=False)]
print(f"Total Freshersworld rows: {len(fw)}")
for idx, r in fw.iterrows():
    print(f"[{idx}] Role: {r['Job Role']} | Comp: {r['Company Name']} | Loc: {r['Location']} | Date: {r['Date Posted']} | Web: {r.get('Company Link')} | URL: {r['Apply Link']}")

print("\n--- OVERALL NULL / EMPTY / NA SUMMARY ---")
for col in df.columns:
    na_count = df[col].isna().sum()
    empty_count = (df[col].astype(str).str.strip() == "").sum()
    na_str_count = (df[col].astype(str).str.strip().str.lower() == "n/a").sum()
    print(f"Column '{col}': {na_count} NaN, {empty_count} empty, {na_str_count} 'N/A'")
