import pandas as pd
import numpy as np

def evaluate():
    df = pd.read_csv('all_jobs_vvs.csv')
    print("=" * 60)
    print("          DATASET QUALITY & ACCURACY AUDIT")
    print("=" * 60)
    print(f"Total Extracted Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}\n")

    print("--- 1. SOURCE BREAKDOWN ---")
    source_counts = df['Source'].value_counts()
    for s, c in source_counts.items():
        print(f"  * {s:<25}: {c:>5} jobs ({(c/len(df))*100:.1f}%)")
    print()

    # Role matching check
    devops_keywords = ['devops', 'sre', 'site reliability', 'cloud', 'infrastructure', 'platform', 
                       'ci/cd', 'kubernetes', 'docker', 'aws', 'azure', 'gcp', 'linux', 'sysadmin', 
                       'system admin', 'automation', 'release', 'build', 'terraform', 'ansible', 
                       'jenkins', 'gitops', 'lead', 'architect', 'security', 'operations', 'engineer', 'developer']

    def is_devops_match(title):
        if not isinstance(title, str):
            return False
        t = title.lower()
        return any(k in t for k in devops_keywords)

    matches = df['Job Role'].apply(is_devops_match)
    match_rate = (matches.sum() / len(df)) * 100
    print("--- 2. JOB ROLE RELEVANCE ---")
    print(f"  * DevOps / Cloud / Infrastructure Matching: {matches.sum()} / {len(df)} ({match_rate:.2f}%)")
    
    non_matches = df[~matches]
    if len(non_matches) > 0:
        print(f"  * Non-standard title samples ({len(non_matches)} total):")
        for t in non_matches['Job Role'].head(5):
            print(f"    - {t}")
    print()

    # Location check
    print("--- 3. LOCATION RELEVANCE ---")
    bangalore_terms = ['bangalore', 'bengaluru', 'karnataka', 'remote', 'india', 'in']
    def is_bangalore_match(loc):
        if not isinstance(loc, str):
            return False
        l = loc.lower()
        return any(t in l for t in bangalore_terms)

    loc_matches = df['Location'].apply(is_bangalore_match)
    loc_match_rate = (loc_matches.sum() / len(df)) * 100
    print(f"  * Bangalore / Remote / India Matching: {loc_matches.sum()} / {len(df)} ({loc_match_rate:.2f}%)")
    print("  * Top 8 Locations in Dataset:")
    for loc, count in df['Location'].value_counts().head(8).items():
        print(f"    - {loc:<35}: {count} jobs")
    print()

    # Data Completeness Check
    print("--- 4. DATA COMPLETENESS & SCHEMA INTEGRITY ---")
    apply_valid = df['Apply Link'].notna() & (df['Apply Link'] != 'N/A') & (df['Apply Link'] != '')
    print(f"  * Apply Links Valid & Present : {apply_valid.sum()} / {len(df)} ({(apply_valid.sum()/len(df))*100:.2f}%)")
    print(f"  * Unique Apply Links (0 Dupes): {df['Apply Link'].nunique()} / {len(df)}")
    
    comp_valid = df['Company Name'].notna() & (df['Company Name'] != 'N/A') & (df['Company Name'] != '')
    print(f"  * Company Names Populated     : {comp_valid.sum()} / {len(df)} ({(comp_valid.sum()/len(df))*100:.2f}%)")
    
    date_valid = df['Date Posted'].notna() & (df['Date Posted'] != 'N/A') & (df['Date Posted'] != '')
    print(f"  * Date Posted Populated       : {date_valid.sum()} / {len(df)} ({(date_valid.sum()/len(df))*100:.2f}%)")
    
    det_valid = df['Company / Job Details'].notna() & (df['Company / Job Details'] != 'N/A') & (df['Company / Job Details'] != '')
    print(f"  * Details & Skills Populated  : {det_valid.sum()} / {len(df)} ({(det_valid.sum()/len(df))*100:.2f}%)")
    print("=" * 60)

if __name__ == "__main__":
    evaluate()
