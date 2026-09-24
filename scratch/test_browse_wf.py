import asyncio
import os
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT
from bs4 import BeautifulSoup
import json

async def test_browse():
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
        
        print("Navigating to /role/l/sales/india...")
        await page.goto("https://wellfound.com/role/l/sales/india", wait_until="domcontentloaded")
        
        # Wait up to 15 seconds, checking title and clicking challenge if present
        for sec in range(15):
            title = await page.title()
            print(f"[{sec}s] Title: {title}")
            if "Just a moment" not in title and "Security" not in title and "Challenge" not in title:
                print("Passed!")
                break
            # Try to click turnstile
            try:
                for frame in page.frames:
                    box = await frame.query_selector("input[type=checkbox], #challenge-stage")
                    if box:
                        await box.click()
            except Exception:
                pass
            await asyncio.sleep(1)
            
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            data = json.loads(next_data.string)
            apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
            job_keys = [k for k in apollo if 'JobListing' in k]
            print(f"Success! Extracted {len(job_keys)} jobs from /role/l/sales/india")
        else:
            print("No __NEXT_DATA__")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_browse())
