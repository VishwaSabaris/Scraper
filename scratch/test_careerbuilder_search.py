import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test():
    user_dir = os.path.abspath("./careerbuilder_session_test")
    os.makedirs(user_dir, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.careerbuilder.com/", timeout=30000)
        await asyncio.sleep(4)
        print('Homepage Title:', await page.title())
        
        # Check inputs
        kw_input = await page.query_selector("input[aria-label*='Job title'], input[placeholder*='Job title'], input[name='keywords'], input#keywords")
        loc_input = await page.query_selector("input[aria-label*='City'], input[placeholder*='City'], input[name='location'], input#location")
        
        print('Found kw_input:', kw_input is not None)
        print('Found loc_input:', loc_input is not None)
        
        if kw_input:
            await kw_input.fill("Sales Executive")
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(6)
            print('After search Title:', await page.title(), 'URL:', page.url)
            from bs4 import BeautifulSoup
            s = BeautifulSoup(await page.content(), 'html.parser')
            print('Cards found:', len(s.find_all('article', {'data-testid': 'JobCard'})))
            print('Links with /job/:', len(s.select('a[href*="/job/"], a[href*="/job-details/"]')))
        await context.close()

if __name__ == "__main__":
    asyncio.run(test())
