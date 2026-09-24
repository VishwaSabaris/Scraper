import pandas as pd
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

df = pd.read_csv('selective_2.csv')
print('Total rows:', len(df))
print('Matches for employer.gov in website:', df['website'].astype(str).str.contains('employer.gov').sum())
print('Matches for employer.gov in Company Link:', df['Company Link'].astype(str).str.contains('employer.gov').sum())
print('Matches for goto?url in Apply Link:', df['Apply Link'].astype(str).str.contains(r'goto\?url').sum())
print('Matches for Various Employer in Company Name:', (df['Company Name'].astype(str) == 'Various Employer').sum())

wf = df[df['Source'] == 'Wellfound']
print('\nTotal Wellfound rows:', len(wf))
print('\n--- Wellfound Sample Entries ---')
for i, (_, r) in enumerate(wf.head(8).iterrows()):
    print(f"[{i+1}] {r['Job Role']} at {r['Company Name']}")
    print(f"    Location:    {r['Location']}")
    print(f"    Apply Link:  {r['Apply Link']}")
    print(f"    Company URL: {r['Company Link']}")
    print(f"    Date Posted: {r['Date Posted']}")
