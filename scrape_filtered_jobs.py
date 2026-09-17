import asyncio
import csv
import os
import sys
import datetime
import re

# Import all scrapers from the workspace
from linkedin_scraper import scrape_linkedin_jobs
from indeed_scraper import scrape_indeed_jobs
from wellfound_scraper import scrape_wellfound_jobs
from glassdoor_scraper import scrape_glassdoor_jobs
from ziprecruiter_scraper import scrape_ziprecruiter_jobs
from naukri_scraper import scrape_naukri_jobs
from jobleads_scraper import scrape_jobleads_jobs
from jobspresso_scraper import scrape_jobspresso_jobs
from himalayas_scraper import scrape_himalayas_jobs
from remote_scraper import scrape_remote_jobs
from careerbuilder_scraper import scrape_careerbuilder_jobs
from workable_scraper import scrape_workable_jobs
from jooble_scraper import scrape_jooble_jobs
from workatastartup_scraper import scrape_workatastartup_jobs
from find_company_websites import find_websites_locally
from utils import save_to_csv

def parse_date_posted_to_days(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.lower().strip()
    
    # Direct relative keywords
    if any(x in date_str for x in ["today", "just", "now", "mins", "minute", "second", "active", "hot"]):
        return 0
    if "yesterday" in date_str:
        return 1
        
    # Explicitly over 30 days
    if any(x in date_str for x in ["30+", "30d+", "30d", "30 days+", "over 30", "30+ days ago"]):
        return 999
        
    # Matches short codes like "3d", "4h", "2w"
    short_match = re.match(r'^(\d+)([dhw])$', date_str)
    if short_match:
        val = int(short_match.group(1))
        unit = short_match.group(2)
        if unit == 'd':
            return val
        elif unit == 'w':
            return val * 7
        elif unit == 'h':
            return 0
            
    # ISO formats like YYYY-MM-DD
    iso_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if iso_match:
        try:
            posted_date = datetime.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            today = datetime.date(2026, 8, 11)  # Current local time context date
            delta = today - posted_date
            return max(0, delta.days)
        except Exception:
            pass

    # Extract first number sequence (ignoring word boundaries to match "30d+", "3+weeks", etc.)
    numbers = re.findall(r'\d+', date_str)
    if numbers:
        val = int(numbers[0])
        if "day" in date_str or "d ago" in date_str or "days ago" in date_str or "d" in date_str:
            return val
        elif "week" in date_str or "w ago" in date_str or "weeks ago" in date_str or "w" in date_str:
            return val * 7
        elif "month" in date_str or "months" in date_str:
            return val * 30
        elif "year" in date_str or "years" in date_str:
            return val * 365
        elif "hour" in date_str or "h" in date_str:
            return 0
            
    if "week ago" in date_str or "a week ago" in date_str:
        return 7
    if "month ago" in date_str or "a month ago" in date_str:
        return 30
        
    return None

def parse_applicants_count(app_str):
    if not app_str or not isinstance(app_str, str):
        return None
    app_str = app_str.lower().strip()
    if app_str in ["n/a", "unknown", ""]:
        return None
    
    # LinkedIn default text when detail scrape is skipped or fails
    if "0-25" in app_str:
        return None
        
    if "under 10" in app_str:
        return 9
        
    has_plus = "+" in app_str
    
    numbers = re.findall(r'\b\d+\b', app_str)
    if not numbers:
        return None
        
    val = int(numbers[0])
    if has_plus and val >= 10:
        return 999
        
    return val

def is_remote_job(job):
    source = job.get("Source", "").lower()
    location = job.get("Location", "").lower()
    details = job.get("Company / Job Details", "").lower()
    title = job.get("Job Role", "").lower()
    
    # 1. Source check (remote-only job boards)
    if any(src in source for src in ["himalayas", "remote.com", "jobspresso"]):
        return True
        
    # 2. Location check
    if any(term in location for term in ["remote", "telecommute", "wfh", "work from home", "anywhere", "virtual"]):
        return True
        
    # 3. Title check
    if "remote" in title:
        return True
        
    # 4. Details check
    if any(term in details for term in ["remote", "work from home", "telecommute", "wfh", "virtual work", "work-from-home"]):
        return True
        
    return False

def is_usa_job(job):
    location = job.get("Location", "").lower()
    
    # Check for direct USA indicators
    if any(term in location for term in ["usa", "united states", "u.s.", "us", "america"]):
        return True
        
    # Exclude non-USA countries
    non_us_indicators = ["india", "uk", "united kingdom", "canada", "germany", "australia", "france", "ireland", "singapore", "netherlands", "spain", "italy", "brazil", "mexico"]
    if any(indicator in location for indicator in non_us_indicators):
        return False
        
    # Default to True since we passed USA search filters
    return True

async def run_scrapers():
    role_input = "Business Development"
    location_input = "USA"
    
    print(f"\n[+] Starting scraping job listings for role '{role_input}' in '{location_input}'...")
    
    all_results = []
    
    # 1. LinkedIn
    print("\n=== STARTING LINKEDIN SCRAPER ===")
    try:
        # fetch_details=True is required to get applicant counts
        linkedin_results = await scrape_linkedin_jobs(role_input, location_input, fetch_details=True, headless=False)
        all_results.extend(linkedin_results)
    except Exception as err:
        print(f"[!] LinkedIn scraping interrupted: {err}")
        
    # 2. Indeed
    print("\n=== STARTING INDEED SCRAPER ===")
    try:
        indeed_results = await scrape_indeed_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(indeed_results)
    except Exception as err:
        print(f"[!] Indeed scraping interrupted: {err}")
        
    # 3. Wellfound
    print("\n=== STARTING WELLFOUND SCRAPER ===")
    try:
        wellfound_results = await scrape_wellfound_jobs(role_input, location_input)
        all_results.extend(wellfound_results)
    except Exception as err:
        print(f"[!] Wellfound scraping interrupted: {err}")
        
    # 4. Glassdoor
    print("\n=== STARTING GLASSDOOR SCRAPER ===")
    try:
        glassdoor_results = await scrape_glassdoor_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(glassdoor_results)
    except Exception as err:
        print(f"[!] Glassdoor scraping interrupted: {err}")
        
    # 5. ZipRecruiter
    print("\n=== STARTING ZIPRECRUITER SCRAPER ===")
    try:
        ziprecruiter_results = await scrape_ziprecruiter_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(ziprecruiter_results)
    except Exception as err:
        print(f"[!] ZipRecruiter scraping interrupted: {err}")
        
    # 6. Naukri
    print("\n=== STARTING NAUKRI SCRAPER ===")
    try:
        naukri_results = await scrape_naukri_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(naukri_results)
    except Exception as err:
        print(f"[!] Naukri scraping interrupted: {err}")
        
    # 7. JobLeads
    print("\n=== STARTING JOBLEADS SCRAPER ===")
    try:
        jobleads_results = await scrape_jobleads_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(jobleads_results)
    except Exception as err:
        print(f"[!] JobLeads scraping interrupted: {err}")
        
    # 8. Jobspresso
    print("\n=== STARTING JOBSPRESSO SCRAPER ===")
    try:
        jobspresso_results = await scrape_jobspresso_jobs(role_input, location_input, max_pages=2)
        all_results.extend(jobspresso_results)
    except Exception as err:
        print(f"[!] Jobspresso scraping interrupted: {err}")
        
    # 9. Himalayas
    print("\n=== STARTING HIMALAYAS SCRAPER ===")
    try:
        himalayas_results = await scrape_himalayas_jobs(role_input, location_input, max_pages=2)
        all_results.extend(himalayas_results)
    except Exception as err:
        print(f"[!] Himalayas scraping interrupted: {err}")
        
    # 10. Remote.com
    print("\n=== STARTING REMOTE.COM SCRAPER ===")
    try:
        remote_results = await scrape_remote_jobs(role_input, location_input, max_pages=2)
        all_results.extend(remote_results)
    except Exception as err:
        print(f"[!] Remote.com scraping interrupted: {err}")

    # 11. CareerBuilder
    print("\n=== STARTING CAREERBUILDER SCRAPER ===")
    try:
        careerbuilder_results = await scrape_careerbuilder_jobs(role_input, location_input)
        all_results.extend(careerbuilder_results)
    except Exception as err:
        print(f"[!] CareerBuilder scraping interrupted: {err}")

    # 12. Workable
    print("\n=== STARTING WORKABLE SCRAPER ===")
    try:
        workable_results = await asyncio.to_thread(scrape_workable_jobs, role_input, location_input, 30)
        all_results.extend(workable_results)
    except Exception as err:
        print(f"[!] Workable scraping interrupted: {err}")

    # 13. Jooble
    print("\n=== STARTING JOOBLE SCRAPER ===")
    try:
        jooble_results = await scrape_jooble_jobs(role_input, location_input, max_pages=2, headless=False)
        all_results.extend(jooble_results)
    except Exception as err:
        print(f"[!] Jooble scraping interrupted: {err}")
        
    print(f"\n[+] Total scraped listings across all platforms: {len(all_results)}")
    
    # Save raw jobs
    save_list_to_csv(all_results, "combined_jobs_raw.csv")
    
    # Apply Filtering
    filtered_results = []
    for job in all_results:
        # 1. Location & Remote Filter
        if not is_usa_job(job):
            continue
        if not is_remote_job(job):
            continue
            
        # 2. Date Filter: under 30 days
        date_posted_str = job.get("Date Posted", "N/A")
        days = parse_date_posted_to_days(date_posted_str)
        if days is not None and days >= 30:
            continue
            
        # 3. Applicant Filter: under 10 applicants
        applicants_str = job.get("No. of Applicants", "N/A")
        applicants = parse_applicants_count(applicants_str)
        if applicants is not None and applicants >= 10:
            continue
            
        filtered_results.append(job)
        
    print(f"[+] Total filtered listings matching criteria: {len(filtered_results)}")
    save_to_csv(filtered_results, "combined_jobs_filtered.csv", requested_role="Software Engineer", default_location="Remote")
    print("[+] Resolving company websites locally...")
    find_websites_locally("combined_jobs_filtered.csv", "combined_jobs_filtered.csv")

if __name__ == "__main__":
    asyncio.run(run_scrapers())
