import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY

BROWSER_PORTALS = [
    "jobleads", "wellfound", "careerbuilder", "jooble", 
    "glassdoor", "indeed", "naukri", "ziprecruiter", "workatastartup"
]

async def test_browser(name):
    info = PORTAL_REGISTRY.get(name)
    if not info:
        return name, 0, 0, "Not in registry"
    func = info["func"]
    t0 = time.time()
    try:
        # Pass headless=True and small max_pages
        res = await asyncio.wait_for(func("Software Engineer", "Bangalore", max_pages=1, headless=True), timeout=18.0)
        dur = time.time() - t0
        return name, len(res) if res else 0, dur, None
    except asyncio.TimeoutError:
        return name, 0, time.time() - t0, "Timeout (>18s)"
    except Exception as e:
        return name, 0, time.time() - t0, f"{type(e).__name__}: {str(e)[:60]}"

async def main():
    print(f"{'Portal':16} | {'Count':6} | {'Time (s)':8} | {'Status'}", flush=True)
    print("-" * 55, flush=True)
    for name in BROWSER_PORTALS:
        name, count, dur, err = await test_browser(name)
        status = err if err else "OK"
        print(f"{name:16} | {count:6} | {dur:8.2f} | {status}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
