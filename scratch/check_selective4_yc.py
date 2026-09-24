import csv

with open('selective_4.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

yc_rows = [r for r in rows if r['Source'] == 'Work at a Startup']
print(f"Total YC rows: {len(yc_rows)}")

gen_app = [r for r in yc_rows if 'General Application' in r['Job Role']]
print(f"General Application rows: {len(gen_app)}")

real_jobs = [r for r in yc_rows if 'General Application' not in r['Job Role']]
print(f"Real job rows: {len(real_jobs)}")
for r in real_jobs:
    print(f"Role: {r['Job Role']:<40} | Comp: {r['Company Name']:<20} | Apply: {r['Apply Link']}")
