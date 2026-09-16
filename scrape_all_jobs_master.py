"""
Universal 26-Portal Job Scraper Master Suite
============================================
Integrates and coordinates job scraping across 26 major job portals:
1. Foundit (Monster India)
2. Apna
3. Instahyre
4. Internshala
5. Shine
6. Adzuna
7. Built In
8. Careerjet
9. Dice
10. SimplyHired
11. TimesJobs
12. Freshersworld
13. LinkedIn
14. Naukri
15. CareerBuilder
16. Jooble
17. Reed.co.uk
18. Glassdoor
19. Himalayas
20. Indeed
21. JobLeads
22. Remote.co / Remote.com
23. Wellfound
24. Workable
25. ZipRecruiter
26. Jobspresso

Features:
- Full interactive questionnaire prompt asking for all 26 portal query filters.
- Dynamic Filter Engine: translates supported filters into exact URL/payloads per portal.
- Graceful omission: skips unsupported filters per portal without breaking execution.
- Deep uncapped pagination support across all platforms.
- Universal deduplication and export to standard schema CSV.
"""

import asyncio
import argparse
import sys
import os
import csv
from typing import List, Dict, Any, Optional

# Import the central filter engine
from filter_engine import UniversalJobFilter, FilterEngine, PORTAL_CAPABILITY_MATRIX

# Import all 26 portal scrapers
from foundit_scraper import scrape_foundit_jobs
from apna_scraper import scrape_apna_jobs
from instahyre_scraper import scrape_instahyre_jobs
from internshala_scraper import scrape_internshala_jobs
from shine_scraper import scrape_shine_jobs
from adzuna_scraper import scrape_adzuna_jobs
from builtin_scraper import scrape_builtin_jobs
from careerjet_scraper import scrape_careerjet_jobs
from dice_scraper import scrape_dice_jobs
from simplyhired_scraper import scrape_simplyhired_jobs
from timesjobs_scraper import scrape_timesjobs_jobs
from freshersworld_scraper import scrape_freshersworld_jobs
from linkedin_scraper import scrape_linkedin_jobs
from naukri_scraper import scrape_naukri_jobs
from careerbuilder_scraper import scrape_careerbuilder_jobs
from jooble_scraper import scrape_jooble_jobs
from reed_scraper import scrape_reed_jobs
from glassdoor_scraper import scrape_glassdoor_jobs
from himalayas_scraper import scrape_himalayas_jobs
from indeed_scraper import scrape_indeed_jobs
from jobleads_scraper import scrape_jobleads_jobs
from remote_scraper import scrape_remote_jobs
from wellfound_scraper import scrape_wellfound_jobs
from workable_scraper import scrape_workable_jobs
from workatastartup_scraper import scrape_workatastartup_jobs
from ziprecruiter_scraper import scrape_ziprecruiter_jobs
from jobspresso_scraper import scrape_jobspresso_jobs
from utils import save_to_csv

