import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS

async def test_non_headless():
    user_dir = "./careerbuilder_session_run"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1600, 'height': 900}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        url = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative&where="
        print("Navigating non-headless to:", url)
        await page.goto(url, timeout=40000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        title = await page.title()
        print("Page Title:", title)
        
        # Check JobCard elements
        cards = await page.locator("article[data-testid='JobCard'], div[data-testid='JobCard']").all()
        print(f"JobCard elements found: {len(cards)}")
        
        if len(cards) > 0:
            for i, card in enumerate(cards[:3]):
                print(f"\n--- Card [{i+1}] ---")
                text = await card.inner_text()
                print("Card Text:\n", text[:200])
                
                # Check if clicking card loads detail pane
                await card.click()
                await asyncio.sleep(2)
                
                # Find detail pane
                desc_el = page.locator("[data-testid='job-description'], .job-description, #job-description, div[id*='job-details']")
                count = await desc_el.count()
                print(f"Desc elements found: {count}")
                if count > 0:
                    desc_text = await desc_el.first.inner_text()
                    print(f"Description length: {len(desc_text)}")
                    print("Description preview:\n", desc_text[:300])
                    
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_non_headless())
