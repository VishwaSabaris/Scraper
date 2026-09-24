import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open("scratch/verified_wellfound_jobs.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

print(f"Total jobs in verified_wellfound_jobs.json: {len(jobs)}")

for i, j in enumerate(jobs):
    role = j.get("Job Role", "")
    comp = j.get("Company Name", "")
    loc = j.get("Location", "")
    link = j.get("Apply Link", "")
    print(f"{i+1:2d}. {role:55s} | {comp:25s} | {loc[:35]}")
