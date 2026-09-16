import asyncio
import os
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_cb_queries():
    queries = [
        'site:careerbuilder.com/job "Sales Development Representative"',
        'site:careerbuilder.com "Sales Development Representative" "Bangalore"',
        'site:careerbuilder.com "Sales Development Representative"'
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        for q in queries:
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            print("="*60)
            print("Query:", q)
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            results = soup.find_all('div', class_=lambda x: x and ('g' in x.split() or 'MjjYud' in x))
            print(f"Results found: {len(results)}")
            for r in results[:3]:
                a = r.find('a', href=True)
                h3 = r.find('h3')
                if a:
                    print("  ", h3.text if h3 else "No H3", "->", a['href'])
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cb_queries())
