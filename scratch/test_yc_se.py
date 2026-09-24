import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from workatastartup_scraper import scrape_workatastartup_jobs

async def test():
    jobs = await scrape_workatastartup_jobs(
        job_role="Software Engineer",
        location="Remote",
        max_scrolls=2,
        headless=True
    )
    print(f"\n[+] Total jobs extracted: {len(jobs)}")
    for j in jobs[:10]:
        print(f"Role: {j['Job Role']}")
        print(f"  Company: {j['Company Name']}")
        print(f"  Location: {j['Location']}")
        print(f"  Apply: {j['Apply Link']}")
        print(f"  Company Link: {j['Company Link']}")
        print("-" * 50)
        
    assert len(jobs) > 0, "No jobs extracted!"
    assert all("General Application" not in j["Job Role"] for j in jobs), "Found General Application fake job!"
    assert all("See all" not in j["Company Name"] for j in jobs), "Found 'See all' in Company Name!"
    assert all("/jobs/" in j["Apply Link"] for j in jobs), "Found non-job apply link!"
    print("\n[SUCCESS] All Work at a Startup assertions passed!")

if __name__ == "__main__":
    asyncio.run(test())
