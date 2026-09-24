import asyncio
import os
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test_search_ui():
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
        
        # Inspect the react-select containers
        details = await page.evaluate('''() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.map(i => ({
                id: i.id,
                placeholder: i.placeholder,
                parentText: i.closest('div')?.parentElement?.innerText || ''
            }));
        }''')
        for d in details:
            print(d)
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_search_ui())
