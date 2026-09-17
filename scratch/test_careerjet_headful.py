import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT
from bs4 import BeautifulSoup

async def test():
    user_dir = os.path.abspath("./careerjet_session_test")
    os.makedirs(user_dir, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        url = 'https://www.careerjet.co.in/jobs?s=Sales&l=Bangalore'
        print('Navigating to', url, 'headless=False...')
        await page.goto(url, timeout=30000)
        await asyncio.sleep(5)
        title = await page.title()
        print('Title:', title)
        content = await page.content()
        s = BeautifulSoup(content, 'html.parser')
        cards = s.select("article.job, .job-list article, article, .job")
        print('Cards found:', len(cards))
        for c in cards[:3]:
            h2 = c.select_one("h2 a, a.title, h2")
            if h2:
                print('Job title:', h2.text.strip())
        await context.close()

if __name__ == "__main__":
    asyncio.run(test())
