import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def inspect_full():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    url = "https://www.ziprecruiter.com/jobs-search?search=Software+Developer&location=London"
    
    async with async_playwright() as p:
        # Launch with persistent context, headless=False
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto(url, timeout=40000)
        await asyncio.sleep(5)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Check articles or job divs
        articles = soup.find_all("article")
        print(f"Articles count: {len(articles)}")
        
        # Check div/li cards
        div_cards = soup.find_all("div", class_=lambda c: c and ("job_result" in c or "job-card" in c or "job_listing" in c or "job-listing" in c))
        print(f"Div cards count: {len(div_cards)}")
        
        # Check data-testid elements
        comp_els = soup.find_all(attrs={"data-testid": "job-card-company"})
        loc_els = soup.find_all(attrs={"data-testid": "job-card-location"})
        print(f"Company elements: {len(comp_els)}, Location elements: {len(loc_els)}")
        
        # Let's inspect parents of company elements
        if comp_els:
            print("\n--- Inspecting first company parent container ---")
            parent = comp_els[0].find_parent(["article", "li", "div"])
            while parent and not any(k in (parent.get("class") or []) for k in ["job", "card", "item", "result"]):
                parent = parent.find_parent(["article", "li", "div"])
            if parent:
                print("Found card parent:", parent.name, parent.get("class"))
                print(parent.prettify()[:1200])
            else:
                print("Direct parent of comp_els[0]:", comp_els[0].parent.name, comp_els[0].parent.get("class"))
                print(comp_els[0].parent.prettify()[:800])
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_full())
