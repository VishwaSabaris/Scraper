import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from linkedin_scraper import scrape_linkedin_jobs

async def test_li():
    t0 = time.time()
    print("Starting LinkedIn scraper test (headless=True)...")
    try:
        jobs = await scrape_linkedin_jobs("Software Engineer", "Bangalore", fetch_details=False, headless=True)
        print(f"LinkedIn finished in {time.time() - t0:.2f}s: Scraped {len(jobs)} jobs")
        if jobs:
            print("Sample:", jobs[0]["Job Role"], jobs[0]["Company Name"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_li())
