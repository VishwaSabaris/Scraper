import asyncio
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrape_all_jobs_master import run_master_scraper
from filter_engine import UniversalJobFilter

async def run_test(test_id, role, location, portals):
    out_csv = f"test_run_{test_id}.csv"
    if os.path.exists(out_csv):
        os.remove(out_csv)
        
    print(f"\n========================================================")
    print(f"[*] RUNNING TEST {test_id}: {role} in {location} on [{portals}]")
    print(f"========================================================")
    
    filters = UniversalJobFilter(
        keywords=role,
        job_title=role,
        location=location,
        experience_level="",
        job_type="",
        work_mode=""
    )
    
    target_portals = [p.strip() for p in portals.split(",") if p.strip()]
    await run_master_scraper(target_portals, filters, max_pages=1, output_file=out_csv)
    
    # Audit output CSV
    print(f"\n--- AUDITING TEST {test_id} OUTPUT: {out_csv} ---")
    if not os.path.exists(out_csv):
        print(f"[!] File {out_csv} not created!")
        return False
        
    with open(out_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
        
    print(f"[+] Total rows in CSV: {len(rows)}")
    print(f"[+] Headers: {fieldnames}")
    
    na_count = 0
    empty_count = 0
    
    for i, r in enumerate(rows):
        for k, v in r.items():
            val = str(v).strip()
            if not val:
                print(f"[!] Row {i} - Column '{k}' is EMPTY!")
                empty_count += 1
            if val.lower() in ["n/a", "none", "null", "nan"]:
                print(f"[!] Row {i} - Column '{k}' has '{val}'!")
                na_count += 1
                
    print(f"[*] Results for Test {test_id}:")
    print(f"    - Total Empty Values : {empty_count}")
    print(f"    - Total N/A Values   : {na_count}")
    
    is_perfect = (empty_count == 0 and na_count == 0 and len(rows) > 0)
    print(f"    - 100% CLEAN STATUS  : {'PASS (100% CLEAN)' if is_perfect else 'FAIL'}")
    return is_perfect

async def main():
    t1 = await run_test(1, "Frontend Engineer", "San Francisco", "builtin,dice,adzuna")
    t2 = await run_test(2, "Product Manager", "London", "reed,workable,jobspresso")
    t3 = await run_test(3, "Data Scientist", "Hyderabad", "foundit,shine,apna,freshersworld")
    
    print("\n" + "=" * 60)
    print("FINAL TEST SUITE SUMMARY:")
    print(f"Test 1 (Frontend Engineer / SF / builtin,dice,adzuna) : {'PASS' if t1 else 'FAIL'}")
    print(f"Test 2 (Product Manager / London / reed,workable,jobspresso) : {'PASS' if t2 else 'FAIL'}")
    print(f"Test 3 (Data Scientist / Hyderabad / foundit,shine,apna,fw) : {'PASS' if t3 else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
