import argparse
import asyncio
import os
import sys
from utils import save_to_csv
from proxy_manager import get_default_proxy_manager
from proxy_refresher import ProxyRefresher

# Import scrapers
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
from workable_scraper import scrape_workable_jobs
from careerbuilder_scraper import scrape_careerbuilder_jobs
from jooble_scraper import scrape_jooble_jobs
from workatastartup_scraper import scrape_workatastartup_jobs
from find_company_websites import find_websites_locally

ALL_PLATFORMS = [
    "linkedin",
    "indeed",
    "glassdoor",
    "workable",
    "wellfound",
    "ziprecruiter",
    "naukri",
    "jobleads",
    "jobspresso",
    "himalayas",
    "remote",
    "reed",
    "careerbuilder",
    "jooble",
    "workatastartup",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Platform Job Scraper & Intelligence Suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Positional args for quick execution: python scraper.py "Software Engineer" "Remote"
    parser.add_argument("role_pos", nargs="?", default=None, help="Job role / keyword (positional)")
    parser.add_argument("location_pos", nargs="?", default=None, help="Location / City / Country (positional)")

    parser.add_argument("-r", "--role", type=str, default=None, help="Target Job Role / Keyword")
    parser.add_argument("-l", "--location", type=str, default=None, help="Target Location (e.g. Remote, USA, London)")
    parser.add_argument(
        "-p",
        "--platforms",
        type=str,
        default="all",
        help=f"Comma-separated list of platforms to scrape or 'all'. Available: {', '.join(ALL_PLATFORMS)}",
    )
    parser.add_argument("-o", "--output", type=str, default="scraped_jobs.csv", help="Output CSV filename")
    parser.add_argument(
        "-d",
        "--details",
        "--fetch-details",
        action="store_true",
        help="Fetch deep LinkedIn job details (descriptions & applicant count)",
    )
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode")
    parser.add_argument("--max-pages", type=int, default=3, help="Max pagination depth per platform")
    parser.add_argument(
        "--no-resolve",
        action="store_true",
        default=False,
        help="Skip automatic company website domain resolution",
    )
    parser.add_argument(
        "--direct",
        "--no-proxy",
        dest="direct",
        action="store_true",
        default=True,
        help="Scrape using direct network connections without proxy delay (recommended)",
    )
    parser.add_argument(
        "--use-proxy",
        dest="use_proxy",
        action="store_true",
        default=False,
        help="Enable proxy rotation from local pool",
    )
    parser.add_argument(
        "--refresh-proxies",
        action="store_true",
        default=False,
        help="Run background proxy refresher service during scraping",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    # Determine job role & location
    role = args.role or args.role_pos
    location = args.location or args.location_pos
    output_file = args.output
    fetch_details = args.details
    headless = args.headless
    max_pages = args.max_pages
    resolve_websites = not args.no_resolve

    # Interactive prompt if no role provided
    if not role:
        print("=" * 60)
        print("       MULTI-PLATFORM JOB SCRAPER SUITE       ")
        print("=" * 60)
        try:
            role = input("[?] Enter Job Role (e.g. Python Developer, Data Analyst): ").strip()
            if not role:
                print("[-] No job role specified. Exiting.")
                return

            loc_in = input("[?] Enter Location (e.g. Remote, USA, London) [Remote]: ").strip()
            location = loc_in if loc_in else "Remote"

            plat_in = input(f"[?] Platforms to scrape (comma-separated or 'all') [all]: ").strip()
            if plat_in:
                args.platforms = plat_in

            deep_in = input("[?] Fetch deep LinkedIn details & applicants? (y/n) [n]: ").strip().lower()
            fetch_details = deep_in == "y"

            out_in = input(f"[?] Output CSV filename [{output_file}]: ").strip()
            if out_in:
                output_file = out_in
        except (KeyboardInterrupt, EOFError):
            print("\n[-] Operation cancelled by user.")
            return

    if not location:
        location = "Remote"

    # Determine target platforms
    plat_str = args.platforms.lower().strip()
    if plat_str == "all":
        selected_platforms = list(ALL_PLATFORMS)
    else:
        selected_platforms = [p.strip() for p in plat_str.split(",") if p.strip() in ALL_PLATFORMS]
        if not selected_platforms:
            print(f"[!] Warning: No recognized platforms in '{plat_str}'. Defaulting to 'all'.")
            selected_platforms = list(ALL_PLATFORMS)

    # Configure Proxy System
    proxy_manager = get_default_proxy_manager()
    if args.use_proxy and not args.direct:
        proxy_manager.enabled = True
        stats = proxy_manager.get_stats()
        print(f"[*] Proxy System: ENABLED | Total Pool: {stats['total']} | Active: {stats['active']}")
    else:
        proxy_manager.enabled = False
        print("[*] Network Mode: DIRECT (Proxies disabled for maximum speed & reliability)")

    # Background Refresher (only if explicitly requested)
    refresher = None
    if args.refresh_proxies:
        print("[*] Starting background proxy refresher thread...")
        refresher = ProxyRefresher(proxy_manager)
        refresher.start()

    print("\n" + "=" * 60)
    print(f"  TARGET ROLE     : {role}")
    print(f"  TARGET LOCATION : {location}")
    print(f"  PLATFORMS       : {', '.join(selected_platforms)}")
    print(f"  OUTPUT CSV      : {output_file}")
    print(f"  HEADLESS MODE   : {headless}")
    print("=" * 60 + "\n")

    all_results = []

    try:
        # 1. LinkedIn
        if "linkedin" in selected_platforms:
            print("\n=== [1/15] STARTING LINKEDIN SCRAPER ===")
            try:
                linkedin_results = await scrape_linkedin_jobs(
                    role, location, fetch_details=fetch_details, headless=headless
                )
                print(f"[+] LinkedIn: Successfully scraped {len(linkedin_results)} listings.")
                all_results.extend(linkedin_results)
            except Exception as err:
                print(f"[!] LinkedIn scraping encountered an issue: {err}")

        # 2. Indeed
        if "indeed" in selected_platforms:
            print("\n=== [2/15] STARTING INDEED SCRAPER ===")
            try:
                indeed_results = await scrape_indeed_jobs(role, location, max_pages=max_pages, headless=headless)
                print(f"[+] Indeed: Successfully scraped {len(indeed_results)} listings.")
                all_results.extend(indeed_results)
            except Exception as err:
                print(f"[!] Indeed scraping encountered an issue: {err}")

        # 3. Glassdoor
        if "glassdoor" in selected_platforms:
            print("\n=== [3/15] STARTING GLASSDOOR SCRAPER ===")
            try:
                glassdoor_results = await scrape_glassdoor_jobs(
                    role, location, max_pages=max_pages, headless=headless
                )
                print(f"[+] Glassdoor: Successfully scraped {len(glassdoor_results)} listings.")
                all_results.extend(glassdoor_results)
            except Exception as err:
                print(f"[!] Glassdoor scraping encountered an issue: {err}")

        # 4. Workable
        if "workable" in selected_platforms:
            print("\n=== [4/15] STARTING WORKABLE SCRAPER ===")
            try:
                workable_results = await asyncio.to_thread(scrape_workable_jobs, role, location, max_pages * 15)
                print(f"[+] Workable: Successfully scraped {len(workable_results)} listings.")
                all_results.extend(workable_results)
            except Exception as err:
                print(f"[!] Workable scraping encountered an issue: {err}")

        # 5. Wellfound
        if "wellfound" in selected_platforms:
            print("\n=== [5/15] STARTING WELLFOUND SCRAPER ===")
            try:
                wellfound_results = await scrape_wellfound_jobs(role, location)
                print(f"[+] Wellfound: Successfully scraped {len(wellfound_results)} listings.")
                all_results.extend(wellfound_results)
            except Exception as err:
                print(f"[!] Wellfound scraping encountered an issue: {err}")

        # 6. ZipRecruiter
        if "ziprecruiter" in selected_platforms:
            print("\n=== [6/15] STARTING ZIPRECRUITER SCRAPER ===")
            try:
                ziprecruiter_results = await scrape_ziprecruiter_jobs(
                    role, location, max_pages=max_pages, headless=headless
                )
                print(f"[+] ZipRecruiter: Successfully scraped {len(ziprecruiter_results)} listings.")
                all_results.extend(ziprecruiter_results)
            except Exception as err:
                print(f"[!] ZipRecruiter scraping encountered an issue: {err}")

        # 7. Naukri
        if "naukri" in selected_platforms:
            print("\n=== [7/15] STARTING NAUKRI SCRAPER ===")
            try:
                naukri_results = await scrape_naukri_jobs(role, location, max_pages=max_pages, headless=headless)
                print(f"[+] Naukri: Successfully scraped {len(naukri_results)} listings.")
                all_results.extend(naukri_results)
            except Exception as err:
                print(f"[!] Naukri scraping encountered an issue: {err}")

        # 8. JobLeads
        if "jobleads" in selected_platforms:
            print("\n=== [8/15] STARTING JOBLEADS SCRAPER ===")
            try:
                jobleads_results = await scrape_jobleads_jobs(role, location, max_pages=max_pages, headless=headless)
                print(f"[+] JobLeads: Successfully scraped {len(jobleads_results)} listings.")
                all_results.extend(jobleads_results)
            except Exception as err:
                print(f"[!] JobLeads scraping encountered an issue: {err}")

        # 9. Jobspresso
        if "jobspresso" in selected_platforms:
            print("\n=== [9/15] STARTING JOBSPRESSO SCRAPER ===")
            try:
                jobspresso_results = await scrape_jobspresso_jobs(role, location, max_pages=max_pages)
                print(f"[+] Jobspresso: Successfully scraped {len(jobspresso_results)} listings.")
                all_results.extend(jobspresso_results)
            except Exception as err:
                print(f"[!] Jobspresso scraping encountered an issue: {err}")

        # 10. Himalayas
        if "himalayas" in selected_platforms:
            print("\n=== [10/15] STARTING HIMALAYAS SCRAPER ===")
            try:
                himalayas_results = await scrape_himalayas_jobs(role, location, max_pages=max_pages)
                print(f"[+] Himalayas: Successfully scraped {len(himalayas_results)} listings.")
                all_results.extend(himalayas_results)
            except Exception as err:
                print(f"[!] Himalayas scraping encountered an issue: {err}")

        # 11. Remote.com
        if "remote" in selected_platforms:
            print("\n=== [11/15] STARTING REMOTE.COM SCRAPER ===")
            try:
                remote_results = await scrape_remote_jobs(role, location, max_pages=max_pages)
                print(f"[+] Remote.com: Successfully scraped {len(remote_results)} listings.")
                all_results.extend(remote_results)
            except Exception as err:
                print(f"[!] Remote.com scraping encountered an issue: {err}")

        # 12. Reed.co.uk
        if "reed" in selected_platforms:
            print("\n=== [12/15] STARTING REED.CO.UK SCRAPER ===")
            try:
                reed_results = await scrape_reed_jobs(role, location)
                print(f"[+] Reed.co.uk: Successfully scraped {len(reed_results)} listings.")
                all_results.extend(reed_results)
            except Exception as err:
                print(f"[!] Reed.co.uk scraping encountered an issue: {err}")

        # 13. CareerBuilder
        if "careerbuilder" in selected_platforms:
            print("\n=== [13/15] STARTING CAREERBUILDER SCRAPER ===")
            try:
                careerbuilder_results = await scrape_careerbuilder_jobs(role, location, headless=headless)
                print(f"[+] CareerBuilder: Successfully scraped {len(careerbuilder_results)} listings.")
                all_results.extend(careerbuilder_results)
            except Exception as err:
                print(f"[!] CareerBuilder scraping encountered an issue: {err}")

        # 14. Jooble
        if "jooble" in selected_platforms:
            print("\n=== [14/15] STARTING JOOBLE SCRAPER ===")
            try:
                jooble_results = await scrape_jooble_jobs(role, location, max_pages=max_pages, headless=headless)
                print(f"[+] Jooble: Successfully scraped {len(jooble_results)} listings.")
                all_results.extend(jooble_results)
            except Exception as err:
                print(f"[!] Jooble scraping encountered an issue: {err}")

        # 15. WorkAtAStartup
        if "workatastartup" in selected_platforms:
            print("\n=== [15/15] STARTING WORKATASTARTUP SCRAPER ===")
            try:
                workatastartup_results = await scrape_workatastartup_jobs(
                    job_role=role, location=location, headless=headless
                )
                print(f"[+] WorkAtAStartup: Successfully scraped {len(workatastartup_results)} listings.")
                all_results.extend(workatastartup_results)
            except Exception as err:
                print(f"[!] WorkAtAStartup scraping encountered an issue: {err}")

        print("\n" + "=" * 60)
        print(f"[+] Scraping complete! Scraped a total of {len(all_results)} job listings.")
        print("=" * 60)

        # Save to CSV
        if all_results:
            save_to_csv(all_results, output_file)

            # Resolve company websites
            if resolve_websites and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print("\n[*] Resolving company websites locally...")
                try:
                    find_websites_locally(output_file, output_file)
                except Exception as err:
                    print(f"[!] Company website resolution encountered an issue: {err}")
        else:
            print("[-] No jobs were found matching your query across the selected platforms.")

    finally:
        if refresher:
            refresher.stop()


if __name__ == "__main__":
    asyncio.run(main())