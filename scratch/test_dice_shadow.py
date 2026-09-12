import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await browser.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        await page.goto('https://www.dice.com/jobs?q=Python&location=Remote', timeout=30000)
        await asyncio.sleep(6)
        
        # Test Dice cards
        data = await page.evaluate('''() => {
            const cards = document.querySelectorAll('dhi-search-card');
            const res = [];
            cards.forEach(c => {
                const root = c.shadowRoot || c;
                const title = root.querySelector('a[data-cy="card-title-link"], a.card-title-link, .card-title, h5 a');
                const comp = root.querySelector('[data-cy="search-result-company-name"], .card-company, a.company-name');
                const loc = root.querySelector('[data-cy="search-result-location"], .card-location');
                const posted = root.querySelector('[data-cy="posted-date"], .posted-date');
                const desc = root.querySelector('[data-cy="card-summary"], .card-description');
                
                const titleText = title ? title.innerText.trim() : (c.innerText || '').split('\\n')[0];
                const link = title ? title.href : '';
                const compText = comp ? comp.innerText.trim() : '';
                const locText = loc ? loc.innerText.trim() : '';
                const dateText = posted ? posted.innerText.trim() : '';
                const descText = desc ? desc.innerText.trim() : '';
                
                res.push({
                    title: titleText,
                    link: link,
                    company: compText,
                    location: locText,
                    date: dateText,
                    desc: descText
                });
            });
            return res;
        }''')
        print('Dice shadow cards count:', len(data))
        if data:
            print('Sample dice shadow card:', data[0])
            print('Sample dice card 1:', data[1] if len(data) > 1 else 'None')
        await browser.close()

asyncio.run(inspect())
