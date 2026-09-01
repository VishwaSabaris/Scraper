import csv
import os
from scrape_filtered_jobs import (
    parse_date_posted_to_days,
    parse_applicants_count,
    is_remote_job,
    is_usa_job,
    save_list_to_csv
)

def main():
    raw_file = "combined_jobs_raw.csv"
    filtered_file = "combined_jobs_filtered.csv"
    
    if not os.path.exists(raw_file):
        print(f"[!] {raw_file} does not exist.")
        return
        
    print(f"[*] Re-applying filters from {raw_file} to {filtered_file}...")
    
    all_results = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_results.append(row)
            
    filtered_results = []
    for job in all_results:
        # 1. Location & Remote Filter
        if not is_usa_job(job):
            continue
        if not is_remote_job(job):
            continue
            
        # 2. Date Filter: under 30 days
        date_posted_str = job.get("Date Posted", "N/A")
        days = parse_date_posted_to_days(date_posted_str)
        if days is not None and days >= 30:
            continue
            
        # 3. Applicant Filter: under 10 applicants
        applicants_str = job.get("No. of Applicants", "N/A")
        applicants = parse_applicants_count(applicants_str)
        if applicants is not None and applicants >= 10:
            continue
            
        filtered_results.append(job)
        
    print(f"[+] Total filtered listings matching criteria: {len(filtered_results)}")
    save_list_to_csv(filtered_results, filtered_file)

if __name__ == "__main__":
    main()