# Complete Portal Registry
PORTAL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "foundit": {
        "name": "Foundit (Monster India)",
        "func": scrape_foundit_jobs,
        "is_async": True,
        "region": "India / Global",
        "speed": "Fast (API)"
    },
    "apna": {
        "name": "Apna",
        "func": scrape_apna_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (SSR)"
    },
    "instahyre": {
        "name": "Instahyre",
        "func": scrape_instahyre_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (API)"
    },
    "internshala": {
        "name": "Internshala",
        "func": scrape_internshala_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (SSR)"
    },
    "shine": {
        "name": "Shine",
        "func": scrape_shine_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (API)"
    },
    "adzuna": {
        "name": "Adzuna",
        "func": scrape_adzuna_jobs,
        "is_async": True,
        "region": "Global / India",
        "speed": "Fast (SSR)"
    },
    "builtin": {
        "name": "Built In",
        "func": scrape_builtin_jobs,
        "is_async": True,
        "region": "US / Remote",
        "speed": "Fast (SSR)"
    },
    "careerjet": {
        "name": "Careerjet",
        "func": scrape_careerjet_jobs,
        "is_async": True,
        "region": "Global / India",
        "speed": "Browser (Stealth)"
    },
    "dice": {
        "name": "Dice",
        "func": scrape_dice_jobs,
        "is_async": True,
        "region": "US / Tech",
        "speed": "Fast (RSC Stream)"
    },
    "simplyhired": {
        "name": "SimplyHired",
        "func": scrape_simplyhired_jobs,
        "is_async": True,
        "region": "Global / India",
        "speed": "Fast (TLS Impersonation)"
    },
    "timesjobs": {
        "name": "TimesJobs",
        "func": scrape_timesjobs_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (POST API)"
    },
    "freshersworld": {
        "name": "Freshersworld",
        "func": scrape_freshersworld_jobs,
        "is_async": True,
        "region": "India",
        "speed": "Fast (SSR)"
    },
    "linkedin": {
        "name": "LinkedIn",
        "func": scrape_linkedin_jobs,
        "is_async": True,
        "region": "Global",
        "speed": "Browser (Stealth Scroll)"
    },
    "naukri": {
        "name": "Naukri",
        "func": scrape_naukri_jobs,
        "is_async": True,
        "region": "India / Gulf",
        "speed": "Browser (Persistent)"
    },
    "careerbuilder": {
        "name": "CareerBuilder",
        "func": scrape_careerbuilder_jobs,
        "is_async": True,
        "region": "US / Global",
        "speed": "Browser (Persistent)"
    },
    "jooble": {
        "name": "Jooble",
        "func": scrape_jooble_jobs,
        "is_async": True,
        "region": "Global / India",
        "speed": "Browser (Persistent)"
    },
    "reed": {
        "name": "Reed.co.uk",
        "func": scrape_reed_jobs,
        "is_async": True,
        "region": "UK / Global",
        "speed": "Fast (Async HTTP)"
    },
    "glassdoor": {
        "name": "Glassdoor",
        "func": scrape_glassdoor_jobs,
        "is_async": True,
        "region": "Global",
        "speed": "Browser (Persistent)"
    },
    "himalayas": {
        "name": "Himalayas",
        "func": scrape_himalayas_jobs,
        "is_async": True,
        "region": "Remote / Worldwide",
        "speed": "Fast (Public API)"
    },
    "indeed": {
        "name": "Indeed",
        "func": scrape_indeed_jobs,
        "is_async": True,
        "region": "Global",
        "speed": "Browser (Stealth)"
    },
    "jobleads": {
        "name": "JobLeads",
        "func": scrape_jobleads_jobs,
        "is_async": True,
        "region": "US / Europe / Global",
        "speed": "Browser (Persistent)"
    },
    "remote_co": {
        "name": "Remote.com",
        "func": scrape_remote_jobs,
        "is_async": True,
        "region": "Remote / Worldwide",
        "speed": "Fast (Next.js Data)"
    },
    "wellfound": {
        "name": "Wellfound (AngelList)",
        "func": scrape_wellfound_jobs,
        "is_async": True,
        "region": "Startups / Global",
        "speed": "Browser (Direct Search)"
    },
    "workable": {
        "name": "Workable",
        "func": scrape_workable_jobs,
        "is_async": False,
        "region": "Global",
        "speed": "Fast (API)"
    },
    "workatastartup": {
        "name": "Work at a Startup (YC)",
        "func": scrape_workatastartup_jobs,
        "is_async": True,
        "region": "Startups / Global",
        "speed": "Browser (Persistent)"
    },
    "ziprecruiter": {
        "name": "ZipRecruiter",
        "func": scrape_ziprecruiter_jobs,
        "is_async": True,
        "region": "US / India / Global",
        "speed": "Browser (Persistent)"
    },
    "jobspresso": {
        "name": "Jobspresso",
        "func": scrape_jobspresso_jobs,
        "is_async": True,
        "region": "Remote",
        "speed": "Fast (Feed)"
    }
}

