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
        await page.goto("https://www.linkedin.com/jobs/search?keywords=Python+Developer+Remote")
        await asyncio.sleep(4)
        soup = BeautifulSoup(await page.content(), 'html.parser')
        cards = soup.find_all(['li', 'div'], class_=lambda x: x and ('base-card' in x or 'base-search-card' in x))
        for c in cards:
            a = c.find('a', class_=lambda x: x and 'title' in x) or c.find('a')
            if a and a.get('href') and '/jobs/view/' in a['href']:
                url = a['href'].split('?')[0]
                print("Job URL:", url)
                await page.goto(url)
                await asyncio.sleep(3)
                detail_soup = BeautifulSoup(await page.content(), 'html.parser')
                bullets = detail_soup.find_all(class_=lambda x: x and ('bullet' in x or 'insight' in x or 'criteria' in x))
                for b_el in bullets:
                    txt = b_el.text.strip()
                    if any(w in txt.lower() for w in ['remote', 'on-site', 'hybrid', 'workplace']):
                        print("  Workplace insight:", txt)
                desc = detail_soup.find(class_=lambda x: x and 'description' in x)
                if desc:
                    desc_text = desc.text.strip()[:300]
                    print("  Desc excerpt:", desc_text)
                break
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
