"""
Enterprise Company Website Resolver & Date Standardizer
======================================================
1. Formats 100% of 'Date Posted' timestamps into standardized ISO YYYY-MM-DD.
2. Resolves official corporate websites for companies in the dataset.
3. Uses high-coverage dictionary mapping, domain heuristics, and web discovery.
4. Caches results into data/company_websites.csv for instant subsequent lookups.
"""

import os
import re
import csv
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from utils import normalize_date_posted

CACHE_FILE = os.path.abspath("./data/company_websites.csv")

# High-Coverage Enterprise Company Map
TOP_CORPORATE_MAP = {
    "salesforce": "https://www.salesforce.com",
    "pwc": "https://www.pwc.com",
    "pricewaterhousecoopers": "https://www.pwc.com",
    "pwc acceleration centers": "https://www.pwc.com",
    "aveva": "https://www.aveva.com",
    "thermo fisher scientific": "https://www.thermofisher.com",
    "thermo fisher": "https://www.thermofisher.com",
    "natwest group": "https://www.natwestgroup.com",
    "natwest": "https://www.natwestgroup.com",
    "mcafee": "https://www.mcafee.com",
    "mphasis": "https://www.mphasis.com",
    "hcl comnet": "https://www.hcltech.com",
    "hcl techbee": "https://www.hcltech.com",
    "hcl tech": "https://www.hcltech.com",
    "hcltech": "https://www.hcltech.com",
    "hcl": "https://www.hcltech.com",
    "tata consultancy services": "https://www.tcs.com",
    "tcs": "https://www.tcs.com",
    "itc infotech india": "https://www.itcinfotech.com",
    "itc infotech": "https://www.itcinfotech.com",
    "capgemini": "https://www.capgemini.com",
    "datamatics global service": "https://www.datamatics.com",
    "datamatics": "https://www.datamatics.com",
    "deloitte": "https://www.deloitte.com",
    "luxoft": "https://www.luxoft.com",
    "luxoft india": "https://www.luxoft.com",
    "withum": "https://www.withum.com",
    "tekion": "https://www.tekion.com",
    "tekion corp": "https://www.tekion.com",
    "thales group": "https://www.thalesgroup.com",
    "thales": "https://www.thalesgroup.com",
    "tarento group": "https://www.tarento.com",
    "varite inc": "https://www.varite.com",
    "varite": "https://www.varite.com",
    "tresvista": "https://www.tresvista.com",
    "world wide technology": "https://www.wwt.com",
    "zenda": "https://www.zenda.com",
    "zemoso technologies": "https://www.zemosolabs.com",
    "moneyview": "https://www.moneyview.in",
    "o9 solutions": "https://www.o9solutions.com",
    "o9 solutions, inc.": "https://www.o9solutions.com",
    "redica systems": "https://www.redica.com",
    "terralogic": "https://www.terralogic.com",
    "objectways": "https://www.objectways.com",
    "c5i": "https://www.c5i.ai",
    "huawei technologies": "https://www.huawei.com",
    "huawei": "https://www.huawei.com",
    "gradient cyber": "https://www.gradientcyber.com",
    "ziroh labs": "https://www.ziroh.com",
    "appsierra": "https://www.appsierra.com",
    "astra security": "https://www.getastra.com",
    "infosys": "https://www.infosys.com",
    "infosys limited": "https://www.infosys.com",
    "wipro": "https://www.wipro.com",
    "wipro limited": "https://www.wipro.com",
    "accenture": "https://www.accenture.com",
    "accenture india": "https://www.accenture.com",
    "accenture india private limited": "https://www.accenture.com",
    "amazon": "https://www.amazon.com",
    "google": "https://www.google.com",
    "microsoft": "https://www.microsoft.com",
    "apple": "https://www.apple.com",
    "meta": "https://www.meta.com",
    "ibm": "https://www.ibm.com",
    "oracle": "https://www.oracle.com",
    "cisco": "https://www.cisco.com",
    "intel": "https://www.intel.com",
    "nvidia": "https://www.nvidia.com",
    "adobe": "https://www.adobe.com",
    "sap": "https://www.sap.com",
    "dell": "https://www.dell.com",
    "hp": "https://www.hp.com",
    "ericsson": "https://www.ericsson.com",
    "nokia": "https://www.nokia.com",
    "cognizant": "https://www.cognizant.com",
    "l&t technology services": "https://www.ltts.com",
    "ltts": "https://www.ltts.com",
    "tech mahindra": "https://www.techmahindra.com",
    "ltimindtree": "https://www.ltimindtree.com",
    "hexaware": "https://www.hexaware.com",
    "zensar": "https://www.zensar.com",
    "birlasoft": "https://www.birlasoft.com",
    "sonata software": "https://www.sonata-software.com",
    "kpit": "https://www.kpit.com",
    "persistent systems": "https://www.persistent.com",
    "cyient": "https://www.cyient.com",
    "cloudxtreme": "https://www.cloudxtreme.com",
    "bluelight consulting": "https://www.bluelight.co",
    "deutsche telekom digital labs": "https://www.telekom.com",
    "deutsche telekom": "https://www.telekom.com",
    "ntt data": "https://www.nttdata.com",
    "ntt data global delivery services ltd": "https://www.nttdata.com",
    "ntt data business solutions": "https://www.nttdata.com",
    "artech": "https://www.artech.com",
    "recro": "https://www.recro.io",
    "straive": "https://www.straive.com",
    "gyansys": "https://www.gyansys.com",
    "xencia": "https://www.xencia.com",
    "xencia technology solutions": "https://www.xencia.com",
    "rapido": "https://www.rapido.bike",
    "epam systems": "https://www.epam.com",
    "epam": "https://www.epam.com",
    "kpmg": "https://www.kpmg.com",
    "kpmg india services llp": "https://www.kpmg.com",
    "ey": "https://www.ey.com",
    "ernst & young": "https://www.ey.com",
    "ernst & young llp ( ey india )": "https://www.ey.com",
    "happiest minds technologies": "https://www.happiestminds.com",
    "happiest minds": "https://www.happiestminds.com",
    "antino": "https://www.antino.com",
    "fdm group": "https://www.fdmgroup.com",
    "t-mobile": "https://www.t-mobile.com",
    "datazip": "https://www.datazip.io",
    "gsstech group": "https://www.gsstechgroup.com",
    "hawk martech": "https://www.hawkmartech.com",
    "nuplay ai": "https://www.nuplay.ai",
    "oolka": "https://www.oolka.in",
    "manifest": "https://www.manifest.com",
    "swiggy": "https://www.swiggy.com",
    "zomato": "https://www.zomato.com",
    "flipkart": "https://www.flipkart.com",
    "myntra": "https://www.myntra.com",
    "ola": "https://www.olacabs.com",
    "phonepe": "https://www.phonepe.com",
    "paytm": "https://www.paytm.com",
    "razorpay": "https://www.razorpay.com",
    "zerodha": "https://www.zerodha.com",
    "groww": "https://www.groww.in",
    "cred": "https://www.cred.club",
    "postman": "https://www.postman.com",
    "browserstack": "https://www.browserstack.com",
    "cleartax": "https://www.cleartax.in",
    "urban company": "https://www.urbancompany.com",
    "meesho": "https://www.meesho.com",
    "zepto": "https://www.zeptonow.com",
    "blinkit": "https://www.blinkit.com",
    "jio": "https://www.jio.com",
    "airtel": "https://www.airtel.in",
    "vodafone": "https://www.vodafone.com",
    "citius tech": "https://www.citiustech.com",
    "virtusa": "https://www.virtusa.com",
    "nagarro": "https://www.nagarro.com",
    "expleo": "https://www.expleo.com",
    "bosh": "https://www.bosch.com",
    "bosch global software technologies": "https://www.bosch.com",
    "siemens": "https://www.siemens.com",
    "schneider electric": "https://www.se.com",
    "cisco systems": "https://www.cisco.com",
    "goldman sachs": "https://www.goldmansachs.com",
    "morgan stanley": "https://www.morganstanley.com",
    "jpmorgan chase": "https://www.jpmorganchase.com",
    "wells fargo": "https://www.wellsfargo.com",
    "standard chartered": "https://www.sc.com",
    "hsbc": "https://www.hsbc.com",
    "barclays": "https://www.barclays.com",
    "societe generale": "https://www.societegenerale.com",
    "ubs": "https://www.ubs.com",
    "target": "https://www.target.com",
    "walmart": "https://www.walmart.com",
    "walmart global tech": "https://www.walmart.com"
}

