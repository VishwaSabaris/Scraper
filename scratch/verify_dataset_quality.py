import csv
from collections import Counter
import sys
import os

def analyze_dataset(filename="final_verified_job_dataset.csv"):
    if not os.path.exists(filename):
        print(f"[!] File '{filename}' not found.")
        return
        
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    total_records = len(rows)
    print(f"\n{'='*30} DATASET QUALITY & INTEGRITY REPORT {'='*30}")
    print(f"Target CSV File : {filename}")
    print(f"Total Records   : {total_records}")
    
    if total_records == 0:
        print("[!] No records to analyze.")
        return
        
    # 1. Uniqueness check
    links = [r['Apply Link'] for r in rows if r.get('Apply Link')]
    unique_links = set(links)
    dup_count = total_records - len(unique_links)
    print(f"Unique Listings : {len(unique_links)} ({100 * len(unique_links) / total_records:.1f}% unique, {dup_count} duplicates)")
    
    # 2. Breakdown by Portal / Source
    sources = Counter(r['Source'] for r in rows)
    print(f"\n--- 1. Breakdown by Portal ---")
    for src, cnt in sources.most_common():
        pct = (cnt / total_records) * 100
        print(f"  * {src:<16}: {cnt:>4} jobs ({pct:>5.1f}%)")
        
    # 3. Field Completeness Check
    print(f"\n--- 2. Field Completeness & Quality ---")
    headers = reader.fieldnames or []
    for h in headers:
        valid_cnt = sum(1 for r in rows if r.get(h) and r.get(h).strip() not in ["", "N/A", "None", "null"])
        pct = (valid_cnt / total_records) * 100
        status = "EXCELLENT" if pct >= 90 else ("GOOD" if pct >= 50 else "OPTIONAL")
        print(f"  * {h:<22}: {valid_cnt:>4}/{total_records} populated ({pct:>5.1f}%) [{status}]")
        
    # 4. Top Companies
    print(f"\n--- 3. Top Companies Extracted ---")
    companies = Counter(r['Company Name'] for r in rows if r.get('Company Name') and r.get('Company Name') not in ["N/A", "Unknown", ""])
    for comp, cnt in companies.most_common(12):
        print(f"  - {comp:<40}: {cnt} listings")
        
    # 5. Top Locations
    print(f"\n--- 4. Location Distribution ---")
    locations = Counter(r['Location'] for r in rows if r.get('Location'))
    for loc, cnt in locations.most_common(8):
        print(f"  - {loc:<40}: {cnt} listings")
        
    # 6. Sample Verified Job from Each Portal
    print(f"\n--- 5. Verified Sample Listing per Portal ---")
    seen_sources = set()
    for r in rows:
        src = r['Source']
        if src not in seen_sources:
            seen_sources.add(src)
            title = r['Job Role'].encode('ascii', 'ignore').decode('ascii')
            comp = r['Company Name'].encode('ascii', 'ignore').decode('ascii')
            loc = r['Location'].encode('ascii', 'ignore').decode('ascii')
            link = r['Apply Link'].encode('ascii', 'ignore').decode('ascii')
            details = r['Company / Job Details'].encode('ascii', 'ignore').decode('ascii')[:80]
            print(f"\n[{src}]")
            print(f"  * Title   : {title}")
            print(f"  * Company : {comp}")
            print(f"  * Location: {loc}")
            print(f"  * Details : {details}...")
            print(f"  * URL     : {link}")
            
    print(f"\n{'='*75}\n")

if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "final_verified_job_dataset.csv"
    analyze_dataset(fn)
