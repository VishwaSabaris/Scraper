import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import urllib.parse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_search():
    # Test 1: keywords=Python Developer, location=New York, f_WT=2
    params = {
        "keywords": "Python Developer",
        "location": "New York",
        "f_WT": "2"
    }
    url = f"https://www.linkedin.com/jobs/search?{urllib.parse.urlencode(params)}"
    print("Navigating to:", url)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        await page.goto(url)
        await asyncio.sleep(6)
        
        print("Final URL:", page.url)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        cards = soup.find_all(['li', 'div'], class_=lambda x: x and ('base-card' in x or 'base-search-card' in x or 'job-search-card' in x))
        print(f"Found {len(cards)} cards")
        for i, card in enumerate(cards[:10]):
            title = card.find(class_=lambda x: x and 'title' in x)
            loc = card.find(class_=lambda x: x and 'location' in x)
            urn = card.get('data-entity-urn', '')
            t_text = title.text.strip() if title else 'N/A'
            l_text = loc.text.strip() if loc else 'N/A'
            print(f"Card {i+1}: {t_text} | Location: {l_text} | Urn: {urn}")
            # Also check if card has any badges or pills or extra spans
            spans = [s.text.strip() for s in card.find_all('span') if s.text.strip()]
            print(f"  Spans: {spans[:5]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
