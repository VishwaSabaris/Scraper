import asyncio
import os
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def check_cf():
    user_dir = os.path.abspath("./wellfound_direct_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
        
        for i in range(10):
            title = await page.title()
            print(f"[{i*2}s] Page Title: {title}")
            if "Wellfound" in title and "Security" not in title and "Just a moment" not in title:
                print("Passed Cloudflare!")
                break
            # Look for iframe or turnstile checkbox
            frames = page.frames
            for f in frames:
                try:
                    cb = await f.query_selector("input[type='checkbox'], #challenge-stage")
                    if cb:
                        print("Found turnstile checkbox! Clicking...")
                        await cb.click()
                except Exception:
                    pass
            await asyncio.sleep(2)
            
        print("Final title:", await page.title())
        await context.close()

if __name__ == "__main__":
    asyncio.run(check_cf())
