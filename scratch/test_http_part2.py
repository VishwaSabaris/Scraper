import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY

HTTP_PORTALS_PART2 = ["reed", "himalayas", "remote_co", "workable", "jobspresso"]

async def test_single(name):
    info = PORTAL_REGISTRY[name]
    func = info["func"]
    is_async = info["is_async"]
    t0 = time.time()
    try:
        if is_async:
            res = await asyncio.wait_for(func("Software Engineer", "", max_pages=1), timeout=25.0)
        else:
            res = await asyncio.to_thread(func, "Software Engineer", "", max_jobs=10)
        dur = time.time() - t0
        count = len(res) if res else 0
        return name, count, dur, None
    except Exception as e:
        return name, 0, time.time() - t0, f"{type(e).__name__}: {e}"

async def main():
    print(f"{'Portal':16} | {'Count':6} | {'Time (s)':8} | {'Status/Error'}")
    print("-" * 65)
    for name in HTTP_PORTALS_PART2:
        name, count, dur, err = await test_single(name)
        err_str = err if err else "OK"
        print(f"{name:16} | {count:6} | {dur:8.2f} | {err_str}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
