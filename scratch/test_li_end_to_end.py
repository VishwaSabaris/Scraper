import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from linkedin_scraper import scrape_linkedin_jobs

async def test():
    filter_params = {
        "keywords": "Python Developer Remote",
        "f_WT": "2"
    }
    jobs = await scrape_linkedin_jobs(
        job_role="Python Developer",
        location="",
        filter_params=filter_params,
        headless=True
    )
    print(f"\n[+] Total LinkedIn jobs extracted: {len(jobs)}")
    for j in jobs[:10]:
        print(f"Role: {j['Job Role']}")
        print(f"  Company: {j['Company Name']}")
        print(f"  Location: {j['Location']}")
        print(f"  Apply: {j['Apply Link']}")
        print("-" * 50)
        
    assert all("onsite" not in j["Job Role"].lower() for j in jobs), "Found onsite in job role!"
    print("\n[SUCCESS] LinkedIn remote assertions passed!")

if __name__ == "__main__":
    asyncio.run(test())
