import asyncio
import sys
from utils import save_to_csv
from proxy_manager import get_default_proxy_manager
from proxy_refresher import ProxyRefresher
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
from reed_scraper import scrape_reed_jobs
from find_company_websites import find_websites_locally

async def main():
    proxy_manager = get_default_proxy_manager()
    stats = proxy_manager.get_stats()
    if proxy_manager.enabled:
        print(f"[*] Proxy System: ENABLED | Total Loaded: {stats['total']} | Active: {stats['active']}")
    else:
        print("[*] Proxy System: DISABLED | Running with direct network connections.")

    # Start the background proxy refresher if enabled
    refresher = ProxyRefresher(proxy_manager)
    refresher.start()
    output_file = "linkedin_jobs.csv"
    try:
        if len(sys.argv) >= 3:
            role_input = sys.argv[1]
            location_input = sys.argv[2]
            fetch_details = False
            if len(sys.argv) >= 4:
                fetch_details = sys.argv[3].lower() == 'y'
            if len(sys.argv) >= 5:
                output_file = sys.argv[4]
            print(f"[+] Running with arguments - Role: {role_input}, Location: {location_input}, Deep LinkedIn Scrape: {fetch_details}, Output CSV: {output_file}")
        else:
            role_input = input("Enter Job Role (e.g., Data Analyst): ").strip()
            location_input = input("Enter Location (e.g., New York or London): ").strip()
            fetch_details_input = input("Do you want to scrape full job descriptions and applicant count for LinkedIn? (y/n) [n is recommended]: ").strip().lower()
            fetch_details = fetch_details_input == 'y'
            output_file_input = input("Enter Output CSV filename [linkedin_jobs.csv]: ").strip()
            if output_file_input:
                output_file = output_file_input
            
        all_results = []
        
        print("\n=== STARTING LINKEDIN SCRAPER ===")
        try:
            linkedin_results = await scrape_linkedin_jobs(role_input, location_input, fetch_details=fetch_details)
            all_results.extend(linkedin_results)
        except Exception as err:
            print(f"[!] LinkedIn scraping interrupted: {err}")
            
        print("\n=== STARTING INDEED SCRAPER ===")
        try:
            indeed_results = await scrape_indeed_jobs(role_input, location_input, max_pages=5)
            all_results.extend(indeed_results)
        except Exception as err:
            print(f"[!] Indeed scraping interrupted: {err}")
            
        print("\n=== STARTING WELLFOUND SCRAPER ===")
        try:
            wellfound_results = await scrape_wellfound_jobs(role_input, location_input)
            all_results.extend(wellfound_results)
        except Exception as err:
            print(f"[!] Wellfound scraping interrupted: {err}")
            
        print("\n=== STARTING GLASSDOOR SCRAPER ===")
        try:
            glassdoor_results = await scrape_glassdoor_jobs(role_input, location_input)
            all_results.extend(glassdoor_results)
        except Exception as err:
            print(f"[!] Glassdoor scraping interrupted: {err}")
            
        print("\n=== STARTING ZIPRECRUITER SCRAPER ===")
        try:
            ziprecruiter_results = await scrape_ziprecruiter_jobs(role_input, location_input, max_pages=5)
            all_results.extend(ziprecruiter_results)
        except Exception as err:
            print(f"[!] ZipRecruiter scraping interrupted: {err}")
            
        print("\n=== STARTING NAUKRI SCRAPER ===")
        try:
            naukri_results = await scrape_naukri_jobs(role_input, location_input, max_pages=5)
            all_results.extend(naukri_results)
        except Exception as err:
            print(f"[!] Naukri scraping interrupted: {err}")
            
        print("\n=== STARTING JOBLEADS SCRAPER ===")
        try:
            jobleads_results = await scrape_jobleads_jobs(role_input, location_input)
            all_results.extend(jobleads_results)
        except Exception as err:
            print(f"[!] JobLeads scraping interrupted: {err}")
            
        print("\n=== STARTING JOBSPRESSO SCRAPER ===")
        try:
            jobspresso_results = await scrape_jobspresso_jobs(role_input, location_input, max_pages=5)
            all_results.extend(jobspresso_results)
        except Exception as err:
            print(f"[!] Jobspresso scraping interrupted: {err}")
            
        print("\n=== STARTING HIMALAYAS SCRAPER ===")
        try:
            himalayas_results = await scrape_himalayas_jobs(role_input, location_input, max_pages=5)
            all_results.extend(himalayas_results)
        except Exception as err:
            print(f"[!] Himalayas scraping interrupted: {err}")
            
        print("\n=== STARTING REMOTE.COM SCRAPER ===")
        try:
            remote_results = await scrape_remote_jobs(role_input, location_input, max_pages=5)
            all_results.extend(remote_results)
        except Exception as err:
            print(f"[!] Remote.com scraping interrupted: {err}")
            
        print("\n=== STARTING REED.CO.UK SCRAPER ===")
        try:
            reed_results = await scrape_reed_jobs(role_input, location_input)
            all_results.extend(reed_results)
        except Exception as err:
            print(f"[!] Reed.co.uk scraping interrupted: {err}")

        print(f"\n[+] Scraped a total of {len(all_results)} job listings across all platforms.")
        save_to_csv(all_results, output_file)
        print("[+] Resolving company websites locally...")
        find_websites_locally(output_file, output_file)
    finally:
        refresher.stop()

if __name__ == "__main__":
    asyncio.run(main())