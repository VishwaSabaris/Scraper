import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test(url, label):
    print(f"\n--- Testing {label} ({url}) ---")
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        await page.goto(url)
        await asyncio.sleep(5)
        soup = BeautifulSoup(await page.content(), 'html.parser')
        cards = soup.find_all(['li', 'div'], class_=lambda x: x and ('base-card' in x or 'base-search-card' in x or 'job-search-card' in x))
        valid_cards = [c for c in cards if c.find('h3') or c.find(class_=lambda x: x and 'title' in x)]
        print(f"Total cards: {len(valid_cards)}")
        for i, c in enumerate(valid_cards[:5]):
            title = (c.find('h3') or c.find(class_=lambda x: x and 'title' in x)).text.strip()
            loc_el = c.find('span', class_=lambda x: x and 'location' in x)
            loc = loc_el.text.strip() if loc_el else 'N/A'
            card_all_text = " ".join(c.text.split())
            print(f"[{i+1}] Title: {title} | Location: {loc}")
            print(f"    Full Card: {card_all_text[:120]}")
        await b.close()

async def main():
    await test("https://www.linkedin.com/jobs/search?keywords=Python+Developer+Remote", "Keywords: Python Developer Remote")
    await test("https://www.linkedin.com/jobs/search?keywords=Python+Developer&f_WT=2", "f_WT=2 without location")
    await test("https://www.linkedin.com/jobs/search?keywords=Python+Developer&location=United+States&f_WT=2", "f_WT=2 with US location")
    await test("https://www.linkedin.com/jobs/search?keywords=Python+Developer&location=remote", "location=remote")

if __name__ == "__main__":
    asyncio.run(main())
