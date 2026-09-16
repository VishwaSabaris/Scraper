import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def inspect_cb_cards_inner():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        u = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative"
        await page.goto(u, timeout=30000, wait_until="networkidle")
        await asyncio.sleep(4)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(class_=lambda x: x and "StyledJobCardsContainer" in x)
        if container:
            print("Found StyledJobCardsContainer!")
            children = container.find_all(recursive=False)
            print("Direct children count:", len(children))
            for i, ch in enumerate(children):
                print(f"Child {i}: tag={ch.name}, class={ch.get('class')}")
                links = ch.find_all('a')
                for l in links:
                    print(f"   Link: text='{l.get_text(strip=True)}', href='{l.get('href')}'")
                print("   Text:", ch.get_text(separator=" | ", strip=True)[:150])
        else:
            print("StyledJobCardsContainer not found")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_cb_cards_inner())
