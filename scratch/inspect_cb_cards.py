import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def inspect_cb_cards():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        u = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative"
        print("Navigating to:", u)
        await page.goto(u, timeout=30000, wait_until="networkidle")
        await asyncio.sleep(4)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        grid = soup.find(id="JobCardGrid")
        if grid:
            print("Found #JobCardGrid!")
            # Find all links or card wrappers
            cards = grid.find_all("div", recursive=False)
            print("Direct div children of #JobCardGrid:", len(cards))
            
            # Print structure of first card
            for i, c in enumerate(cards[:3]):
                print(f"\n--- Card {i+1} ---")
                print("Tags/Classes:", c.get("class"))
                title_link = c.find("a")
                if title_link:
                    print("  Link text:", title_link.get_text(strip=True))
                    print("  Href:", title_link.get("href"))
                print("  All text:", c.get_text(separator=" | ", strip=True)[:300])
        else:
            print("JobCardGrid not found!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_cb_cards())