INDIAN_PORTALS = ["foundit", "apna", "instahyre", "internshala", "shine", "adzuna", "timesjobs", "freshersworld", "naukri", "jooble"]
GLOBAL_PORTALS = ["linkedin", "indeed", "glassdoor", "careerjet", "dice", "simplyhired", "builtin", "reed", "himalayas", "jobleads", "remote_co", "wellfound", "workable", "workatastartup", "ziprecruiter", "careerbuilder", "jobspresso"]


def prompt_user_filters() -> UniversalJobFilter:
    """
    Displays an interactive CLI questionnaire asking the user for all portal filter options.
    """
    print("\n" + "=" * 70)
    print("      UNIVERSAL 26-PORTAL JOB SCRAPER - QUERY FILTER SETUP")
    print("=" * 70)
    print("Press Enter to keep default suggestions in brackets.\n")

    uf = UniversalJobFilter()

    # 1. Role / Keywords
    role_input = input("[1/13] Job Title / Keywords [Python Developer]: ").strip()
    uf.job_title = role_input or "Python Developer"
    uf.keywords = uf.job_title

    # 2. Location
    loc_input = input("[2/13] Target Location / City / Remote [Bangalore]: ").strip()
    uf.location = loc_input or "Bangalore"

    # 3. Work Mode
    print("\n  Work Modes: (1) All, (2) Remote / WFH, (3) Hybrid, (4) On-Site / Office")
    wm_choice = input("  Select Work Mode [1]: ").strip()
    if wm_choice == "2":
        uf.work_mode = "remote"
    elif wm_choice == "3":
        uf.work_mode = "hybrid"
    elif wm_choice == "4":
        uf.work_mode = "wfo"
    else:
        uf.work_mode = ""

    # 4. Experience Level
    print("\n  Experience Levels: (1) Any, (2) Fresher / Entry (0-2 yrs), (3) Mid (3-5 yrs), (4) Senior (6-8 yrs), (5) Lead / Exec (8+ yrs)")
    exp_choice = input("  Select Experience Level [1]: ").strip()
    if exp_choice == "2":
        uf.experience_min = 0
        uf.experience_max = 2
        uf.experience_level = "entry"
    elif exp_choice == "3":
        uf.experience_min = 3
        uf.experience_max = 5
        uf.experience_level = "mid"
    elif exp_choice == "4":
        uf.experience_min = 6
        uf.experience_max = 8
        uf.experience_level = "senior"
    elif exp_choice == "5":
        uf.experience_min = 8
        uf.experience_max = 25
        uf.experience_level = "lead"

    # 5. Salary Min
    sal_input = input("\n[5/13] Minimum Salary (e.g. 500000 INR or 80000 USD) [Any]: ").strip()
    if sal_input.isdigit():
        uf.salary_min = int(sal_input)

    # 6. Freshness / Date Posted
    print("\n  Date Posted / Freshness: (1) Any Time, (2) Past 24 Hours, (3) Past 7 Days, (4) Past 14 Days, (5) Past 30 Days")
    fresh_choice = input("  Select Freshness [1]: ").strip()
    if fresh_choice == "2":
        uf.date_posted_days = 1
    elif fresh_choice == "3":
        uf.date_posted_days = 7
    elif fresh_choice == "4":
        uf.date_posted_days = 14
    elif fresh_choice == "5":
        uf.date_posted_days = 30

    # 7. Job Type
    print("\n  Job Type: (1) All, (2) Full-time, (3) Part-time, (4) Contract, (5) Internship")
    jt_choice = input("  Select Job Type [1]: ").strip()
    if jt_choice == "2":
        uf.job_type = "full_time"
    elif jt_choice == "3":
        uf.job_type = "part_time"
    elif jt_choice == "4":
        uf.job_type = "contract"
    elif jt_choice == "5":
        uf.job_type = "internship"

    # 8. Skills / Tags
    skills_input = input("\n[8/13] Specific Skills / Tags (e.g. Django, AWS, React) [Optional]: ").strip()
    if skills_input:
        uf.skills = skills_input

    # 9. Company Specific
    comp_input = input("[9/13] Specific Company Name [Optional]: ").strip()
    if comp_input:
        uf.company = comp_input

    # 10. Industry / Department
    dept_input = input("[10/13] Department / Category / Functional Area [Optional]: ").strip()
    if dept_input:
        uf.department = dept_input
        uf.category = dept_input

    # 11. Education
    edu_input = input("[11/13] Education / Qualification (e.g. BE/B.Tech, Any) [Optional]: ").strip()
    if edu_input:
        uf.education = edu_input

    # 12. Distance / Radius
    dist_input = input("[12/13] Distance Radius in KM (e.g. 25, 50) [Optional]: ").strip()
    if dist_input.isdigit():
        uf.distance_km = int(dist_input)

    # 13. Sort Order
    sort_choice = input("\n[13/13] Sort By: (1) Relevance, (2) Date Posted [1]: ").strip()
    if sort_choice == "2":
        uf.sort_by = "date"
    else:
        uf.sort_by = "relevance"

    return uf


