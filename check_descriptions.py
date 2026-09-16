import csv
from collections import defaultdict

with open('all_scraped_jobs_26_portals.csv', mode='r', encoding='utf-8-sig') as f:
    records = list(csv.DictReader(f))

by_src = defaultdict(lambda: {'total': 0, 'missing_or_short': 0, 'samples': []})
for r in records:
    src = r.get('Source', 'Unknown')
    det = r.get('Company / Job Details', '').strip()
    by_src[src]['total'] += 1
    if not det or det == 'N/A' or len(det) < 60:
        by_src[src]['missing_or_short'] += 1
        if len(by_src[src]['samples']) < 2:
            by_src[src]['samples'].append((r.get('Job Role'), r.get('Apply Link'), det))

print('Total records:', len(records))
for src, data in by_src.items():
    print(f"{src:<16}: Total={data['total']:>3}, Missing/Short={data['missing_or_short']:>3}")
    for smp in data['samples']:
        print(f"   Sample: {smp[0]} | Desc: {smp[2][:90]}")
