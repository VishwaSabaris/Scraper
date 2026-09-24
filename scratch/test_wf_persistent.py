import asyncio
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import sys
sys.path.insert(0, '.')
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test():
    user_dir = os.path.abspath("./wellfound_direct_session")
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                channel="chrome",
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        print("Navigating to https://wellfound.com/role/l/sales/chennai...")
        resp = await page.goto("https://wellfound.com/role/l/sales/chennai", wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(6)
        print("Status:", resp.status if resp else "None")
        print("Title:", await page.title())
        
        # Check __NEXT_DATA__
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            data = json.loads(next_data.string)
            apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
            job_keys = [k for k in apollo if 'JobListing' in k]
            print(f"Found {len(job_keys)} JobListing keys in Apollo!")
        else:
            print("No __NEXT_DATA__ found")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test())
