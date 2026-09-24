import sys
import os
import asyncio
import traceback

sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY

async def test_portal(name, portal_info):
    func = portal_info["func"]
    is_async = portal_info["is_async"]
    print(f"\n---> Testing {name} ({portal_info['name']})...")
    try:
        if is_async:
            # Most scrapers take (job_title, location) or (role, location, max_pages)
            try:
                res = await asyncio.wait_for(func("Software Engineer", "Bangalore", max_pages=1), timeout=25.0)
            except TypeError:
                try:
                    res = await asyncio.wait_for(func("Software Engineer", "Bangalore"), timeout=25.0)
                except TypeError:
                    res = await asyncio.wait_for(func("Software Engineer"), timeout=25.0)
        else:
            try:
                res = func("Software Engineer", "Bangalore", max_pages=1)
            except TypeError:
                res = func("Software Engineer", "Bangalore")
                
        count = len(res) if res else 0
        print(f"[OK] {name}: Scraped {count} jobs")
        if count > 0:
            sample = res[0]
            print(f"     Sample: Role={sample.get('Job Role')}, Comp={sample.get('Company Name')}, Src={sample.get('Source')}")
        return name, count, None
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[FAIL] {name}: {err}")
        return name, 0, err

async def main():
    results = {}
    for name, portal_info in PORTAL_REGISTRY.items():
        name, count, err = await test_portal(name, portal_info)
        results[name] = {"count": count, "error": err}
        
    print("\n" + "="*50)
    print("SUMMARY OF ALL PORTALS:")
    print("="*50)
    for name, data in results.items():
        status = f"{data['count']} jobs" if data['count'] > 0 else f"FAILED/EMPTY ({data['error']})"
        print(f"{name:16}: {status}")

if __name__ == "__main__":
    asyncio.run(main())
