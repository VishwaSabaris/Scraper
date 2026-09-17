import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test():
    async with async_playwright() as p:
        try:
            # Try launching installed Google Chrome
            browser = await p.chromium.launch(headless=True, channel="chrome", args=CHROMIUM_STEALTH_ARGS)
            page = await browser.new_page()
            await page.add_init_script(STEALTH_JS_INIT)
            url = 'https://www.naukri.com/lead-generation-executive-jobs'
            print('Navigating to', url, 'with Chrome channel...')
            await page.goto(url, timeout=30000)
            await asyncio.sleep(6)
            title = await page.title()
            print('Title:', title)
            await browser.close()
        except Exception as e:
            print('Error with channel chrome:', e)

if __name__ == "__main__":
    asyncio.run(test())
