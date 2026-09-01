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

def save_to_csv(data, filename="linkedin_jobs.csv"):
    if not data:
        print("[-] Process completed with no results to write.")
        return
        
    keys = data[0].keys()
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
                        # Keep it as dict
                        existing_rows.append(row)
        except Exception as err:
            print(f"[!] Error reading existing CSV '{filename}': {err}")
            
    # Filter new data to avoid adding duplicates
    new_records = []
    for item in data:
        link = item.get("Apply Link", "")
        if link not in existing_links:
            new_records.append(item)
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
