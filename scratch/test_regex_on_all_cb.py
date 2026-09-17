import pandas as pd
import re

df = pd.read_csv('all_scraped_jobs_26_portals.csv')
cb = df[df['Source'].str.contains('CareerBuilder', case=False, na=False) | df['Apply Link'].str.contains('careerbuilder', case=False, na=False)].copy()

def extract_cb_company(role, comp, details, link):
    # If comp is already valid (not placeholder)
    placeholders = ["careerbuilder employer", "inside sales", "pt or ft", "chicago, il", "(raleigh, nc", "spring '27 graduates)", "sales development representative ...", "tampa job in tampa, florida", "enterprise job in ...", "clio | apply today at", "insurance agency"]
    
    # Check if details has "posted X days ago by <Company>"
    m = re.search(r'posted\s+(?:\d+\+?\s+days?\s+ago|\d+\s+hours?\s+ago|\d+\s+months?\s+ago|yesterday|today)?\s*by\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\.|\s+Apply|\s+on\s+CareerBuilder)', details, re.IGNORECASE)
    if m:
        c = m.group(1).strip()
        if c.lower() not in ["careerbuilder", "an employer", "the employer"]:
            return c
            
    # Check "About <Company>"
    m2 = re.search(r'About\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+Trucking|\s+is\s+|\s+was\s+|\s+runs\s+|\s+offers\s+|\s+specializes\s+|\s+provides\s+|\s+builds\s+|\s+creates\s+)', details)
    if m2:
        c = m2.group(1).strip()
        if c.lower() not in ["the role", "us", "our", "you"]:
            return c
            
    # Check "Client Details <Company>"
    m3 = re.search(r'Client Details\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)(?:\s+is|\s+in|\s+has|\s+Chicago)', details)
    if m3:
        return m3.group(1).strip()
        
    # Check "for <Company> Account Executives" or "build <Company>'s"
    m4 = re.search(r'for\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)\s+Account Executives', details)
    if m4:
        return m4.group(1).strip()
        
    m4b = re.search(r"build\s+([A-Z0-9][A-Za-z0-9\s.,&\'\-]+?)'s\s+outbound", details)
    if m4b:
        return m4b.group(1).strip()
        
    # Check if comp has "Clio | Apply Today at" -> "Clio"
    if "|" in comp:
        part0 = comp.split("|")[0].strip()
        if part0.lower() not in placeholders and len(part0) > 1:
            return part0
            
    # Check if comp itself is valid
    if comp.lower() not in placeholders and "careerbuilder" not in comp.lower():
        return comp
        
    return "UNKNOWN"

for idx, r in cb.iterrows():
    extracted = extract_cb_company(r['Job Role'], r['Company Name'], str(r['Company / Job Details']), r['Apply Link'])
    print(f"[{idx}] Orig: {r['Company Name']:<35} -> Extracted: {extracted:<25} | URL: {r['Apply Link'].split('/')[-1][:40]}")
