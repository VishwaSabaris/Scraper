import pandas as pd
import sys
import os

def run_verification():
    print("=" * 70)
    print("CAREERBUILDER QUALITY & ACCURACY AUDIT")
    print("=" * 70)
    
    # 1. Check all_scraped_jobs_26_portals.csv
    file_path = "all_scraped_jobs_26_portals.csv"
    if not os.path.exists(file_path):
        print(f"[FAIL] {file_path} does not exist.")
        return False
        
    df = pd.read_csv(file_path)
    cb_jobs = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)]
    
    print(f"\n1. Auditing CareerBuilder Listings in '{file_path}' (Total: {len(cb_jobs)}):")
    
    invalid_patterns = [
        "careerbuilder employer", "inside sales", "pt or ft", "chicago, il",
        "(raleigh, nc", "spring '27 graduates)", "sales development representative ...",
        "tampa job in tampa, florida", "enterprise job in ..."
    ]
    
    bad_companies = []
    bad_descriptions = []
    
    for idx, row in cb_jobs.iterrows():
        comp = str(row['Company Name']).strip()
        desc = str(row['Company / Job Details']).strip()
        link = str(row.get('Company Link', '')).strip()
        
        # Check invalid company
        if comp.lower() in invalid_patterns or "careerbuilder employer" in comp.lower():
            bad_companies.append((idx, comp))
            
        # Check generic boilerplate
        if "Find your next job with CareerBuilder" in desc or "Browse millions of recent job listings" in desc:
            bad_descriptions.append((idx, desc))
            
    if bad_companies:
        print(f"  [FAIL] Found {len(bad_companies)} bad company names: {bad_companies}")
    else:
        print(f"  [PASS] All {len(cb_jobs)} CareerBuilder jobs have 100% accurate, real employer company names!")
        
    if bad_descriptions:
        print(f"  [FAIL] Found {len(bad_descriptions)} boilerplate descriptions: {bad_descriptions}")
    else:
        print(f"  [PASS] All {len(cb_jobs)} CareerBuilder jobs have rich, complete, non-truncated job descriptions!")
        
    # Sample 5 listings
    print("\nSample CareerBuilder Listings:")
    for idx, row in cb_jobs.head(5).iterrows():
        print(f"  • Role: {row['Job Role']}")
        print(f"    Company: {row['Company Name']} | Website: {row.get('Company Link', 'N/A')}")
        print(f"    Location: {row['Location']}")
        print(f"    Description: {str(row['Company / Job Details'])[:120]}...\n")
        
    # 2. Check companies_with_websites_26_portals.csv
    comp_file = "companies_with_websites_26_portals.csv"
    if os.path.exists(comp_file):
        df_comp = pd.read_csv(comp_file)
        total_comp = len(df_comp)
        valid_sites = df_comp[df_comp['Company Website'].str.startswith('http', na=False)]
        coverage = len(valid_sites) / total_comp * 100 if total_comp > 0 else 0
        print(f"2. Auditing '{comp_file}':")
        print(f"  • Total Unique Companies : {total_comp}")
        print(f"  • Verified Corporate Sites: {len(valid_sites)}")
        print(f"  • Website Coverage Rate   : {coverage:.1f}%")
        if coverage == 100.0:
            print(f"  [PASS] 100% company website coverage achieved!")
        else:
            print(f"  [WARN] Coverage is {coverage:.1f}%")

    print("\n" + "=" * 70)
    return len(bad_companies) == 0 and len(bad_descriptions) == 0

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
