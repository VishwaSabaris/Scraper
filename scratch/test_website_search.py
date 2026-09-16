import urllib.parse
import re
import requests
from ddgs import DDGS
from concurrent.futures import ThreadPoolExecutor

EXCLUDED_DOMAINS = {
    "google.com", "google.co.in", "duckduckgo.com", "bing.com", "yahoo.com",
    "linkedin.com", "indeed.com", "glassdoor.com", "glassdoor.co.in",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com",
    "wikipedia.org", "crunchbase.com", "naukri.com", "shine.com", "foundit.in",
    "instahyre.com", "internshala.com", "apna.co", "timesjobs.com", "freshersworld.com",
    "zaubacorp.com", "toffler.in", "ambitionbox.com", "zoominfo.com", "pitchbook.com",
    "theorg.com", "craft.co", "owler.com", "levels.fyi", "ycombinator.com", "github.com"
}

def clean_company_name(name):
    if not name or str(name).lower() in ["n/a", "unknown", "confidential", "nan", "null"]:
        return ""
    clean = re.sub(r'(?i)\b(pvt\.?\s*ltd\.?|private\s+limited|limited|inc\.?|llc|corp\.?|corporation|gmbh|co\.?|india\s+private\s+limited|india\s+pvt\s+ltd|india\s+llp|india|services|technologies|solutions|technologies\s+pvt\s+ltd)\b', '', str(name))
    clean = re.sub(r'[\(\)\[\]\{\}]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' ,.-')
    return clean if len(clean) >= 2 else str(name).strip()

def is_valid_company_website(url):
    if not url or not url.startswith("http"):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        for ex in EXCLUDED_DOMAINS:
            if domain == ex or domain.endswith("." + ex):
                return False
        return bool(domain and "." in domain)
    except Exception:
        return False

def extract_base_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url

def search_company_website(company, location=""):
    clean = clean_company_name(company)
    if not clean:
        return "N/A"
        
    query = f'"{clean}" official website'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            for r in results:
                href = r.get("href", "")
                if is_valid_company_website(href):
                    return extract_base_domain(href)
    except Exception:
        pass
    return "N/A"

sample_companies = [
    "Kinetic Innovative Staffing Pty Ltd",
    "MoEngage",
    "CrowdStrike",
    "EBIZON NETINFO PRIVATE LIMITED",
    "Salesforce.com India Pvt Ltd",
    "NielsenIQ",
    "Testzeus",
    "Kadwin Technologies",
    "New Relic One India Pvt. Ltd.",
    "Thermo Fisher Scientific India Pvt Ltd",
    "Snowflake Computing India Llp",
    "Atlassian India Llp"
]

print("Testing website resolution on sample companies:")
for comp in sample_companies:
    site = search_company_website(comp)
    print(f"  {comp:<40} -> {site}")
