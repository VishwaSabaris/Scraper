"""
Master Multi-Portal Job Scraper Runner
======================================
Coordinates and runs scrapers across 12 job portals:
1. Foundit (Monster India)
2. Apna
3. Instahyre
4. Internshala
5. Shine
6. Adzuna
7. BuiltIn
8. Careerjet
9. Dice
10. SimplyHired
11. TimesJobs
12. Freshersworld

Usage:
    python scrape_new_portals.py --role "Python Developer" --location "Bangalore" --pages 1
    python scrape_new_portals.py --portal foundit --role "Data Engineer"
    python scrape_new_portals.py --portal dice --role "DevOps" --location "Remote"
"""

import asyncio
import argparse
import sys
import os
import csv
from typing import List, Dict, Any

# Import all 12 portal scrapers
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
from utils import save_to_csv

PORTAL_MAP = {
    "foundit": ("Foundit", scrape_foundit_jobs),
    "apna": ("Apna", scrape_apna_jobs),
    "instahyre": ("Instahyre", scrape_instahyre_jobs),
    "internshala": ("Internshala", scrape_internshala_jobs),
    "shine": ("Shine", scrape_shine_jobs),
    "adzuna": ("Adzuna", scrape_adzuna_jobs),
    "builtin": ("BuiltIn", scrape_builtin_jobs),
    "careerjet": ("Careerjet", scrape_careerjet_jobs),
    "dice": ("Dice", scrape_dice_jobs),
    "simplyhired": ("SimplyHired", scrape_simplyhired_jobs),
    "timesjobs": ("TimesJobs", scrape_timesjobs_jobs),
    "freshersworld": ("Freshersworld", scrape_freshersworld_jobs),
}

async def run_single_portal(portal_key: str, role: str, location: str, max_pages: int) -> List[Dict[str, Any]]:
    if portal_key not in PORTAL_MAP:
        print(f"[!] Unknown portal: '{portal_key}'. Available: {list(PORTAL_MAP.keys())}")
        return []
        
    name, scraper_fn = PORTAL_MAP[portal_key]
    print(f"\n{'='*20} RUNNING {name.upper()} SCRAPER {'='*20}")
    try:
        results = await scraper_fn(role, location, max_pages=max_pages)
        print(f"[+] {name} returned {len(results)} jobs.")
        return results
    except Exception as err:
        print(f"[!] {name} scraper encountered an error: {err}")
        return []

async def run_all_portals(role: str, location: str, max_pages: int) -> List[Dict[str, Any]]:
    print(f"\n{'='*25} LAUNCHING 12-PORTAL AGGREGATOR {'='*25}")
    print(f"[*] Target Role:     '{role}'")
    print(f"[*] Target Location: '{location or 'Any'}'")
    print(f"[*] Max Pages/Site:  {max_pages}\n")
    
    all_results = []
    portal_counts = {}
    
    for key, (name, scraper_fn) in PORTAL_MAP.items():
        print(f"\n>>> [{name}] Starting extraction...")
        try:
            results = await scraper_fn(role, location, max_pages=max_pages)
            portal_counts[name] = len(results)
            all_results.extend(results)
        except Exception as err:
            print(f"[!] [{name}] Error during run: {err}")
            portal_counts[name] = 0
            
    print(f"\n{'='*25} EXTRACTION SUMMARY {'='*25}")
    for name, count in portal_counts.items():
        print(f"  * {name:<15}: {count:>4} jobs")
    print(f"{'-'*45}")
    print(f"  * TOTAL SCRAPED : {len(all_results):>4} jobs\n")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Multi-Portal Job Scraper Suite (12 Portals)")
    parser.add_argument("--portal", "-p", default="all", choices=["all"] + list(PORTAL_MAP.keys()), help="Target job portal to scrape (default: all)")
    parser.add_argument("--role", "-r", default="Python Developer", help="Job role or keywords (default: 'Python Developer')")
    parser.add_argument("--location", "-l", default="Bangalore", help="Location / City / Remote (default: 'Bangalore')")
    parser.add_argument("--pages", "-n", type=int, default=1, help="Max pages per portal (default: 1)")
    parser.add_argument("--output", "-o", default="", help="Output CSV filename (default: auto-named)")
    
    args = parser.parse_args()
    
    if args.portal == "all":
        results = asyncio.run(run_all_portals(args.role, args.location, args.pages))
        out_file = args.output or "combined_12_portals_jobs.csv"
    else:
        results = asyncio.run(run_single_portal(args.portal, args.role, args.location, args.pages))
        out_file = args.output or f"{args.portal}_jobs.csv"
        
    if results:
        save_to_csv(results, out_file)
        print(f"\n[++++] Successfully saved {len(results)} jobs to '{out_file}'!")
    else:
        print("\n[-] No matching jobs found to save.")

if __name__ == "__main__":
    main()
