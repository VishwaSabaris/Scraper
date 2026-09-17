from ddgs import DDGS
import pandas as pd
import re
import time

df = pd.read_csv('all_scraped_jobs_26_portals.csv')
cb = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)].copy()

results_resolved = []

with DDGS() as ddgs:
    for idx, row in cb.iterrows():
        url = row['Apply Link']
        slug = url.split('/')[-1].split('?')[0]
        slug_clean = slug.split('--')[0].replace('-', ' ')
        current_det = str(row['Company / Job Details'])
        
        print(f"\n[{idx}] Resolving: {slug_clean}")
        
        # Candidate queries
        queries = [
            f'"{slug.split("--")[0]}"',
            f'careerbuilder {slug_clean}',
            f'"{row["Job Role"]}" {slug_clean}',
            f'"{row["Job Role"]}" CareerBuilder'
        ]
        
        best_comp = None
        best_desc = None
        
        for q in queries:
            try:
                hits = list(ddgs.text(q, max_results=3))
                for h in hits:
                    title = h.get('title', '')
                    body = h.get('body', '')
                    href = h.get('href', '')
                    
                    # Look for "posted X days ago by Company" or "About Company" or "at Company"
                    m = re.search(r'posted\s+.*?by\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\.|\s+Apply|\s+on\s+CareerBuilder)', body, re.IGNORECASE)
                    if m:
                        best_comp = m.group(1).strip()
                    
                    if not best_comp:
                        m2 = re.search(r'About\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+Trucking|\s+is|\s+was|\s+runs|\s+offers|\s+specializes|\s+provides)', body)
                        if m2:
                            best_comp = m2.group(1).strip()
                            
                    if not best_comp:
                        m3 = re.search(r'(?:at|by)\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+in|\s+posted|\s+on|\s*\||\s*–|\s*-\s*CareerBuilder)', title, re.IGNORECASE)
                        if m3 and "CareerBuilder" not in m3.group(1):
                            best_comp = m3.group(1).strip()
                            
                    if len(body) > 100:
                        best_desc = body
                        
                if best_comp and best_desc:
                    break
            except Exception as e:
                time.sleep(1)
                
        print(f"  -> Found Comp: {best_comp} | Desc: {best_desc[:80] if best_desc else 'None'}...")
        results_resolved.append({
            "idx": idx,
            "resolved_comp": best_comp,
            "resolved_desc": best_desc
        })

print(f"\nResolved {len(results_resolved)} rows.")
