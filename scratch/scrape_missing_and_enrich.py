import asyncio
import os
import sys
import pandas as pd
import csv

# Set stdout encoding to UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linkedin_scraper import scrape_linkedin_jobs
from indeed_scraper import scrape_indeed_jobs
from careerbuilder_scraper import scrape_careerbuilder_jobs
from resolve_company_websites import process_job_csv

async def main():
    role = "Sales Development Representative"
    location = "Bangalore"
    
    print("=" * 80, flush=True)
    print("   SCRAPING MISSING PORTALS: LINKEDIN, INDEED, CAREERBUILDER", flush=True)
    print("=" * 80, flush=True)
    
    # 1. LinkedIn
    print("\n>>> [1/3] Scraping LinkedIn...", flush=True)
    try:
        linkedin_jobs = await scrape_linkedin_jobs(role, location, headless=True)
        print(f"[+] LinkedIn scraped: {len(linkedin_jobs)} jobs", flush=True)
    except Exception as e:
        print(f"[!] LinkedIn error: {e}", flush=True)
        linkedin_jobs = []
        
    # 2. Indeed
    print("\n>>> [2/3] Scraping Indeed...", flush=True)
    try:
        indeed_jobs = await scrape_indeed_jobs(role, location, max_pages=3, headless=True)
        print(f"[+] Indeed scraped: {len(indeed_jobs)} jobs", flush=True)
    except Exception as e:
        print(f"[!] Indeed error: {e}", flush=True)
        indeed_jobs = []
        
    # 3. CareerBuilder
    print("\n>>> [3/3] Scraping CareerBuilder...", flush=True)
    try:
        cb_jobs = await scrape_careerbuilder_jobs(role, location, headless=True)
        print(f"[+] CareerBuilder scraped: {len(cb_jobs)} jobs", flush=True)
    except Exception as e:
        print(f"[!] CareerBuilder error: {e}", flush=True)
        cb_jobs = []
        
    new_jobs = linkedin_jobs + indeed_jobs + cb_jobs
    print(f"\n[+] Total newly scraped listings from missing portals: {len(new_jobs)}", flush=True)
    
    target_csv = "all_sdr_26_jobs.csv"
    if os.path.exists(target_csv):
        existing_df = pd.read_csv(target_csv)
        existing_records = existing_df.to_dict(orient="records")
    else:
        existing_records = []
        
    print(f"[*] Existing listings in '{target_csv}': {len(existing_records)}", flush=True)
    
    # Deduplicate and merge
    combined = existing_records + new_jobs
    seen_keys = set()
    unique_merged = []
    
    for job in combined:
        apply_link = str(job.get("Apply Link", "")).strip()
        role_clean = str(job.get("Job Role", "")).strip().lower()
        comp_clean = str(job.get("Company Name", "")).strip().lower()
        
        dedup_key = apply_link if (apply_link and apply_link != "N/A" and apply_link != "nan") else f"{role_clean}|{comp_clean}"
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            unique_merged.append(job)
            
    print(f"[+] Total merged and deduplicated records: {len(unique_merged)} (Added {len(unique_merged) - len(existing_records)} new records)", flush=True)
    
    keys = ["Job Role", "Company Name", "Location", "Date Posted", "Apply Link", "Company Link", "No. of Applicants", "Company / Job Details", "Source"]
    with open(target_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for item in unique_merged:
            row = {k: item.get(k, "N/A") for k in keys}
            writer.writerow(row)
            
    print(f"[+] Saved updated dataset to '{target_csv}'.", flush=True)
    
    # Now run the Enterprise Company Website Resolver
    print("\n" + "=" * 80, flush=True)
    print("   RESOLVING COMPANY WEBSITES FOR ALL SCRAPED JOB DATA", flush=True)
    print("=" * 80, flush=True)
    process_job_csv(target_csv)
    
    # Also resolve for all_jobs_vvs.csv and all_jobs_maximum_extracted.csv if they exist
    for other_csv in ["all_jobs_vvs.csv", "all_jobs_maximum_extracted.csv"]:
        if os.path.exists(other_csv):
            process_job_csv(other_csv)

if __name__ == "__main__":
    asyncio.run(main())
