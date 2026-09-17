import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_google():
    query = 'site:careerbuilder.com/job-details/ "Sales Development Representative"'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=20"
        print(f"Navigating to Google: {url}")
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        results = soup.find_all("div", class_=lambda x: x and ("g" in x.split() or "MjjYud" in x))
        print(f"Found {len(results)} search result containers")
        
        for i, res in enumerate(results):
            a_tag = res.find("a", href=True)
            h3_tag = res.find("h3")
            snippet_el = res.find("div", class_=lambda x: x and ("VwiC3b" in x or "yXK7lf" in x or "s3v9rd" in x))
            
            if not a_tag or not h3_tag:
                continue
                
            href = a_tag["href"]
            title = h3_tag.text.strip()
            snippet = snippet_el.text.strip() if snippet_el else ""
            
            print(f"\n[{i+1}] Title: {title}")
            print(f"    URL: {href}")
            print(f"    Snippet: {snippet}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_google())
