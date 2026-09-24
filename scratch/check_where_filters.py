import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        await page.goto('https://www.linkedin.com/jobs/search?keywords=Python+Developer&location=United+States')
        await asyncio.sleep(5)
        btn = page.locator("button:has-text('Where are the filters?'), a:has-text('Where are the filters?')")
        if await btn.count() > 0:
            print("Found where are the filters button")
            # print parent text
            print("Parent text:", await btn.first.locator("xpath=..").text_content())
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
