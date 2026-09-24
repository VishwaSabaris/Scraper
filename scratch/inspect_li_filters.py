import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await (await create_stealth_context(b)).new_page()
        await page.goto('https://www.linkedin.com/jobs/search?keywords=Python+Developer&location=United+States')
        await asyncio.sleep(5)
        # Check filter buttons or forms on page
        buttons = await page.locator("button, [data-tracking-control-name]").all_text_contents()
        filter_buttons = [b.strip() for b in buttons if b.strip() and len(b.strip()) < 30]
        print("Filter buttons / controls found:")
        print(filter_buttons[:30])
        
        # Check if there is an on-site/remote filter button
        remote_btn = page.locator("button:has-text('On-site/remote'), button:has-text('Remote')")
        print("Remote button count:", await remote_btn.count())
        if await remote_btn.count() > 0:
            print("Remote button text:", await remote_btn.first.text_content())
            await remote_btn.first.click()
            await asyncio.sleep(2)
            # Check what popped up
            popups = await page.locator("fieldset, [role='dialog'], form").all_text_contents()
            for pop in popups:
                print("Popup:", pop[:200])

        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
