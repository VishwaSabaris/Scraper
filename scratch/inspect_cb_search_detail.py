import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS

async def test_cb_detail_panel():
    user_dir = "./careerbuilder_session_run"
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=True,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1600, 'height': 900}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=True,
                viewport={'width': 1600, 'height': 900}
            )
        page = context.pages[0] if context.pages else await context.new_page()
        
        url = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative&where="
        print("Navigating to:", url)
        await page.goto(url, timeout=40000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        title = await page.title()
        print("Title:", title)
        
        # Check if cards exist
        cards = await page.locator("article[data-testid='JobCard'], div[data-testid='JobCard']").all()
        print(f"Locator found {len(cards)} JobCard elements")
        
        if not cards:
            # check generic card selectors
            cards = await page.locator("#JobCardGrid > div, div[id*='JobCard']").all()
            print(f"Generic locator found {len(cards)} elements")
            
        for i, card in enumerate(cards[:5]):
            print(f"\n--- Card [{i+1}] ---")
            text = await card.inner_text()
            print("Card Text:\n", text[:200])
            
            # Click the card to load right detail panel
            try:
                await card.click()
                await asyncio.sleep(2)
                
                # Check detail pane
                detail_pane = page.locator("#job-details, [data-testid='job-description'], .job-description, #job-description, div[class*='JobDescription']")
                count = await detail_pane.count()
                print(f"Detail pane count: {count}")
                if count > 0:
                    desc_text = await detail_pane.first.inner_text()
                    print(f"Detail pane description length: {len(desc_text)}")
                    print("Detail snippet:\n", desc_text[:300])
            except Exception as e:
                print("Click error:", e)
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_cb_detail_panel())
