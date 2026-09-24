import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def run():
    queries = [
        "https://www.linkedin.com/jobs/search?keywords=Python+Developer+Remote",
        "https://www.linkedin.com/jobs/search?keywords=Python+Developer+Remote&location=United+States",
        "https://www.linkedin.com/jobs/search?keywords=Python+Developer+Remote&location=Worldwide",
    ]
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        for q in queries:
            print(f"\n--- Checking URL: {q} ---")
            await page.goto(q)
            await asyncio.sleep(4)
            cards = await page.locator("ul.jobs-search__results-list > li, li .base-card, .job-search-card").all()
            print(f"Cards found: {len(cards)}")
            for idx, card in enumerate(cards[:8]):
                txt = " ".join((await card.text_content()).split())
                print(f"  [{idx+1}] {txt}")
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
