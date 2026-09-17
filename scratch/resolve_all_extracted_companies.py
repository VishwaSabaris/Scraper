import csv
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from find_company_websites_ddgs import (
    load_cache, append_to_cache, search_company_website_ddgs,
    is_valid_company_url, clean_company_name, CACHE_FILE, KNOWN_ENTERPRISE_MAP
)

def resolve_extracted():
    input_file = "extracted_companies_26_portals.csv"
    output_file = "companies_with_websites_26_portals.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    cache = load_cache()
    
    with open(input_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"[*] Resolving websites for {len(rows)} companies in {input_file}...")
    
    resolved_rows = []
    found_count = 0
    
    for idx, r in enumerate(rows, 1):
        company = r.get("Company Name", "").strip()
        location = r.get("Location", "").strip()
        
        if not company or company in ["N/A", "Unknown", ""]:
            continue
            
        c_clean = clean_company_name(company)
        c_lower = company.lower()
        c_clean_lower = c_clean.lower()
        
        url = None
        # Check cache
        if c_lower in cache and is_valid_company_url(cache[c_lower]):
            url = cache[c_lower]
        elif c_clean_lower in cache and is_valid_company_url(cache[c_clean_lower]):
            url = cache[c_clean_lower]
        elif c_lower in KNOWN_ENTERPRISE_MAP:
            url = KNOWN_ENTERPRISE_MAP[c_lower]
        elif c_clean_lower in KNOWN_ENTERPRISE_MAP:
            url = KNOWN_ENTERPRISE_MAP[c_clean_lower]
            
        if not url:
            # Query DDGS
            print(f"[{idx}/{len(rows)}] Querying DDGS for: {company} ({location})...")
            url = search_company_website_ddgs(company, location)
            if url and url != "N/A":
                cache[c_lower] = url
                cache[c_clean_lower] = url
                append_to_cache(company, url)
                print(f"  [+] Found: {url}")
            else:
                print(f"  [-] Not found")
                url = "N/A"
                
        if url and url != "N/A":
            found_count += 1
            
        resolved_rows.append({
            "Company Name": company,
            "Location": location,
            "Company Website": url if url else "N/A"
        })
        
    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Company Name", "Location", "Company Website"])
        writer.writeheader()
        writer.writerows(resolved_rows)
        
    print(f"[+] Saved {len(resolved_rows)} companies with websites to '{output_file}'.")
    print(f"[+] Coverage: {found_count} / {len(resolved_rows)} ({found_count/len(resolved_rows)*100:.1f}%)")

if __name__ == "__main__":
    resolve_extracted()