def display_portal_filter_matrix(target_portals: List[str], uf: UniversalJobFilter):
    """
    Displays a transparent summary of how input filters map to each portal.
    """
    print("\n" + "=" * 80)
    print(f"  PORTAL FILTER ADAPTATION & CAPABILITY MATRIX ({len(target_portals)} Portals)")
    print("=" * 80)

    for pkey in target_portals:
        pinfo = PORTAL_REGISTRY.get(pkey, {"name": pkey})
        pname = pinfo.get("name", pkey)
        params, applied, omitted = FilterEngine.adapt_for_portal(pkey, uf)
        
        print(f"\n[{pname.upper()}]")
        print(f"  * Status       : Ready")
        print(f"  * Region       : {pinfo.get('region', 'Global')} | Engine: {pinfo.get('speed', 'Fast')}")
        
        if applied:
            print(f"  * APPLIED ({len(applied)}) : " + ", ".join(applied))
        else:
            print(f"  * APPLIED      : Base Role & Location Query")
            
        if omitted:
            print(f"  * OMITTED ({len(omitted)}) : " + ", ".join(omitted) + " (Gracefully skipped - not natively supported)")
            
    print("\n" + "=" * 80 + "\n")


async def execute_portal_scraper(pkey: str, pinfo: Dict[str, Any], uf: UniversalJobFilter, max_pages: int) -> List[Dict[str, Any]]:
    """
    Executes a single portal scraper safely with adapted filter parameters and pagination.
    """
    pname = pinfo["name"]
    func = pinfo["func"]
    is_async = pinfo.get("is_async", True)

    portal_params, applied, omitted = FilterEngine.adapt_for_portal(pkey, uf)
    effective_role = FilterEngine.get_effective_role(uf)
    effective_loc = uf.location or ""

    print(f"\n{'='*20} [{pname.upper()}] STARTING EXTRACTION {'='*20}")
    print(f"[*] Role: '{effective_role}' | Location: '{effective_loc or 'Any'}' | Max Pages: {max_pages}")
    
    try:
        if is_async:
            results = await func(effective_role, effective_loc, max_pages=max_pages, filter_params=portal_params, headless=True)
        else:
            # Synchronous function wrapper
            results = await asyncio.to_thread(func, effective_role, effective_loc, max_jobs=max_pages * 25, filter_params=portal_params)

        return results
    except Exception as err:
        print(f"[!] [{pname}] Scraper encountered an error: {err}")
        return []


