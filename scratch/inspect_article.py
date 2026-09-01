import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def inspect_art():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    url = "https://www.ziprecruiter.com/jobs-search?search=Software+Developer&location=London"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto(url, timeout=30000)
        await asyncio.sleep(4)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        articles = soup.find_all("article")
        print(f"Total articles found: {len(articles)}")
        
        for idx, art in enumerate(articles[:2]):
            print(f"\n================ ARTICLE {idx+1} ================")
            print(art.prettify()[:1500])
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_art())
