import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_cb_interactive():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        # Navigate to home first or search
        await page.goto("https://www.careerbuilder.com/", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # Fill search inputs directly
        keywords_input = page.locator("input[name='keywords'], input[id='keywords'], input[placeholder*='job title']")
        if await keywords_input.count() > 0:
            print("Found keywords input on homepage! Filling...")
            await keywords_input.first.fill("Sales Development Representative")
            await asyncio.sleep(1)
            
            # Submit search
            search_btn = page.locator("button[type='submit'], button:has-text('Search'), button:has-text('Find Jobs')")
            if await search_btn.count() > 0:
                print("Clicking search button...")
                await search_btn.first.click()
                await asyncio.sleep(5)
                print("Post-search URL:", page.url)
                
                # Check cards
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all("article")
                if not cards:
                    cards = soup.find_all("div", class_=lambda x: x and "JobCard" in str(x))
                if not cards:
                    cards = soup.find_all("div", class_=lambda x: x and "card" in str(x).lower())
                print(f"Cards found after homepage search: {len(cards)}")
                
                # Also check all job links
                links = soup.find_all("a", href=lambda h: h and ("/job/" in h or "/job-listings/" in h))
                print(f"Job links found: {len(links)}")
                for l in links[:5]:
                    print("  ", l.get_text(strip=True), "->", l.get("href"))
        else:
            print("No keywords input found on homepage.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cb_interactive())
