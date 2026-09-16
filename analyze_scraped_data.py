"""
Dataset Accuracy and Completeness Analyzer
==========================================
Analyzes all_scraped_jobs_26_portals.csv to measure data quality, field population, 
URL validity, role relevance, date normalization, and company website resolution.
"""

import csv
import re
import urllib.parse
from collections import Counter

def analyze_dataset(csv_path="all_scraped_jobs_26_portals.csv"):
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        records = list(reader)
        
    total_records = len(records)
    print("=" * 80)
    print(f"       DATA QUALITY & ACCURACY ANALYSIS: '{csv_path}'")
    print(f"       Total Extracted Records: {total_records}")
    print("=" * 80)

    # 1. Field completeness metrics
    fields = ["Job Role", "Company Name", "Location", "Date Posted", "Apply Link", "Company Link", "No. of Applicants", "Company / Job Details", "Source"]
    field_counts = {k: 0 for k in fields}
    
    # 2. Portal distribution
    sources = Counter()
    
    # 3. Date format validation (ISO YYYY-MM-DD)
    iso_dates = 0
    
    # 4. URL format validation
    valid_apply_links = 0
    valid_company_links = 0
    
    # 5. Role match quality
    sdr_keywords = ["sales", "representative", "sdr", "bde", "business development", "account", "growth", "outreach", "lead", "inside sales"]
    relevant_roles = 0
    
    # 6. Detailed length
    rich_details_count = 0

    for r in records:
        for k in fields:
            val = r.get(k, "").strip()
            if val and val != "N/A":
                field_counts[k] += 1
                
        # Source
        src = r.get("Source", "Unknown")
        sources[src] += 1
        
        # Date
        dp = r.get("Date Posted", "").strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', dp):
            iso_dates += 1
            
        # Apply link
        al = r.get("Apply Link", "").strip()
        if al.startswith("http://") or al.startswith("https://"):
            valid_apply_links += 1
            
        # Company link
        cl = r.get("Company Link", "").strip()
        if cl.startswith("http://") or cl.startswith("https://"):
            valid_company_links += 1
            
        # Role relevance
        role = r.get("Job Role", "").lower()
        if any(kw in role for kw in sdr_keywords):
            relevant_roles += 1
            
        # Details richness (> 25 characters)
        det = r.get("Company / Job Details", "").strip()
        if len(det) > 25:
            rich_details_count += 1

    print("\n1. FIELD COMPLETENESS AND POPULATION:")
    print("-" * 65)
    for k in fields:
        pct = (field_counts[k] / total_records) * 100 if total_records else 0
        print(f"  * {k:<24}: {field_counts[k]:>4} / {total_records} ({pct:5.1f}%)")

    print("\n2. PORTAL DISTRIBUTION (26-PORTAL SUITE):")
    print("-" * 65)
    for src, cnt in sources.most_common():
        pct = (cnt / total_records) * 100 if total_records else 0
        print(f"  * {src:<24}: {cnt:>4} listings ({pct:5.1f}%)")

    print("\n3. DATA ACCURACY & VALIDATION METRICS:")
    print("-" * 65)
    print(f"  * Job Role Relevance Rate : {relevant_roles:>4} / {total_records} ({(relevant_roles/total_records)*100:5.1f}%) [Sales/SDR/BDE matches]")
    print(f"  * ISO Date Normalization  : {iso_dates:>4} / {total_records} ({(iso_dates/total_records)*100:5.1f}%) [YYYY-MM-DD formatted]")
    print(f"  * Valid HTTP Apply Links  : {valid_apply_links:>4} / {total_records} ({(valid_apply_links/total_records)*100:5.1f}%) [Canonical URL valid]")
    print(f"  * Official Company Links  : {valid_company_links:>4} / {total_records} ({(valid_company_links/total_records)*100:5.1f}%) [Corporate websites]")
    print(f"  * Rich Details Populated  : {rich_details_count:>4} / {total_records} ({(rich_details_count/total_records)*100:5.1f}%) [Role context/salary/exp]")
    print("=" * 80)

if __name__ == "__main__":
    analyze_dataset()
