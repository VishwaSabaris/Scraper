import json
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('scratch/verified_wellfound_jobs.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

for i, j in enumerate(jobs):
    print(f"{i+1}. {j['Job Role']} | {j['Company Name']} | {j['Location']}")
