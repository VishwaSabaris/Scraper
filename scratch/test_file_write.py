import os
import shutil

for f in ["all_scraped_jobs_26_portals.csv", "all_scraped_jobs_26_portals_enriched.csv", "all_sdr_26_jobs.csv", "careerbuilder_jobs.csv"]:
    try:
        with open(f, "r+", encoding="utf-8-sig") as fp:
            print(f"Can open {f} for r+ : SUCCESS")
    except Exception as e:
        print(f"Cannot open {f}: {e}")
