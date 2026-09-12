import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def test_careerjet():
    user_dir = os.path.abspath("./scratch/careerjet_test_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        try:
            await page.goto("https://www.careerjet.co.in/", timeout=20000)
            await asyncio.sleep(2)
        except Exception:
            pass
            
        url = "https://www.careerjet.co.in/search/jobs?s=Python&l=Bangalore"
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=30000)
        await asyncio.sleep(5)
        
        # Extract cards using page.evaluate
        cards = await page.evaluate('''() => {
            const results = [];
            const articles = document.querySelectorAll('article.job, article, .job');
            articles.forEach(art => {
                const titleEl = art.querySelector('header h2 a, h2 a, a.title, h2');
                const compEl = art.querySelector('.company_compact, .company, p.company');
                const locEl = art.querySelector('.location_compact, .location, ul.location');
                const salEl = art.querySelector('.salary, ul.salary');
                const descEl = art.querySelector('.desc, .job-description');
                
                if (titleEl) {
                    results.push({
                        title: titleEl.innerText.trim(),
                        link: titleEl.href || (titleEl.tagName === 'A' ? titleEl.href : ''),
                        company: compEl ? compEl.innerText.trim() : 'Careerjet Employer',
                        location: locEl ? locEl.innerText.trim() : 'Bangalore',
                        salary: salEl ? salEl.innerText.trim() : 'N/A',
                        desc: descEl ? descEl.innerText.trim() : ''
                    });
                }
            });
            return results;
        }''')
        print(f"Careerjet extracted cards: {len(cards)}")
        if cards:
            print("Sample Careerjet:", cards[0])
            
        await context.close()

asyncio.run(test_careerjet())
