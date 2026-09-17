import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

files_to_check = [
    "all_scraped_jobs_26_portals.csv",
    "all_scraped_jobs_26_portals_enriched.csv",
    "builtin_jobs.csv",
    "freshersworld_jobs.csv",
    "extracted_companies_26_portals.csv",
    "companies_with_websites_26_portals.csv"
]

print("=" * 80)
print("COMPREHENSIVE DATASET INTEGRITY & CLEANLINESS AUDIT")
print("=" * 80)

for filename in files_to_check:
    if not os.path.exists(filename):
        print(f"\n[-] {filename}: FILE NOT FOUND")
        continue
        
    with open(filename, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        
    print(f"\n[+] Auditing: {filename} (Total Rows: {len(rows)})")
    print(f"    Columns: {', '.join(fieldnames)}")
    
    issues_by_col = {col: 0 for col in fieldnames}
    na_count = {col: 0 for col in fieldnames}
    empty_count = {col: 0 for col in fieldnames}
    
    for row_idx, r in enumerate(rows, 1):
        for col in fieldnames:
            val = str(r.get(col, "")).strip()
            val_lower = val.lower()
            if not val or val_lower in ["", "nan", "null", "none"]:
                empty_count[col] += 1
                issues_by_col[col] += 1
            elif val_lower in ["n/a", "na"]:
                na_count[col] += 1
                issues_by_col[col] += 1
                
    has_issues = False
    for col in fieldnames:
        total_bad = issues_by_col[col]
        if total_bad > 0:
            has_issues = True
            print(f"    [!] Issue in column '{col}': {total_bad} bad entries (Empty/Null: {empty_count[col]}, 'N/A': {na_count[col]})")
            
    if not has_issues:
        print("    [✓] 100% CLEAN: 0 Empty, 0 Null, 0 NaN, 0 'N/A' across all rows and columns!")

print("\n" + "=" * 80)
