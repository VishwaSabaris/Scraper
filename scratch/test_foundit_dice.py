import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test_foundit():
    print("--- Testing Foundit with persistent stealth context ---")
    user_dir = os.path.abspath("./scratch/foundit_test_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        # First visit homepage
        try:
            await page.goto("https://www.foundit.in/", timeout=20000)
            await asyncio.sleep(2)
        except Exception:
            pass
            
        url = "https://www.foundit.in/srp/results?query=Python&locations=Bangalore"
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=30000)
        await asyncio.sleep(5)
        
        # Check title and content
        print("Page title:", await page.title())
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Let's inspect any card containers
        cards = soup.select('.srpResultCard') or soup.select('[class*="srpResultCard"]') or soup.select('.cardContainer') or soup.select('[class*="cardContainer"]') or soup.select('[class*="jobTuple"]')
        print("Foundit cards found:", len(cards))
        for c in cards[:2]:
            title_el = c.select_one('.jobTitle') or c.select_one('[class*="title"]') or c.select_one('a')
            comp_el = c.select_one('.companyName') or c.select_one('[class*="company"]')
            loc_el = c.select_one('.location') or c.select_one('[class*="location"]')
            print("Foundit card:", title_el.text.strip() if title_el else 'No title', "|", comp_el.text.strip() if comp_el else 'No comp', "|", loc_el.text.strip() if loc_el else 'No loc')
            
        await context.close()

async def test_dice():
    print("\n--- Testing Dice with persistent stealth context ---")
    user_dir = os.path.abspath("./scratch/dice_test_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        url = "https://www.dice.com/jobs?q=Python&location=Remote"
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=30000)
        await asyncio.sleep(6)
        
        print("Page title:", await page.title())
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        cards = soup.select('dhi-search-card') or soup.select('[data-cy="search-card"]') or soup.select('a[data-cy="card-title-link"]') or soup.select('.search-card')
        print("Dice cards found:", len(cards))
        
        # Look for shadow DOM or card links
        links = await page.evaluate('''() => {
            const results = [];
            const els = document.querySelectorAll('a[data-cy="card-title-link"], a[href*="/job-detail/"]');
            els.forEach(el => {
                results.push({
                    title: el.innerText.trim(),
                    href: el.href
                });
            });
            return results;
        }''')
        print("Dice JS evaluated links count:", len(links))
        if links:
            print("Sample dice evaluated link:", links[0])
            
        await context.close()

async def main():
    await test_foundit()
    await test_dice()

asyncio.run(main())
