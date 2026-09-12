import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test():
    user_dir = os.path.abspath("./scratch/foundit_session_test")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        urls = []
        page.on('response', lambda res: urls.append((res.status, res.url)))
        
        try:
            await page.goto('https://www.foundit.in/', timeout=25000)
            await asyncio.sleep(3)
            
            await page.goto('https://www.foundit.in/srp/results?query=Python&locations=Bangalore', timeout=25000)
            await asyncio.sleep(6)
            
            print('Foundit Title:', await page.title())
            print('Foundit URL:', page.url)
            print('Captured responses count:', len(urls))
            for status, u in urls:
                if any(k in u.lower() for k in ['search', 'job', 'srp', 'api', 'result', 'list', 'middleware']):
                    print(f'  [{status}] -> {u[:120]}')
                    
            cards = await page.query_selector_all('.srpResultCard, .cardContainer, [class*="card"], [class*="jobTuple"]')
            print('Cards found in page:', len(cards))
        except Exception as e:
            print("Foundit error:", e)
        finally:
            await context.close()

asyncio.run(test())