async def run_master_scraper(target_portals: List[str], uf: UniversalJobFilter, max_pages: int, output_file: str):
    """
    Orchestrates the entire scraping workflow across all selected portals.
    """
    display_portal_filter_matrix(target_portals, uf)

    all_scraped_jobs = []
    portal_counts = {}

    for idx, pkey in enumerate(target_portals, 1):
        if pkey not in PORTAL_REGISTRY:
            print(f"[!] Unknown portal key: '{pkey}'. Skipping.")
            continue

        pinfo = PORTAL_REGISTRY[pkey]
        jobs = await execute_portal_scraper(pkey, pinfo, uf, max_pages)
        portal_counts[pinfo["name"]] = {
            "count": len(jobs),
            "region": pinfo.get("region", "Global"),
            "status": "[OK] COMPLETED" if len(jobs) > 0 else "[--] ZERO LISTINGS"
        }
        all_scraped_jobs.extend(jobs)

    # ─────────────────────────────────────────────────────────────
    # ELEGANT DETERMINISTIC TERMINAL SUMMARY TABLE
    # ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 88)
    print("                    UNIVERSAL JOB SCRAPING RESULTS SUMMARY")
    print("=" * 88)
    print(f" {'#':<3} {'Portal Name':<28} {'Region / Scope':<22} {'Status':<16} {'Jobs Scraped':>12}")
    print("-" * 88)
    
    for idx, (pname, stats) in enumerate(portal_counts.items(), 1):
        print(f" {idx:<3} {pname:<28} {stats['region']:<22} {stats['status']:<16} {stats['count']:>12}")
        
    print("-" * 88)
    print(f"  * TOTAL RAW LISTINGS SCRAPED     : {len(all_scraped_jobs):>6} jobs")

    # Deduplication based on Apply Link / Role + Company
    seen_keys = set()
    unique_jobs = []
    for job in all_scraped_jobs:
        apply_link = job.get("Apply Link", "").strip()
        role = job.get("Job Role", "").strip().lower()
        company = job.get("Company Name", "").strip().lower()
        
        dedup_key = apply_link if (apply_link and apply_link != "N/A") else f"{role}|{company}"
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            unique_jobs.append(job)

    print(f"  * TOTAL UNIQUE DEDUPLICATED JOBS : {len(unique_jobs):>6} jobs")
    print("=" * 88 + "\n")

    if unique_jobs:
        save_to_csv(unique_jobs, output_file)
        print(f"[++++] Success! Saved {len(unique_jobs)} verified job records to '{output_file}'")
        
        # 1. Automatic Job Description Enrichment
        print(f"\n[*] Launching Universal Job Description Enricher for '{output_file}'...")
        try:
            from enrich_job_descriptions import enrich_job_csv
            enrich_job_csv(output_file)
        except Exception as e:
            print(f"[!] Job description enrichment notice: {e}")

        # 2. Automatic Company Website Resolution & Date Normalization
        print(f"\n[*] Launching Company Website Finder for '{output_file}'...")
        try:
            from resolve_company_websites import process_job_csv
            process_job_csv(output_file)
        except Exception as e:
            print(f"[!] Company Website resolution notice: {e}")
    else:
        print("[-] No matching job records were extracted to save.")


