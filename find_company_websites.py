"""
Company Website Finder Utility (DDGS Engine + Caching)
=====================================================
1. Reads company names & locations from a job CSV or extracted company CSV.
2. Resolves official company website URLs using DuckDuckGo Search (ddgs).
3. Automatically caches results in data/company_websites.csv so queries are never duplicated.
4. Enriches 'Company Link' or 'Website' column in output datasets.
"""

import os
import sys
import logging
from find_company_websites_ddgs import (
    enrich_dataset_with_company_websites,
    clean_company_name,
    is_valid_company_url,
    search_company_website_ddgs
)

# ── Logging Configuration ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CompanyWebsiteFinder")


def main():
    """
    Usage:
      python find_company_websites.py [input_csv] [output_csv]
      python find_company_websites.py --all
    """
    args = sys.argv[1:]

    if not args:
        # Default target
        target = "all_scraped_jobs_26_portals.csv"
        if os.path.exists(target):
            enrich_dataset_with_company_websites(target)
        else:
            logger.error(f"Target '{target}' not found.")
        return

    if args[0] == "--all":
        candidates = [
            "all_scraped_jobs_26_portals.csv",
            "all_sdr_26_jobs.csv",
            "all_jobs_vvs.csv",
            "final_verified_job_dataset.csv"
        ]
        for c in candidates:
            if os.path.exists(c):
                enrich_dataset_with_company_websites(c)
        return

    if len(args) == 2:
        enrich_dataset_with_company_websites(args[0], args[1])
    elif len(args) == 1:
        enrich_dataset_with_company_websites(args[0], args[0])


if __name__ == "__main__":
    main()
