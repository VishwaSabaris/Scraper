import asyncio
import random
import csv
import os
from typing import Optional, Dict, Any

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

CHROMIUM_STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
    "--ignore-certificate-errors-spki-list",
    "--disable-dev-shm-usage"
]

STEALTH_JS_INIT = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    window.chrome = {
        runtime: {}
    };
"""

def is_role_match(job_title, requested_role):
    """Strictly matches requested job role terms against job titles to prevent irrelevant job listings."""
    if not job_title or job_title == "N/A":
        return False
        
    title_lower = job_title.lower()
    req_lower = requested_role.lower().strip()
    
    # Synonyms dictionary for specific roles
    synonyms = {
        "devops": ["devops", "dev ops", "sre", "site reliability", "cloud engineer", "platform engineer", "infrastructure engineer", "sysadmin"],
        "ml": ["ml", "machine learning", "ai engineer", "ai developer", "deep learning"],
        "machine learning": ["ml", "machine learning", "ai engineer", "ai developer", "deep learning"],
        "data analyst": ["data analyst", "bi analyst", "business intelligence", "data analytics"],
        "data engineer": ["data engineer", "data platform", "etl engineer", "data pipeline"]
    }
    
    for key, syn_list in synonyms.items():
        if key in req_lower:
            if any(syn in title_lower for syn in syn_list):
                return True
                
    # Generic modifier words that shouldn't match alone
    generic_words = {"engineer", "developer", "specialist", "analyst", "lead", "senior", "junior", "manager", "architect", "intern", "staff"}
    specific_terms = [t for t in req_lower.split() if t not in generic_words and len(t) > 1]
    
    if specific_terms:
        # Require at least one specific term (e.g. 'ml', 'devops', 'python', 'react')
        return any(st in title_lower for st in specific_terms)
        
    # Fallback for single generic term
    req_terms = [t for t in req_lower.split() if len(t) > 1]
    return any(term in title_lower for term in req_terms)

async def create_stealth_context(browser, proxy: Optional[Dict[str, str]] = None):
    """Creates a browser context configured with stealth headers, properties, and optional proxy."""
    context_args: Dict[str, Any] = {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": {'width': 1366, 'height': 768},
        "locale": "en-US",
        "extra_http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
    }
    
    if proxy:
        context_args["proxy"] = proxy

    context = await browser.new_context(**context_args)
    await context.add_init_script(STEALTH_JS_INIT)
    return context

async def human_delay(min_sec=2, max_sec=5):
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)

import datetime
import re

def normalize_date_posted(val) -> str:
    """
    Converts epoch timestamps (ms/s), relative dates ('Today', '2d ago', '30+ days ago'), 
    month strings ('1 September'), and non-standard date strings into clean ISO format YYYY-MM-DD.
    """
    if val is None or pd.isna(val) if 'pd' in globals() else False:
        return 'N/A'
        
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['n/a', 'unknown', 'none', 'nan', 'save', 'null']:
        return 'N/A'
    
    # 1. Pure numeric epoch timestamp
    if val_str.isdigit() or (val_str.replace('.', '', 1).isdigit() and '.' in val_str):
        try:
            num = float(val_str)
            if num > 1e11:  # Milliseconds timestamp
                ts = num / 1000.0
            elif num > 1e8:  # Seconds timestamp
                ts = num
            else:
                return 'N/A'
            return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        except Exception:
            return 'N/A'

    # 2. ISO timestamp format: 2026-09-12T... or YYYY-MM-DD
    iso_match = re.match(r'^(\d{4}-\d{2}-\d{2})', val_str)
    if iso_match:
        return iso_match.group(1)

    # 3. Relative date formats
    today = datetime.date(2026, 9, 12)
    lower = val_str.lower()
    
    if any(k in lower for k in ['today', 'just', 'now', 'hour', 'min', 'sec', 'recent', 'few moments', 'active']):
        return today.strftime('%Y-%m-%d')
    if 'yesterday' in lower:
        return (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
    months_match = re.search(r'(\d+)\+?\s*(?:m|month|months)', lower)
    if months_match:
        m = int(months_match.group(1))
        return (today - datetime.timedelta(days=m * 30)).strftime('%Y-%m-%d')

    weeks_match = re.search(r'(\d+)\+?\s*(?:w|week|weeks)', lower)
    if weeks_match:
        w = int(weeks_match.group(1))
        return (today - datetime.timedelta(days=w * 7)).strftime('%Y-%m-%d')

    days_match = re.search(r'(\d+)\+?\s*(?:d|day|days)', lower)
    if days_match:
        d = int(days_match.group(1))
        return (today - datetime.timedelta(days=d)).strftime('%Y-%m-%d')

    # 4. Standard Date formats like DD-Mon-YYYY or DD/MM/YYYY or DD Month
    for fmt in ('%d-%b-%Y', '%d-%m-%Y', '%d/%m/%Y', '%b %d, %Y', '%Y/%m/%d', '%d %B %Y', '%B %d %Y'):
        try:
            dt = datetime.datetime.strptime(val_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    # 5. Formats without year like "1 September" or "September 1"
    for fmt in ('%d %B', '%d %b', '%B %d', '%b %d'):
        try:
            dt = datetime.datetime.strptime(val_str, fmt)
            # Default to current year 2026
            dt = dt.replace(year=2026)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    return 'N/A'

def save_to_csv(data, filename="linkedin_jobs.csv"):
    if not data:
        print("[-] Process completed with no results to write.")
        return
        
    keys = list(data[0].keys())
    existing_links = set()
    existing_rows = []
    
    # Read existing data if the file exists and has size
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, 'r', encoding='utf-8') as input_file:
                reader = csv.DictReader(input_file)
                if reader.fieldnames:
                    # Keep existing records
                    for row in reader:
                        link = row.get("Apply Link", "")
                        if link:
                            existing_links.add(link)
                        # Normalize date in existing row if needed
                        if "Date Posted" in row:
                            row["Date Posted"] = normalize_date_posted(row["Date Posted"])
                        existing_rows.append(row)
        except Exception as err:
            print(f"[!] Error reading existing CSV '{filename}': {err}")
            
    # Filter new data to avoid adding duplicates and normalize dates
    new_records = []
    for item in data:
        link = item.get("Apply Link", "")
        if link not in existing_links:
            clean_item = dict(item)
            if "Date Posted" in clean_item:
                clean_item["Date Posted"] = normalize_date_posted(clean_item["Date Posted"])
            new_records.append(clean_item)
            existing_links.add(link)
            
    print(f"[*] CSV Append check: found {len(new_records)} new unique listings out of {len(data)} scraped.")
    
    if not new_records and existing_rows:
        print(f"[+] All scraped jobs are already present in {filename}. No new records added.")
        return
        
    # Combine old and new records
    all_records = existing_rows + new_records
    
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_records)
        
    print(f"[++++] Complete! Combined dataset ({len(all_records)} total records) updated in {filename}")