def clean_company_name(name: str) -> str:
    if not name or str(name).lower() in ["n/a", "unknown", "confidential", "jooble employer", "foundit recruiter", "nan", "null"]:
        return ""
    clean = re.sub(r'(?i)\b(pvt\.?\s*ltd\.?|private\s+limited|limited|inc\.?|llc|corp\.?|corporation|gmbh|co\.?|india|services|technologies|solutions|group|labs|acceleration\s+centers)\b', '', str(name))
    clean = re.sub(r'[\(\)\[\]\{\}]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' ,.-')
    return clean if clean else str(name).strip()

def load_cache() -> dict:
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c = row.get("Company Name", "").strip().lower()
                    u = row.get("Website URL", "").strip()
                    if c and u:
                        cache[c] = u
        except Exception:
            pass
    return cache

def save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Company Name", "Website URL"])
        writer.writeheader()
        for c, u in sorted(cache.items()):
            writer.writerow({"Company Name": c, "Website URL": u})

def verify_domain_fast(domain: str) -> bool:
    """Quickly check if a domain responds to HTTP HEAD request."""
    try:
        url = f"https://{domain}"
        resp = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        return resp.status_code < 400
    except Exception:
        try:
            url = f"http://{domain}"
            resp = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            return resp.status_code < 400
        except Exception:
            return False

def resolve_single_company(company_name: str, cache: dict) -> str:
    if not company_name or str(company_name).lower() in ["n/a", "unknown", "confidential", "jooble employer", "foundit recruiter", "nan", "null", ""]:
        return "N/A"
        
    c_raw = str(company_name).strip()
    c_lower = c_raw.lower()
    
    # 1. Exact or alias match in curated corporate map
    if c_lower in TOP_CORPORATE_MAP:
        return TOP_CORPORATE_MAP[c_lower]
        
    # Check partial match in corporate map
    for k, url in TOP_CORPORATE_MAP.items():
        if k in c_lower or c_lower in k:
            return url
            
    # 2. Check local persistent cache
    if c_lower in cache and cache[c_lower] != "N/A":
        return cache[c_lower]
        
    # 3. Fast Domain Heuristic (.com / .in / .io / .ai)
    clean = clean_company_name(c_raw)
    slug = re.sub(r'[^a-z0-9]', '', clean.lower())
    if len(slug) >= 3:
        for tld in [".com", ".in", ".io", ".ai", ".co"]:
            candidate = f"{slug}{tld}"
            if verify_domain_fast(candidate):
                site_url = f"https://www.{candidate}"
                cache[c_lower] = site_url
                return site_url

    return "N/A"

def process_job_csv(filepath: str):
    print(f"\n[*] Processing and enhancing dataset: '{filepath}'...", flush=True)
    if not os.path.exists(filepath):
        print(f"[!] File '{filepath}' not found.", flush=True)
        return
        
    df = pd.read_csv(filepath)
    total_rows = len(df)
    print(f"[*] Loaded {total_rows} listings.", flush=True)
    
    # 1. Standardize 100% of dates to YYYY-MM-DD
    print("[*] 1/2 Standardizing Date Posted format to ISO YYYY-MM-DD...", flush=True)
    df['Date Posted'] = df['Date Posted'].apply(normalize_date_posted)
    
    # 2. Resolve official company websites
    print("[*] 2/2 Resolving company website domains (Company Link)...", flush=True)
    cache = load_cache()
    
    unique_companies = [c for c in df['Company Name'].dropna().unique() if str(c).strip()]
    print(f"[*] Analyzing {len(unique_companies)} unique companies...", flush=True)
    
    company_site_map = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_comp = {executor.submit(resolve_single_company, c, cache): c for c in unique_companies}
        for future in as_completed(future_to_comp):
            c = future_to_comp[future]
            try:
                company_site_map[c] = future.result()
            except Exception:
                company_site_map[c] = "N/A"
                
    # Update dataframe
    df['Company Link'] = df['Company Name'].map(lambda c: company_site_map.get(c, "N/A") if pd.notna(c) else "N/A")
    
    # Save cache
    save_cache(cache)
    
    # Save CSV
    df.to_csv(filepath, index=False)
    resolved_count = (df['Company Link'] != "N/A").sum()
    valid_dates_count = (df['Date Posted'] != "N/A").sum()
    print(f"\n[++++] Processing Complete for '{filepath}'!", flush=True)
    print(f"  * Total Records       : {total_rows}", flush=True)
    print(f"  * Normalized Dates    : {valid_dates_count} / {total_rows} ({valid_dates_count/total_rows*100:.1f}%) formatted as YYYY-MM-DD", flush=True)
    print(f"  * Resolved Websites   : {resolved_count} / {total_rows} ({resolved_count/total_rows*100:.1f}%) official corporate links", flush=True)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "all_jobs_vvs.csv"
    process_job_csv(target)
