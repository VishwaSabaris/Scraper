import os
import re
import csv
import socket
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

def clean_company_name(name):
    if not name or str(name).lower() in ['n/a', 'nan', 'null', 'unknown', 'confidential', 'jooble employer', 'foundit recruiter', 'careerbuilder employer', 'indeed employer']:
        return ''
    clean = re.sub(r'(?i)\b(pvt\.?\s*ltd\.?|private\s+limited|limited|inc\.?|llc|corp\.?|corporation|gmbh|co\.?|india\s+private\s+limited|india\s+pvt\s+ltd|india\s+llp|india|technology\s+information|services|technologies|solutions|group|labs|pty\s+ltd|enterprises|holdings|m/s|private\s+ltd)\b', '', str(name))
    clean = re.sub(r'[\(\)\[\]\{\}]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' ,.-')
    return clean if len(clean) >= 2 else str(name).strip()

def fast_dns_check(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

def verify_live_domain(domain):
    if not fast_dns_check(domain):
        return False
    try:
        url = f"https://{domain}"
        r = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return r.status_code < 400
    except Exception:
        try:
            url = f"http://{domain}"
            r = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            return r.status_code < 400
        except Exception:
            return False

def resolve_company_fast(company_name, cache):
    if not company_name:
        return "N/A"
    c_raw = str(company_name).strip()
    c_lower = c_raw.lower()
    
    # Check cache
    if c_lower in cache and cache[c_lower] != "N/A":
        return cache[c_lower]
        
    clean = clean_company_name(c_raw)
    if not clean:
        return "N/A"
        
    clean_lower = clean.lower()
    if clean_lower in cache and cache[clean_lower] != "N/A":
        return cache[clean_lower]
        
    # Generate slugs
    slug = re.sub(r'[^a-z0-9]', '', clean_lower)
    if len(slug) >= 3:
        for tld in [".com", ".in", ".io", ".ai", ".co", ".org", ".net", ".tech"]:
            candidate = f"{slug}{tld}"
            if verify_live_domain(candidate):
                site = f"https://www.{candidate}"
                cache[c_lower] = site
                return site
                
    return "N/A"

df = pd.read_csv('all_sdr_26_jobs.csv')
companies = [c for c in df['Company Name'].dropna().unique() if str(c).strip()]
print(f"Testing fast resolution on {len(companies)} unique companies...")

cache = {}
if os.path.exists('data/company_websites.csv'):
    with open('data/company_websites.csv', 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            c = row.get('Company Name', '').strip().lower()
            u = row.get('Website URL', '').strip()
            if c and u and u != 'N/A':
                cache[c] = u

resolved_map = {}
with ThreadPoolExecutor(max_workers=40) as executor:
    futures = {executor.submit(resolve_company_fast, c, cache): c for c in companies}
    for f in as_completed(futures):
        c = futures[f]
        try:
            resolved_map[c] = f.result()
        except Exception:
            resolved_map[c] = "N/A"

resolved_count = sum(1 for v in resolved_map.values() if v != "N/A")
print(f"Fast DNS + Heuristics + Cache resolved: {resolved_count} / {len(companies)} ({resolved_count/len(companies)*100:.1f}%)")

sample_res = list(resolved_map.items())[:15]
for c, u in sample_res:
    print(f"  {c:<40} -> {u}")
