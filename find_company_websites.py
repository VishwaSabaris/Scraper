"""
Company Website Finder Utility (DataForSEO SERP API + Local Fallback)
====================================================================
1. Reads company names & locations from a job CSV or extracted company CSV.
2. Resolves official company website URLs using DataForSEO Google SERP API (via API_KEY_SERP from .env).
3. If the API key is not present or account verification is pending, falls back gracefully to DuckDuckGo / local search.
4. Automatically caches results in data/company_websites.csv so queries are never duplicated.
"""

import os
import sys
import csv
import time
import base64
import random
import logging
import urllib.parse
from typing import List, Dict, Optional, Tuple, Set

import requests

# ── Logging Configuration ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CompanyWebsiteFinder")

# ── Domains that are directories, social media, or job boards (not official homepages) ─
EXCLUDED_DOMAINS = {
    "google.com", "google.co.uk", "google.co.in", "google.com.au",
    "duckduckgo.com", "bing.com", "yahoo.com", "yandex.com",
    "linkedin.com", "indeed.com", "glassdoor.com", "glassdoor.co.uk",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com",
    "wikipedia.org", "crunchbase.com", "reed.co.uk", "wellfound.com",
    "github.com", "youtube.com", "xing.com", "zoominfo.com",
    "pitchbook.com", "jobspresso.co", "himalayas.app", "remote.com",
    "ziprecruiter.com", "careerbuilder.com", "naukri.com", "simplyhired.com",
    "totaljobs.com", "cv-library.co.uk", "adzuna.com", "monster.com",
    "seek.com.au", "bloomberg.com", "reuters.com", "wsj.com",
    "wuzzuf.net", "angel.co", "companieshouse.gov.uk", "gov.uk",
    "craft.co", "theorg.com", "owler.com", "cbinsights.com",
    "glassdoor.com", "glassdoor.co.uk", "levels.fyi", "ycombinator.com"
}


# ─────────────────────────────────────────────────────────────────────────────
# Environment and Config Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_env_variable(key: str, default: str = "") -> str:
    """Reads environment variable directly or by parsing .env file."""
    val = os.environ.get(key)
    if val:
        return val.strip()
    
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        env_path = ".env"

    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip("'").strip('"')
        except Exception as e:
            logger.warning(f"Error reading .env file: {e}")
            
    return default


