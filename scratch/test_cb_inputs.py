import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def t():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        await page.goto('https://www.careerbuilder.com/')
        await asyncio.sleep(5)
        print('Title:', await page.title())
        inputs = await page.query_selector_all('input')
        print('Total inputs:', len(inputs))
        for inp in inputs:
            print('id:', await inp.get_attribute('id'), 'name:', await inp.get_attribute('name'), 'placeholder:', await inp.get_attribute('placeholder'))
        await b.close()

if __name__ == "__main__":
    asyncio.run(t())
