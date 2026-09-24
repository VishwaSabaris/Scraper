import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        await page.goto('https://www.linkedin.com/jobs/view/4462361684')
        await asyncio.sleep(4)
        c = await page.content()
        soup = BeautifulSoup(c, 'html.parser')
        print("Page title:", soup.title.text if soup.title else "No title")
        for el in soup.find_all(class_=lambda x: x and ('workplace' in x.lower() or 'job-insight' in x.lower() or 'bullet' in x.lower() or 'topcard' in x.lower())):
            txt = el.text.strip()
            print("Insight element:", txt[:100])
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