def parse_cli_args():
    parser = argparse.ArgumentParser(description="Universal 26-Portal Job Scraper Master Suite")
    
    # Query parameters
    parser.add_argument("--role", "-r", default="", help="Job role / keywords (e.g. 'Python Developer')")
    parser.add_argument("--location", "-l", default="", help="Location / City / Country (e.g. 'Bangalore')")
    parser.add_argument("--work-mode", "-w", default="", choices=["remote", "hybrid", "wfo", "all", ""], help="Work mode filter")
    parser.add_argument("--experience", "-e", type=int, default=None, help="Experience in years (e.g. 2)")
    parser.add_argument("--experience-level", default="", choices=["entry", "mid", "senior", "lead", ""], help="Experience seniority level")
    parser.add_argument("--salary-min", "-s", type=int, default=None, help="Minimum salary")
    parser.add_argument("--salary-max", type=int, default=None, help="Maximum salary")
    parser.add_argument("--freshness", "-f", type=int, default=None, choices=[1, 3, 7, 14, 15, 30], help="Date posted freshness in days")
    parser.add_argument("--job-type", "-j", default="", choices=["full_time", "part_time", "contract", "internship", ""], help="Job employment type")
    parser.add_argument("--skills", default="", help="Skills or tags (e.g. 'Django, React')")
    parser.add_argument("--company", default="", help="Specific company name")
    parser.add_argument("--department", default="", help="Department or functional area")
    parser.add_argument("--education", default="", help="Education degree qualification")
    parser.add_argument("--distance", type=int, default=None, help="Distance radius in km")
    parser.add_argument("--sort", default="relevance", choices=["relevance", "date", "salary"], help="Sort order")
    
    # Execution options
    parser.add_argument("--portals", "-p", default="all", help="Target portals: 'all', 'indian', 'global', or comma-separated list")
    parser.add_argument("--pages", "-n", type=int, default=3, help="Max pages per portal (default: 3)")
    parser.add_argument("--output", "-o", default="all_jobs_master_extracted.csv", help="Output CSV filename")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive filter setup questionnaire")

    return parser.parse_args()


def main():
    args = parse_cli_args()

    # Determine if we should run interactive prompt
    if args.interactive or (not args.role and len(sys.argv) == 1):
        uf = prompt_user_filters()
        print("\n  Target Portals: (1) All 26 Portals, (2) Indian Portals (10), (3) Global Portals (16), (4) Custom")
        portal_choice = input("  Select Target Portals [1]: ").strip()
        if portal_choice == "2":
            target_portals = INDIAN_PORTALS
        elif portal_choice == "3":
            target_portals = GLOBAL_PORTALS
        elif portal_choice == "4":
            custom_input = input("  Enter comma-separated portal names (e.g. foundit, apna, shine, dice): ").strip()
            target_portals = [p.strip().lower() for p in custom_input.split(",") if p.strip().lower() in PORTAL_REGISTRY]
            if not target_portals:
                target_portals = list(PORTAL_REGISTRY.keys())
        else:
            target_portals = list(PORTAL_REGISTRY.keys())

        pages_input = input("\n  Max Pages to scrape per portal [3]: ").strip()
        max_pages = int(pages_input) if pages_input.isdigit() else 3

        out_input = input("  Output CSV Filename [all_jobs_master_extracted.csv]: ").strip()
        output_file = out_input or "all_jobs_master_extracted.csv"
    else:
        # CLI Mode
        uf = UniversalJobFilter(
            keywords=args.role or "Python Developer",
            job_title=args.role or "Python Developer",
            location=args.location or "Bangalore",
            work_mode=args.work_mode,
            experience_min=args.experience,
            experience_level=args.experience_level,
            salary_min=args.salary_min,
            salary_max=args.salary_max,
            date_posted_days=args.freshness,
            job_type=args.job_type,
            skills=args.skills,
            company=args.company,
            department=args.department,
            category=args.department,
            education=args.education,
            distance_km=args.distance,
            sort_by=args.sort
        )

        p_arg = args.portals.lower().strip()
        if p_arg == "all":
            target_portals = list(PORTAL_REGISTRY.keys())
        elif p_arg == "indian":
            target_portals = INDIAN_PORTALS
        elif p_arg == "global":
            target_portals = GLOBAL_PORTALS
        else:
            target_portals = [p.strip() for p in p_arg.split(",") if p.strip() in PORTAL_REGISTRY]
            if not target_portals:
                target_portals = list(PORTAL_REGISTRY.keys())

        max_pages = args.pages
        output_file = args.output

    # Run the Master Scraper Engine
    asyncio.run(run_master_scraper(target_portals, uf, max_pages, output_file))


if __name__ == "__main__":
    main()
