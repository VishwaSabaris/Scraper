import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def inspect_dice_dom():
    user_dir = os.path.abspath("./scratch/dice_session_inspect")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        await page.goto("https://www.dice.com/jobs?q=Python&location=Remote", timeout=30000)
        await asyncio.sleep(5)
        
        # Extract full job card data using JS evaluation in page context
        cards_data = await page.evaluate('''() => {
            const results = [];
            // Check custom elements or card containers
            const cards = document.querySelectorAll('dhi-search-card, [data-cy="search-card"], [class*="search-card"]');
            cards.forEach(card => {
                const titleEl = card.querySelector('a[data-cy="card-title-link"], .card-title-link, h5 a, h3 a');
                const compEl = card.querySelector('a[data-cy="search-result-company-name"], [data-cy="search-result-company-name"], .card-company');
                const locEl = card.querySelector('[data-cy="search-result-location"], .card-location');
                const dateEl = card.querySelector('[data-cy="posted-date"], .posted-date');
                const descEl = card.querySelector('[data-cy="card-summary"], .card-description');
                
                if (titleEl || compEl) {
                    results.push({
                        title: titleEl ? titleEl.innerText.trim() : '',
                        link: titleEl ? titleEl.href : '',
                        company: compEl ? compEl.innerText.trim() : '',
                        location: locEl ? locEl.innerText.trim() : '',
                        date: dateEl ? dateEl.innerText.trim() : '',
                        desc: descEl ? descEl.innerText.trim() : ''
                    });
                }
            });
            return results;
        }''')
        
        print(f"Dice JS extracted cards count: {len(cards_data)}")
        for idx, c in enumerate(cards_data[:3]):
            print(f"Card {idx}:", c)
            
        await context.close()

asyncio.run(inspect_dice_dom())
