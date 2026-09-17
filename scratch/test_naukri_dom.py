import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT
from bs4 import BeautifulSoup

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        url = 'https://www.naukri.com/lead-generation-executive-jobs?k=Lead+Generation+Executive'
        print('Navigating to', url)
        await page.goto(url, timeout=30000)
        await asyncio.sleep(6)
        print('Title:', await page.title())
        content = await page.content()
        print('Content length:', len(content))
        s = BeautifulSoup(content, 'html.parser')
        print('Cards cust-job-tuple:', len(s.select('.cust-job-tuple')))
        print('Cards srp-jobtuple-wrapper:', len(s.select('.srp-jobtuple-wrapper')))
        print('Cards article:', len(s.select('article')))
        print('Divs with tuple:', len(s.find_all(class_=lambda c: c and 'tuple' in str(c))))
        print('Links with job-listings:', len(s.select('a[href*="job-listings"]')))
        
        # Check title / company in job-listings links
        links = s.select('a[href*="job-listings"]')
        for l in links[:5]:
            print('Job link:', l.get('href'), 'text:', l.text.strip())
        await b.close()

if __name__ == "__main__":
    asyncio.run(test())
