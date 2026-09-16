import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_cb_slug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        urls = [
            "https://www.careerbuilder.com/jobs-sales-development-representative",
            "https://www.careerbuilder.com/jobs-sales-development-representative?pay=",
            "https://www.careerbuilder.com/jobs?utf8=%E2%9C%93&keywords=Sales+Development+Representative&location="
        ]
        
        for u in urls:
            print("="*60)
            print("Navigating to:", u)
            await page.goto(u, timeout=30000, wait_until="networkidle")
            await asyncio.sleep(3)
            print("Final URL:", page.url)
            print("Title:", await page.title())
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Check for articles or job cards
            articles = soup.find_all("article")
            print("Articles count:", len(articles))
            
            # Check for links with /job/ or /job-listings/
            job_links = soup.find_all("a", href=lambda h: h and ("/job/" in h or "/job-listings/" in h or "jobdetail" in h.lower() or "job_key" in h.lower()))
            print("Job links count:", len(job_links))
            for jl in job_links[:5]:
                print("  ", jl.get_text(strip=True), "->", jl.get("href"))
                
            # Check NEXT_DATA
            nd = soup.find("script", id="__NEXT_DATA__")
            if nd:
                print("NEXT_DATA found len:", len(nd.string))
                if "jobResults" in nd.string or "jobTitle" in nd.string or "companyName" in nd.string or "jobViewResults" in nd.string:
                    print("Found job keys in NEXT_DATA!")
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cb_slug())
