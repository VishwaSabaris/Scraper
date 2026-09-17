import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        res1 = await page.goto('https://www.careerbuilder.com/job-listings/search?q=Python', timeout=20000)
        print('Old URL Title:', await page.title(), 'URL:', page.url)
        res2 = await page.goto('https://www.careerbuilder.com/jobs?keywords=Python', timeout=20000)
        print('New URL Title:', await page.title(), 'URL:', page.url)
        await b.close()

if __name__ == "__main__":
    asyncio.run(test())
