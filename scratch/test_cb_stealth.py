import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_cb_stealth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=CHROMIUM_STEALTH_ARGS
        )
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        # Test Careerjet / Careerbuilder / other
        url = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative&where="
        print("Navigating to:", url)
        await page.goto(url, timeout=40000, wait_until="networkidle")
        await asyncio.sleep(4)
        
        # Let's check if there are any jobs or links
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for cards or text
        print("Page Title:", await page.title())
        cards = soup.find_all("article")
        print("Articles:", len(cards))
        
        # Look for any job cards or links
        links = [a.get("href") for a in soup.find_all("a") if a.get("href") and "/job" in a.get("href")]
        print("Job links count:", len(links))
        for l in links[:5]:
            print("  ", l)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cb_stealth())
