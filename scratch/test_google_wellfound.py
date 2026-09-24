import sys
sys.path.insert(0, '.')
import asyncio
import os
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_search():
    query = 'site:wellfound.com/jobs "Lead Generation" Chennai'
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    print("URL:", google_url)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(google_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"Total links: {len(links)}")
        for a in links:
            href = a['href']
            h3 = a.find('h3')
            text = h3.text if h3 else a.text.strip()
            if h3 or 'wellfound' in href:
                print(f"HREF: {href[:100]} | TEXT: {text[:60]}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
