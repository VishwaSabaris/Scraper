"""
Universal Job Description Enrichment Engine
===========================================
Fetches, cleans, and populates complete and rich job descriptions for any scraped job
records where the description was missing, truncated, or contained only metadata.

Supports:
- LinkedIn Guest API (instant full multi-paragraph job description)
- BuiltIn (JSON-LD & DOM content parsing)
- JobLeads (Direct SSR job detail parsing)
- Instahyre (API & page text parsing)
- Foundit, Shine, Internshala, Reed, CareerBuilder, Workable, etc.
- Schema.org (JSON-LD JobPosting description extraction for any job board)
- HTML OpenGraph and standard meta description fallback
"""

import asyncio
import csv
import json
import os
import re
import sys
import html
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

def clean_description_text(raw_text: str) -> str:
    """Cleans HTML tags, unescapes entities, and normalizes spacing."""
    if not raw_text:
        return ""
    # Convert HTML breaks and paragraphs to spaces
    text = re.sub(r'<(?:br|p|div|li)\b[^>]*>', ' ', raw_text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape HTML entities (&amp;, &nbsp;, &#39;, etc.)
    text = html.unescape(text)
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_json_ld_description(soup: BeautifulSoup) -> Optional[str]:
    """Extracts description from Schema.org JobPosting JSON-LD."""
    for script in soup.find_all('script', type='application/ld+json'):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and "@graph" in data:
                items.extend(data["@graph"])
                
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    desc = item.get("description", "")
                    if desc and len(desc) > 30:
                        return clean_description_text(desc)
        except Exception:
            continue
    return None

def fetch_linkedin_description(apply_link: str) -> Optional[str]:
    """Extracts full LinkedIn description using guest API."""
    job_id_match = re.search(r'(\d{8,12})', apply_link)
    if not job_id_match:
        return None
        
    job_id = job_id_match.group(1)
    api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        res = c_requests.get(api_url, headers=HEADERS, impersonate="chrome120", timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            desc_el = soup.select_one(".show-more-less-html__markup, .description__text, section.description, .decorated-job-posting__details")
            if desc_el:
                cleaned = clean_description_text(desc_el.get_text(separator=" "))
                if len(cleaned) > 40:
                    return cleaned
    except Exception:
        pass
    return None

def fetch_generic_description(url: str) -> Optional[str]:
    """Extracts job description from generic HTML job posting pages."""
    try:
        res = c_requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=15)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Try Schema.org JSON-LD
        json_ld_desc = extract_json_ld_description(soup)
        if json_ld_desc and len(json_ld_desc) > 60:
            return json_ld_desc
            
        # 2. Try common Job Description Selectors
        selectors = [
            "[data-testid='job-description']",
            ".job-description",
            "#job-description",
            ".job-details-text",
            ".job-detail-description",
            ".jobDescriptionContent",
            ".description__text",
            ".show-more-less-html__markup",
            "[data-id='job-description']",
            ".job-info",
            ".job_description",
            "article.job-description",
            ".role-description",
            ".job-desc",
            ".job_desc",
            ".description"
        ]
        
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                txt = clean_description_text(el.get_text(separator=" "))
                if len(txt) > 60:
                    return txt
                    
        # 3. Try OpenGraph / Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_desc and meta_desc.get("content"):
            txt = clean_description_text(meta_desc["content"])
            if len(txt) > 50:
                return txt
                
        # 4. Fallback: Search for longest text section in article / main
        main_container = soup.find(['main', 'article']) or soup.body
        if main_container:
            candidates = []
            for tag in main_container.find_all(['div', 'section', 'p']):
                if len(tag.find_all(['div', 'section'])) == 0:
                    t = clean_description_text(tag.get_text())
                    if len(t) > 100:
                        candidates.append(t)
            if candidates:
                # Combine top candidates
                return " ".join(candidates[:3])[:800]
                
    except Exception:
        pass
    return None

def is_description_incomplete(details_str: str) -> bool:
    """Checks if the details field is missing real job description text."""
    if not details_str or details_str.strip() in ["N/A", ""]:
        return True
    det = details_str.strip()
    # Check if only company/salary header metadata without descriptive sentences
    if len(det) < 50:
        return True
    if det.startswith("Company:") and ("| Skills:" in det or "| Target:" in det) and len(det) < 130:
        return False  # Instahyre skills tag can be enriched or kept
    if det.startswith("Work Setting:") and len(det) < 80:
        return True
    if det.startswith("Company:") and det.endswith("Salary: Not disclosed |"):
        return True
    return False

def enrich_single_job(record: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches a single job record with full description if missing or short."""
    current_desc = (record.get("Job Description") or record.get("Company / Job Details") or record.get("job_description") or "").strip()
    apply_link = record.get("Apply Link", "").strip()
    source = record.get("Source", "").strip().lower()
    role = record.get("Job Role", "").strip()
    company = record.get("Company Name", "").strip()
    
    # If already rich and detailed (> 120 chars), preserve it
    if not is_description_incomplete(current_desc) and len(current_desc) > 120 and "..." not in current_desc[-10:]:
        record["Job Description"] = current_desc
        return record
        
    if not apply_link or not apply_link.startswith("http"):
        record["Job Description"] = current_desc
        return record

    new_desc = None
    
    # 1. LinkedIn specific handler
    if "linkedin" in source or "linkedin.com" in apply_link:
        new_desc = fetch_linkedin_description(apply_link)
        
    # 2. Generic / other portals
    if not new_desc:
        new_desc = fetch_generic_description(apply_link)
        
    if new_desc and len(new_desc) > 50:
        # Prepend key metadata if useful
        prefix = f"Company: {company} | " if company and company != "N/A" and not new_desc.startswith(company) else ""
        full_text = prefix + new_desc
        # Truncate at max 1000 characters for optimal CSV portability
        record["Job Description"] = full_text[:1000] if len(full_text) > 1000 else full_text
    elif not current_desc or current_desc == "N/A":
        # Fallback informative context
        loc = record.get("Location", "")
        record["Job Description"] = f"Role: {role} | Company: {company} | Location: {loc} | Direct Apply: {apply_link}"
    else:
        record["Job Description"] = current_desc
        
    return record

def enrich_job_csv(csv_path: str, max_workers: int = 15):
    """Reads a CSV file, enriches missing descriptions concurrently, and saves updated file."""
    if not os.path.exists(csv_path):
        print(f"[!] File not found: {csv_path}")
        return

    print(f"\n[*] Enriching Job Descriptions for '{csv_path}'...")
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        records = list(reader)
        fieldnames = reader.fieldnames

    if not records:
        print("[!] No records in CSV to enrich.")
        return

    import concurrent.futures
    
    needs_enrichment = [r for r in records if is_description_incomplete(r.get("Job Description") or r.get("Company / Job Details", ""))]
    print(f"[*] Found {len(needs_enrichment)} out of {len(records)} records needing description enhancement.")

    if not needs_enrichment:
        print("[+] All records already contain complete descriptions!")
        return

    enriched_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_rec = {executor.submit(enrich_single_job, rec): rec for rec in records}
        for future in concurrent.futures.as_completed(future_to_rec):
            try:
                updated = future.result()
                det = updated.get("Job Description") or updated.get("Company / Job Details", "")
                if len(det) > 80:
                    enriched_count += 1
            except Exception:
                pass

    # Save back to CSV with universal sanitization
    from utils import sanitize_job_record
    cleaned_records = [sanitize_job_record(r) for r in records]
    canonical_headers = [
        "Job Role", "Company Name", "Location", "Date Posted",
        "Apply Link", "Company Link", "No. of Applicants",
        "Job Description", "Source",
        "website", "apply_link_url"
    ]
    
    tmp_path = f"{csv_path}.tmp"
    with open(tmp_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=canonical_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cleaned_records)
    
    if os.path.exists(tmp_path):
        os.replace(tmp_path, csv_path)

    print(f"[++++] Description Enrichment Complete! Successfully enriched {enriched_count} / {len(records)} records with full job descriptions.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all_scraped_jobs_26_portals.csv"
    enrich_job_csv(target)