def get_dataforseo_auth_header(api_key: str) -> Optional[str]:
    """Generates the HTTP Basic Authorization header string from the API key."""
    if not api_key:
        return None
    api_key = api_key.strip()
    if api_key.startswith("Basic "):
        return api_key
    
    # Check if already a base64 encoded 'login:password'
    try:
        decoded = base64.b64decode(api_key).decode("utf-8")
        if ":" in decoded:
            return f"Basic {api_key}"
    except Exception:
        pass
    
    # If passed as 'login:password', encode to base64
    if ":" in api_key:
        encoded = base64.b64encode(api_key.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"
        
    return f"Basic {api_key}"


# ─────────────────────────────────────────────────────────────────────────────
# Name and URL Cleaning Helpers
# ─────────────────────────────────────────────────────────────────────────────

def clean_company_name(name: str) -> str:
    """Strip bullet separators and common legal suffixes."""
    if not name:
        return ""
    name = name.strip()
    if "•" in name:
        name = name.split("•")[0].strip()
    for suffix in [
        " Ltd", " Limited", " LLC", " Inc.", " Inc", " Corp.", " Corp",
        " Co.", " Co", " plc", " PLC", " LLP", " Ltd.", " Limited."
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    return name


def clean_location(location: str) -> str:
    """Return primary city from a location string."""
    if not location:
        return ""
    return location.split(",")[0].strip()


def is_valid_company_website(url: str) -> bool:
    """True if the URL is plausibly an official company homepage."""
    if not url or url == "N/A" or not url.startswith("http"):
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


def extract_base_domain_url(url: str) -> str:
    """Extracts scheme://domain from full URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return url
    except Exception:
        return url


# ─────────────────────────────────────────────────────────────────────────────
# DataForSEO Google SERP API Resolver
# ─────────────────────────────────────────────────────────────────────────────

def search_websites_dataforseo_batch(
    companies_batch: List[Tuple[str, str]],
    auth_header: str
) -> Dict[str, str]:
    """
    Queries DataForSEO Google SERP Live Advanced endpoint in batches.
    Returns mapping of lowercase company name -> resolved website URL.
    """
    endpoint = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }

    payload = []
    for idx, (company, location) in enumerate(companies_batch):
        clean_name = clean_company_name(company)
        clean_loc = clean_location(location)
        query = f"{clean_name} {clean_loc} official website" if clean_loc else f"{clean_name} official website"
        
        payload.append({
            "keyword": query,
            "language_code": "en",
            "depth": 5,
            "tag": company  # tag is echoed back in the response
        })

    results_map: Dict[str, str] = {}

    try:
        logger.info(f"Sending batch of {len(payload)} search tasks to DataForSEO SERP API...")
        response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
        
        if response.status_code != 200:
            logger.warning(f"DataForSEO HTTP status: {response.status_code}. Response: {response.text[:300]}")
            return results_map

        data = response.json()
        status_code = data.get("status_code")
        status_msg = data.get("status_message")

        # Check for verification errors
        if status_code == 40104 or "verify your account" in str(status_msg).lower():
            logger.error(
                "[!] DataForSEO Account Verification Required: "
                "Please verify your account at https://app.dataforseo.com/ to enable live SERP requests."
            )
            return results_map

        if status_code != 20000 and status_code != 200:
            logger.warning(f"DataForSEO error: {status_code} - {status_msg}")
            return results_map

        tasks = data.get("tasks", [])
        for task in tasks:
            task_status = task.get("status_code")
            task_msg = task.get("status_message")
            if task_status and task_status != 20000:
                logger.warning(f"DataForSEO task issue [{task_status}]: {task_msg}")
                continue

            company_tag = task.get("tag") or (task.get("data", {}).get("keyword") if task.get("data") else None)
            if not company_tag:
                continue

            found_url = "N/A"
            task_result = task.get("result")
            if task_result and len(task_result) > 0:
                items = task_result[0].get("items", [])
                for item in items:
                    if item.get("type") == "organic":
                        url = item.get("url", "")
                        if is_valid_company_website(url):
                            found_url = extract_base_domain_url(url)
                            logger.info(f"  [DataForSEO] ✓ {company_tag} -> {found_url}")
                            break

            results_map[company_tag.lower().strip()] = found_url

    except Exception as e:
        logger.error(f"Error during DataForSEO batch request: {e}")

    return results_map


# ─────────────────────────────────────────────────────────────────────────────
# Local Fallback Search (DuckDuckGo Search)
# ─────────────────────────────────────────────────────────────────────────────

def _ddg_search_single(query: str, max_retries: int = 2) -> Optional[str]:
    """Queries DuckDuckGo via ddgs library with fallback."""
    try:
        from ddgs import DDGS
        for attempt in range(1, max_retries + 1):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    for r in results:
                        href = r.get("href", "")
                        if href and is_valid_company_website(href):
                            return extract_base_domain_url(href)
                return None
            except Exception as e:
                time.sleep(1.5 * attempt)
    except ImportError:
        pass
    return None


def search_website_fallback(company: str, location: str) -> str:
    """Performs local fallback search for a company website."""
    clean_name = clean_company_name(company)
    clean_loc = clean_location(location)

    queries = [
        f"{clean_name} {clean_loc} official website",
        f"{clean_name} official website",
    ]

    for q in queries:
        url = _ddg_search_single(q)
        if url:
            logger.info(f"  [Fallback] ✓ {company} -> {url}")
            return url
        time.sleep(random.uniform(0.6, 1.2))

    logger.warning(f"  [Fallback] ✗ No website found for '{company}'.")
    return "N/A"


# ─────────────────────────────────────────────────────────────────────────────
# Main Website Resolution Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def find_websites_locally(input_csv: str, output_csv: str, batch_size: int = 25):
    """
    Reads the input CSV, resolves company website URLs using DataForSEO SERP API
    (with local search fallback), caches resolved websites to data/company_websites.csv,
    adds a 'Website' column, and writes the updated dataset to output_csv.
    """
    if not os.path.exists(input_csv):
        logger.error(f"Input CSV '{input_csv}' not found.")
        return

    logger.info(f"Starting company website resolution for '{input_csv}'...")

    # Step 1: Read API key from .env
    api_key_serp = get_env_variable("API_KEY_SERP")
    auth_header = get_dataforseo_auth_header(api_key_serp) if api_key_serp else None

    if auth_header:
        logger.info("[*] DataForSEO API Key detected. Using DataForSEO Google SERP API for website resolution.")
    else:
        logger.warning("[-] No API_KEY_SERP found in .env. Using free local search engine fallback.")

    # Step 2: Load cached website mappings
    cache_csv = "data/company_websites.csv"
    os.makedirs(os.path.dirname(cache_csv), exist_ok=True)
    resolved: Dict[str, str] = {}

    if os.path.exists(cache_csv):
        try:
            with open(cache_csv, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    c = row.get("Company Name", "").strip().lower()
                    url = row.get("Website URL", "").strip()
                    if url and url != "N/A":
                        resolved[c] = url
            logger.info(f"Loaded {len(resolved)} cached website mappings from {cache_csv}.")
        except Exception as e:
            logger.warning(f"Could not read website cache: {e}")

    # Step 3: Read input rows
    records = []
    fieldnames = []
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            records.append(row)

    if not records:
        logger.warning(f"Input CSV '{input_csv}' has no data rows.")
        return

    # Add 'Website' or 'Website URL' header if missing
    website_col = "Website URL" if "Website URL" in fieldnames else "Website"
    if website_col not in fieldnames:
        fieldnames.append(website_col)

    # Step 4: Identify companies that need resolution
    pending_companies: List[Tuple[str, str]] = []
    seen_pending: Set[str] = set()

    for row in records:
        company = row.get("Company Name", "").strip()
        location = row.get("Location", "").strip()
        current_web = row.get(website_col, "N/A")

        if not company or company.lower() == "n/a":
            continue

        c_lower = company.lower()
        if current_web and current_web != "N/A" and current_web.startswith("http"):
            resolved[c_lower] = current_web
            continue

        if c_lower not in resolved and c_lower not in seen_pending:
            seen_pending.add(c_lower)
            pending_companies.append((company, location))

    logger.info(f"Total entries: {len(records)} | Unique companies to resolve: {len(pending_companies)}")

    # Step 5: Resolve in batches using DataForSEO if available
    api_failed = False
    newly_resolved_count = 0

    if auth_header and pending_companies:
        for i in range(0, len(pending_companies), batch_size):
            batch = pending_companies[i:i + batch_size]
            batch_results = search_websites_dataforseo_batch(batch, auth_header)
            
            # Check if API returned results
            if batch_results:
                for company, _ in batch:
                    c_lower = company.lower()
                    url = batch_results.get(c_lower, "N/A")
                    resolved[c_lower] = url
                    if url != "N/A":
                        newly_resolved_count += 1
            else:
                logger.warning(f"DataForSEO batch {i // batch_size + 1} did not return results. Switching to local fallback.")
                api_failed = True
                break

    # Step 6: For remaining unresolved companies, use fallback
    for company, location in pending_companies:
        c_lower = company.lower()
        if c_lower not in resolved or resolved[c_lower] == "N/A" and api_failed:
            url = search_website_fallback(company, location)
            resolved[c_lower] = url
            if url != "N/A":
                newly_resolved_count += 1

    # Step 7: Update records and cache
    cache_rows_to_save = []
    for row in records:
        company = row.get("Company Name", "").strip()
        c_lower = company.lower()
        website = resolved.get(c_lower, "N/A")
        row[website_col] = website

    # Write output CSV
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Save all resolved mappings to cache
    with open(cache_csv, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=["Company Name", "Location", "Website URL"])
        writer.writeheader()
        for row in records:
            c = row.get("Company Name", "").strip()
            l = row.get("Location", "").strip()
            w = row.get(website_col, "N/A")
            if c and c.lower() != "n/a":
                writer.writerow({
                    "Company Name": c,
                    "Location": l,
                    "Website URL": w
                })

    logger.info(
        f"[+] Completed! Resolved {newly_resolved_count} new websites. "
        f"Output written to '{output_csv}' and cached in '{cache_csv}'."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Helper
# ─────────────────────────────────────────────────────────────────────────────

def extract_unique_companies_from_csv(input_csv: str, output_csv: str) -> List[Dict[str, str]]:
    """
    Extracts unique company names and locations from a specified job CSV
    and saves them to output_csv.
    """
    if not os.path.exists(input_csv):
        logger.error(f"Input CSV '{input_csv}' not found.")
        return []

    seen = set()
    unique_companies = []

    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            logger.error(f"Input CSV '{input_csv}' has no headers.")
            return []

        company_col = None
        location_col = None
        for col in reader.fieldnames:
            col_l = col.lower().strip()
            if col_l in ["company name", "company", "company_name"]:
                company_col = col
            elif col_l in ["location", "job location", "job_location"]:
                location_col = col

        if not company_col or not location_col:
            logger.error(f"Could not find Company and Location columns in '{input_csv}'.")
            return []

        for row in reader:
            company = row.get(company_col, "").strip()
            location = row.get(location_col, "").strip()
            if company and company.lower() != "n/a":
                key = (company.lower(), location.lower())
                if key not in seen:
                    seen.add(key)
                    unique_companies.append({
                        "Company Name": company,
                        "Location": location
                    })

    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".", exist_ok=True)
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Company Name", "Location"])
        writer.writeheader()
        writer.writerows(unique_companies)

    logger.info(f"[+] Extracted {len(unique_companies)} unique companies from '{input_csv}' to '{output_csv}'.")
    return unique_companies


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Usage:
      python find_company_websites.py --extract [input_jobs_csv] [output_companies_csv]
      python find_company_websites.py [input_csv] [output_csv]
    """
    args = sys.argv[1:]

    if len(args) >= 3 and args[0] == "--extract":
        input_csv = args[1]
        output_csv = args[2]
        extract_unique_companies_from_csv(input_csv, output_csv)
        return

    if len(args) == 2:
        input_csv = args[0]
        output_csv = args[1]
    elif len(args) == 1:
        input_csv = args[0]
        output_csv = args[0]
    else:
        # Default behavior: extract from software_engineer_london_uk.csv and find websites
        extracted_csv = "software_engineer_london_companies.csv"
        input_jobs_csv = "software_engineer_london_uk.csv"
        
        if os.path.exists(input_jobs_csv):
            extract_unique_companies_from_csv(input_jobs_csv, extracted_csv)
            find_websites_locally(extracted_csv, "software_engineer_london_companies_with_websites.csv")
        else:
            logger.error(f"Default '{input_jobs_csv}' not found.")
        return

    find_websites_locally(input_csv, output_csv)


if __name__ == "__main__":
    main()
