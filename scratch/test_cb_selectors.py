import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def inspect_cb():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        urls = [
            "https://www.careerbuilder.com/jobs?keywords=Sales+Development+Representative&location=USA",
            "https://www.careerbuilder.com/jobs?keywords=Sales+Development+Representative",
            "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative"
        ]
        
        for u in urls:
            print("="*60)
            print("Testing URL:", u)
            try:
                await page.goto(u, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(4)
                print("Final URL:", page.url)
                print("Title:", await page.title())
                
                selectors = [
                    'article[data-testid="JobCard"]',
                    '.data-results-content-parent',
                    '.job-listing-item',
                    'li.data-results-content-parent',
                    'div[data-job-id]',
                    'a[href*="/job/"]',
                    'a[href*="/job-listings/"]',
                    'div#card-scroll-container',
                    '.job-card',
                    'div[data-testid="job-card"]',
                    'ul.job-listings > li'
                ]
                for sel in selectors:
                    cnt = await page.locator(sel).count()
                    print(f'  Selector "{sel}": {cnt}')
                
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                # Look for all links
                links = [a.get("href", "") for a in soup.find_all("a") if "/job/" in a.get("href", "") or "/job-listings/" in a.get("href", "") or "job" in a.get("href", "")]
                print(f"  Found {len(links)} job-related links in HTML. Sample: {links[:3]}")
                
            except Exception as e:
                print("Error loading:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_cb())
