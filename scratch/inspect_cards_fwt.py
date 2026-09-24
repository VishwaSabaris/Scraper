import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def run():
    url = "https://www.linkedin.com/jobs/search?keywords=Python+Developer&location=New+York&f_WT=2"
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        await page.goto(url)
        await asyncio.sleep(5)
        
        cards = await page.locator("ul.jobs-search__results-list > li, li .base-card, .job-search-card").all()
        print(f"Cards found: {len(cards)}")
        for idx, card in enumerate(cards[:15]):
            text = await card.text_content()
            clean_text = " ".join(text.split())
            print(f"Card {idx+1}: {clean_text}")
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
