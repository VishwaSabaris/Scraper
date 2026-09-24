import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY

async def test_single(name, info):
    func = info["func"]
    is_async = info["is_async"]
    t0 = time.time()
    try:
        if is_async:
            # We run headless=True for browser scrapers so they don't pop up or block
            coro = func("Software Engineer", "Bangalore", max_pages=1, headless=True)
            res = await asyncio.wait_for(coro, timeout=20.0)
        else:
            res = await asyncio.to_thread(func, "Software Engineer", "Bangalore", max_jobs=10)
        dur = time.time() - t0
        count = len(res) if res else 0
        return name, count, dur, None
    except asyncio.TimeoutError:
        return name, 0, time.time() - t0, "Timeout (>20s)"
    except Exception as e:
        return name, 0, time.time() - t0, f"{type(e).__name__}: {e}"

async def main():
    print(f"{'Portal':16} | {'Count':6} | {'Time (s)':8} | {'Status/Error'}")
    print("-" * 65)
    for name, info in PORTAL_REGISTRY.items():
        name, count, dur, err = await test_single(name, info)
        err_str = err if err else "OK"
        print(f"{name:16} | {count:6} | {dur:8.2f} | {err_str}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
