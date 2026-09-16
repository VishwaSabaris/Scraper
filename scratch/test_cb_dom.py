import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def dump_cb_dom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        await page.goto("https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative", timeout=30000)
        await asyncio.sleep(6)
        
        html = await page.content()
        with open("scratch/cb_search_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved scratch/cb_search_page.html, size:", len(html))
        
        # Check what scripts, links, tags exist
        soup = BeautifulSoup(html, "html.parser")
        print("Page title:", soup.title.string if soup.title else "No title")
        
        # Check for NEXT_DATA or state
        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data:
            print("Found __NEXT_DATA__! Length:", len(next_data.string))
            with open("scratch/cb_next_data.json", "w", encoding="utf-8") as f:
                f.write(next_data.string)
        else:
            print("No __NEXT_DATA__ found.")
            
        scripts = [s.get("id") or s.get("type") for s in soup.find_all("script")]
        print("Script IDs/types:", scripts[:10])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_cb_dom())
