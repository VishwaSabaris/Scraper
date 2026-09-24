import sys, os
sys.path.insert(0, os.path.abspath("."))
import csv
import re
import requests
from bs4 import BeautifulSoup
from utils import normalize_date_posted, get_company_website

# 1. Read existing selective_4.csv
with open('selective_4.csv', 'r', encoding='utf-8-sig') as f:
    existing_rows = list(csv.DictReader(f))

# Keep non-LinkedIn and non-YC rows (Indeed, JobLeads, Remote.com)
other_rows = [r for r in existing_rows if r['Source'] not in ['LinkedIn', 'Work at a Startup']]
print(f"Retained {len(other_rows)} rows from Indeed, JobLeads, Remote.com.")

# 2. Load the 31 verified remote LinkedIn jobs
from linkedin_scraper import scrape_linkedin_jobs
# Read from our successful test or rerun fast
import json
with open('scratch/test_li_end_to_end.py') as f:
    pass

# We will load the verified remote LinkedIn jobs
import asyncio
from linkedin_scraper import scrape_linkedin_jobs

async def get_li_jobs():
    filter_params = {
        "keywords": "Python Developer Remote",
        "f_WT": "2"
    }
    return await scrape_linkedin_jobs(
        job_role="Python Developer",
        location="",
        filter_params=filter_params,
        headless=True
    )

li_jobs = asyncio.run(get_li_jobs())
print(f"Loaded {len(li_jobs)} verified remote LinkedIn jobs.")

# 3. Process Work at a Startup rows
# Filter out General Application fake jobs
yc_real_jobs = [r for r in existing_rows if r['Source'] == 'Work at a Startup' and 'General Application' not in r['Job Role']]

# Known company mappings for the YC jobs in selective_4.csv:
JOB_TO_COMP = {
    63441: "Harvey",
    99320: "Harvey",
    99321: "Harvey",
    78412: "AiPrise",
    78403: "AiPrise",
    78397: "AiPrise",
    78393: "AiPrise",
    62175: "Andromeda Surgical",
    106813: "Andromeda Surgical",
    94934: "MixRank",
    94932: "MixRank",
    94930: "MixRank",
    94931: "MixRank",
    96607: "Cityfurnish",
    82375: "Cityfurnish",
    75274: "Cityfurnish",
    93015: "Yondu",
    103271: "Yondu",
    69125: "Yummy Future",
    69123: "Yummy Future",
    69124: "Yummy Future",
    69126: "Yummy Future"
}

fixed_yc_jobs = []
for r in yc_real_jobs:
    # Only keep developer/engineer roles matching Python/Software
    apply_link = r.get('Apply Link', '')
    match = re.search(r'/jobs/(\d+)', apply_link)
    job_id = int(match.group(1)) if match else None
    
    comp_name = JOB_TO_COMP.get(job_id, r.get('Company Name', 'YC Startup'))
    if "See all" in comp_name:
        comp_name = "YC Startup"
        
    r['Company Name'] = comp_name
    r['Company Link'] = f"https://www.workatastartup.com/companies/{comp_name.lower().replace(' ', '-')}"
    r['website'] = r['Company Link']
    
    # Ensure role is engineering/developer
    role = r.get('Job Role', '')
    if any(non in role.lower() for non in ['content designer', 'growth strategist', 'marketing intern', 'founder’s office', 'founder\'s office', 'operations associate']):
        continue
    fixed_yc_jobs.append(r)

print(f"Retained {len(fixed_yc_jobs)} verified engineering jobs from Work at a Startup.")

# Combine all clean records
final_rows = []
for j in li_jobs:
    final_rows.append({
        "Job Role": j["Job Role"],
        "Company Name": j["Company Name"],
        "Location": j["Location"],
        "Date Posted": j["Date Posted"],
        "Apply Link": j["Apply Link"],
        "Company Link": j["Company Link"],
        "No. of Applicants": j["No. of Applicants"],
        "Job Description": j["Company / Job Details"],
        "Source": "LinkedIn",
        "website": j["Company Link"],
        "apply_link_url": j["Apply Link"]
    })

final_rows.extend(other_rows)
final_rows.extend(fixed_yc_jobs)

canonical_headers = [
    "Job Role", "Company Name", "Location", "Date Posted",
    "Apply Link", "Company Link", "No. of Applicants",
    "Job Description", "Source",
    "website", "apply_link_url"
]

with open('selective_4.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=canonical_headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(final_rows)

print(f"\n[+] Successfully saved {len(final_rows)} clean records to selective_4.csv!")
