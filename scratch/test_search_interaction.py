import asyncio
import os
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test_interact():
    user_dir = os.path.abspath("./wellfound_direct_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        inputs = await page.query_selector_all("input[id*='react-select']")
        print(f"Found {len(inputs)} react-select inputs")
        if len(inputs) >= 2:
            # First input: Role
            await inputs[0].click()
            await inputs[0].fill("Sales")
            await asyncio.sleep(1)
            # Check dropdown options
            options = await page.eval_on_selector_all("[id*='react-select'][id*='option']", "elems => elems.map(e => e.innerText)")
            print("Role options:", options)
            if options:
                await page.click(f"[id*='react-select'][id*='option']:has-text('{options[0]}')")
            await asyncio.sleep(1)
            
            # Second input: Location
            await inputs[1].click()
            await inputs[1].fill("India")
            await asyncio.sleep(1)
            loc_options = await page.eval_on_selector_all("[id*='react-select'][id*='option']", "elems => elems.map(e => e.innerText)")
            print("Location options:", loc_options)
            if loc_options:
                await page.click(f"[id*='react-select'][id*='option']:has-text('{loc_options[0]}')")
            await asyncio.sleep(1)
            
            # Click Search button
            search_btn = await page.query_selector("button:has-text('Search')")
            if search_btn:
                print("Clicking Search button...")
                await search_btn.click()
                await asyncio.sleep(4)
                print("New URL after search:", page.url)
                print("New Title after search:", await page.title())
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_interact())
